import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
from utils.email_manager import send_email, log_email_event, get_last_email_status
from utils.grading import calculate_weighted_average
from utils.template_manager import get_templates, save_new_template, delete_template, render_template

def render():
    st.title("✉️ Smart Email Center")
    
    tab_send, tab_templates, tab_log = st.tabs(["📤 Senden", "📝 Vorlagen", "📜 Protokoll"])
    
    # ==========================================
    # TAB 1: SEND EMAILS
    # ==========================================
    with tab_send:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Konfiguration")
            sender_email = st.text_input("Email-Adresse (Absender)", value=st.session_state.config['email']['sender_email'])
            # NEW: Input for the Name used in {sender_name}
            sender_name_input = st.text_input("Name (Unterschrift)", value="Deine Lehrperson") 
            sender_pwd = st.text_input("Passwort", type="password")
            
            selected_subject = st.selectbox("Fach", st.session_state.config['subjects'])
            st.session_state.config['email']['sender_email'] = sender_email
            
        with col2:
            st.subheader("Vorlage wählen")
            templates = get_templates()
            template_names = [t['name'] for t in templates]
            if template_names:
                selected_template_name = st.selectbox("Vorlage", template_names)
                selected_template = next(t for t in templates if t['name'] == selected_template_name)
                st.info(f"Kategorie: {selected_template['category']}")
            else:
                st.warning("Keine Vorlagen gefunden. Bitte erstellen Sie zuerst eine.")
                return

        if not sender_pwd:
            st.warning("Bitte Passwort eingeben.")
            return

        # 2. Student Selection
        st.write("---")
        st.subheader("Empfänger")
        selected_students = []
        col_sel1, col_sel2 = st.columns([1, 4])
        with col_sel1:
            select_all = st.checkbox("Alle auswählen")
        
        filter_mode = st.radio("Filter:", ["Alle", "Nur Ungenügende (< 4.0)", "Noch nie gesendet"], horizontal=True)

        for student in st.session_state.students:
            avg = calculate_weighted_average(student['id'], selected_subject)
            last_log = get_last_email_status(student['id'], selected_subject)
            
            # Apply Filters
            if filter_mode == "Nur Ungenügende (< 4.0)" and (not avg or avg >= 4.0): continue
            if filter_mode == "Noch nie gesendet" and last_log and last_log['status'] == 'sent': continue

            status_icon = "🟢" if last_log and last_log['status'] == 'sent' else "⚪"
            avg_str = f"{avg:.2f}" if avg else "-"
            label = f"{status_icon} {student['Vorname']} {student['Nachname']} (Ø {avg_str})"
            
            if select_all or st.checkbox(label, key=f"email_{student['id']}"):
                selected_students.append(student)

        # 3. Preview & Send
        if selected_students:
            st.write("---")
            st.subheader(f"Vorschau ({len(selected_students)} Empfänger)")
            
            preview_student = selected_students[0]
            
            # Get assignments
            student_assignments = [a for a in st.session_state.assignments if a['subject'] == selected_subject and preview_student['id'] in a.get('grades', {})]
            w_avg = calculate_weighted_average(preview_student['id'], selected_subject)
            
            # PASS SENDER NAME HERE
            subj_line, body_text, body_html = render_template(
                selected_template, 
                preview_student, 
                selected_subject, 
                w_avg, 
                student_assignments, 
                sender_name=sender_name_input
            )
            
            st.text_input("Betreff", subj_line, disabled=True)
            
            preview_mode = st.radio("Vorschau Modus", ["HTML (Wie Email)", "Text (Raw)"], horizontal=True)
            
            if preview_mode == "HTML (Wie Email)":
                components.html(body_html, height=400, scrolling=True)
            else:
                st.text_area("Inhalt", body_text, height=250, disabled=True)
            
            if st.button("🚀 Massenversand starten", type="primary"):
                progress = st.progress(0)
                status = st.empty()
                success_count = 0
                
                for i, stud in enumerate(selected_students):
                    status.text(f"Sende an {stud['Vorname']}...")
                    
                    s_assigns = [a for a in st.session_state.assignments if a['subject'] == selected_subject and stud['id'] in a.get('grades', {})]
                    s_avg = calculate_weighted_average(stud['id'], selected_subject)
                    
                    # PASS SENDER NAME HERE TOO
                    s_subj, s_text, s_html = render_template(
                        selected_template, 
                        stud, 
                        selected_subject, 
                        s_avg, 
                        s_assigns, 
                        sender_name=sender_name_input
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

    # ==========================================
    # TAB 2: MANAGE TEMPLATES
    # ==========================================
    with tab_templates:
        st.subheader("Neue Vorlage erstellen")
        with st.form("new_template"):
            t_name = st.text_input("Vorlagen-Name (z.B. 'Warnung')")
            t_cat = st.selectbox("Kategorie", ["Bericht", "Intervention", "Lob", "Info"])
            t_subj = st.text_input("Betreffzeile", value="Notenstand {subject}")
            st.caption("Verwenden Sie `{grades_list}` für die Tabelle und `{sender_name}` für Ihre Unterschrift.")
            t_body = st.text_area("Nachricht", height=200, value="Hallo {firstname},\n\nanbei deine Notenübersicht.\n\n{grades_list}\n\nLieber Gruss,\n{sender_name}")
            
            if st.form_submit_button("💾 Vorlage speichern"):
                save_new_template(t_name, t_cat, t_subj, t_body)
                st.success("Gespeichert!")
                st.rerun()
        
        st.write("---")
        st.subheader("Vorhandene Vorlagen")
        for t in get_templates():
            with st.expander(f"{t['name']} ({t['category']})"):
                st.write(f"**Betreff:** {t['subject_line']}")
                st.code(t['body'])
                if st.button("Löschen", key=f"del_{t['name']}"):
                    delete_template(t['name'])
                    st.rerun()

    # ==========================================
    # TAB 3: LOG
    # ==========================================
    with tab_log:
        if 'email_log' in st.session_state and st.session_state.email_log:
            df_log = pd.DataFrame(st.session_state.email_log)
            st.dataframe(df_log, use_container_width=True)
        else:
            st.info("Noch keine Emails versendet.")