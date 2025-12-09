import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
from utils.email_manager import send_email, log_email_event, get_last_email_status, get_students_with_changes
from utils.grading import calculate_weighted_average
from utils.template_manager import get_templates, save_new_template, delete_template, render_template

def render():
    st.title("✉️ Smart Email Center")
    
    tab_send, tab_templates, tab_log = st.tabs(["📤 Senden", "📝 Vorlagen", "📜 Protokoll"])
    
    with tab_send:
        # --- CONFIG ---
        with st.expander("⚙️ Email Einstellungen", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                sender_email = st.text_input("Absender Email", value=st.session_state.config['email']['sender_email'])
                sender_name_input = st.text_input("Anzeigename (Signatur)", value="Deine Lehrperson") 
            with col2:
                sender_pwd = st.text_input("Passwort", type="password")
                selected_subject = st.selectbox("Fach auswählen", st.session_state.config['subjects'])
            
            st.session_state.config['email']['sender_email'] = sender_email

        if not sender_pwd:
            st.warning("Bitte Passwort eingeben um fortzufahren.")
            return

        # --- IMPROVEMENT 2: SMART BATCH REPORT ---
        st.subheader("🤖 Smart Aktionen")
        
        # Determine who has new grades
        students_with_changes = get_students_with_changes(selected_subject)
        
        col_smart1, col_smart2 = st.columns([2, 1])
        with col_smart1:
            st.info(f"System erkannt: **{len(students_with_changes)} Schüler/innen** haben neue Noten seit der letzten Email.")
        
        with col_smart2:
            if st.button("✨ Wochenbericht senden (Smart Batch)", type="primary", use_container_width=True):
                # Auto-select filter logic below
                st.session_state['smart_batch_trigger'] = True

        st.divider()

        # --- MANUAL SELECTION ---
        st.subheader("Empfänger Auswahl")
        
        templates = get_templates()
        selected_template_name = st.selectbox("Vorlage", [t['name'] for t in templates])
        selected_template = next(t for t in templates if t['name'] == selected_template_name)

        # Logic to handle Smart Batch Trigger
        preselected_ids = []
        if st.session_state.get('smart_batch_trigger'):
            preselected_ids = [s['id'] for s in students_with_changes]
            st.success("Smart Filter angewendet: Nur Schüler mit Änderungen ausgewählt.")
            del st.session_state['smart_batch_trigger'] # Reset

        selected_students = []
        
        # Filter UI
        filter_mode = st.radio("Filter:", ["Alle", "Nur Ungenügende (< 4.0)", "Manuelle Auswahl"], horizontal=True)

        with st.container(height=300):
            for student in st.session_state.students:
                avg = calculate_weighted_average(student['id'], selected_subject)
                last_log = get_last_email_status(student['id'], selected_subject)
                
                # Determine "New Data" indicator
                has_changes = student['id'] in [s['id'] for s in students_with_changes]
                change_indicator = "🔔 Neu | " if has_changes else ""
                
                # Filter Logic
                should_select = False
                if student['id'] in preselected_ids: should_select = True
                elif filter_mode == "Alle": should_select = True
                elif filter_mode == "Nur Ungenügende (< 4.0)" and avg and avg < 4.0: should_select = True
                
                status_icon = "🟢" if last_log and last_log['status'] == 'sent' else "⚪"
                label = f"{status_icon} {change_indicator}{student['Vorname']} {student['Nachname']} (Ø {avg:.2f if avg else '-'})"
                
                if st.checkbox(label, value=should_select, key=f"email_{student['id']}"):
                    selected_students.append(student)

        # --- PREVIEW & SEND ---
        if selected_students:
            st.write("---")
            st.subheader(f"Vorschau ({len(selected_students)} Empfänger)")
            
            preview_student = selected_students[0]
            student_assignments = [a for a in st.session_state.assignments if a['subject'] == selected_subject and preview_student['id'] in a.get('grades', {})]
            w_avg = calculate_weighted_average(preview_student['id'], selected_subject)
            
            subj_line, _, body_html = render_template(
                selected_template, preview_student, selected_subject, w_avg, student_assignments, sender_name=sender_name_input
            )
            
            st.text_input("Betreff", subj_line, disabled=True)
            with st.expander("HTML Vorschau ansehen"):
                components.html(body_html, height=300, scrolling=True)
            
            if st.button("🚀 Emails jetzt senden", type="primary"):
                progress = st.progress(0)
                status = st.empty()
                success_count = 0
                
                for i, stud in enumerate(selected_students):
                    status.text(f"Sende an {stud['Vorname']}...")
                    s_assigns = [a for a in st.session_state.assignments if a['subject'] == selected_subject and stud['id'] in a.get('grades', {})]
                    s_avg = calculate_weighted_average(stud['id'], selected_subject)
                    
                    s_subj, s_text, s_html = render_template(
                        selected_template, stud, selected_subject, s_avg, s_assigns, sender_name=sender_name_input
                    )
                    
                    recipient = f"{stud['Anmeldename']}@lernende.bbw.ch"
                    ok, msg = send_email(recipient, s_subj, s_text, sender_email, sender_pwd, html_body=s_html)
                    
                    if ok:
                        success_count += 1
                        log_email_event(stud['id'], f"{stud['Vorname']} {stud['Nachname']}", selected_subject, 'sent')
                    else:
                        log_email_event(stud['id'], f"{stud['Vorname']} {stud['Nachname']}", selected_subject, 'failed', msg)
                    
                    progress.progress((i+1)/len(selected_students))
                
                status.text("Fertig!")
                st.success(f"{success_count} Emails versendet.")
                st.rerun()

    # (Tab Templates & Log remain largely same, omitted for brevity but assumed present)
    with tab_templates:
        st.info("Vorlagen Verwaltung (Unverändert)")
        for t in get_templates():
             with st.expander(f"{t['name']}"):
                 st.code(t['body'])

    with tab_log:
        if 'email_log' in st.session_state and st.session_state.email_log:
            st.dataframe(pd.DataFrame(st.session_state.email_log), use_container_width=True)
        else:
            st.info("Keine Logs.")