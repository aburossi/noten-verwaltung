import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
from utils.email_manager import send_email, log_email_event, get_last_email_status, get_students_with_changes
from utils.grading import calculate_weighted_average
from utils.template_manager import get_templates, save_new_template, delete_template, render_template
from utils.data_manager import get_class_registry

def generate_email_log_print_html(class_name, email_log, subject_filter=None):
    """Generate printable HTML for email communication log"""
    
    # Filter if needed
    filtered_log = email_log
    if subject_filter and subject_filter != "Alle":
        filtered_log = [log for log in email_log if log['subject'] == subject_filter]
    
    # Build log rows
    log_rows = ""
    for log in filtered_log:
        timestamp = datetime.fromisoformat(log['timestamp']).strftime("%d.%m.%Y %H:%M")
        
        status_color = "#388e3c" if log['status'] == 'sent' else "#d32f2f"
        status_text = "✓ Gesendet" if log['status'] == 'sent' else "✗ Fehler"
        
        log_rows += f"""
        <tr>
            <td style="padding:8px; border-bottom:1px solid #ddd;">{timestamp}</td>
            <td style="padding:8px; border-bottom:1px solid #ddd;"><strong>{log['student_name']}</strong></td>
            <td style="padding:8px; border-bottom:1px solid #ddd;">{log['subject']}</td>
            <td style="padding:8px; border-bottom:1px solid #ddd; color:{status_color}; font-weight:bold;">{status_text}</td>
            <td style="padding:8px; border-bottom:1px solid #ddd; font-size:11px; color:#666;">{log.get('error', '-')}</td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Email-Protokoll - {class_name}</title>
        <style>
            @media print {{
                body {{ margin: 0; }}
                .no-print {{ display: none; }}
            }}
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            .header {{ margin-bottom: 20px; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            .footer {{ margin-top: 30px; padding-top: 10px; border-top: 1px solid #ccc; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Email-Kommunikationsprotokoll</h1>
            <p><strong>Klasse:</strong> {class_name} | <strong>Gedruckt am:</strong> {datetime.now().strftime("%d.%m.%Y, %H:%M Uhr")}</p>
            <p><strong>Anzahl Einträge:</strong> {len(filtered_log)}</p>
        </div>
        
        <table>
            <thead>
                <tr style="background-color: #f2f2f2;">
                    <th style="text-align:left; padding:8px; border-bottom:2px solid #333;">Zeitstempel</th>
                    <th style="text-align:left; padding:8px; border-bottom:2px solid #333;">Empfänger</th>
                    <th style="text-align:left; padding:8px; border-bottom:2px solid #333;">Fach</th>
                    <th style="text-align:left; padding:8px; border-bottom:2px solid #333;">Status</th>
                    <th style="text-align:left; padding:8px; border-bottom:2px solid #333;">Bemerkung</th>
                </tr>
            </thead>
            <tbody>
                {log_rows}
            </tbody>
        </table>
        
        <div class="footer">
            <p><strong>Legende:</strong> <span style="color:#388e3c;">✓</span> Erfolgreich gesendet | <span style="color:#d32f2f;">✗</span> Fehlgeschlagen</p>
        </div>
        
        <div class="no-print" style="margin-top: 20px; text-align: center;">
            <button onclick="window.print()" style="padding: 10px 20px; font-size: 16px; cursor: pointer;">🖨️ Drucken</button>
            <button onclick="window.close()" style="padding: 10px 20px; font-size: 16px; cursor: pointer; margin-left: 10px;">Schließen</button>
        </div>
    </body>
    </html>
    """
    return html

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
                # Calculate the display string first
                avg_display = f"{avg:.2f}" if avg else "-"
                # Use the pre-calculated string in the label
                label = f"{status_icon} {change_indicator}{student['Vorname']} {student['Nachname']} (Ø {avg_display})"                
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

    # --- TAB 2: TEMPLATES ---
    with tab_templates:
        st.subheader("📝 Email Vorlagen")
        
        templates = get_templates()
        
        # Display existing templates
        for t in templates:
            with st.expander(f"📄 {t['name']} ({t['category']})"):
                st.text_input("Betreff", t['subject_line'], disabled=True, key=f"subj_{t['name']}")
                st.text_area("Text", t['body'], height=200, disabled=True, key=f"body_{t['name']}")
                st.caption("**Verfügbare Platzhalter:** {firstname}, {lastname}, {subject}, {average}, {grades_list}, {date}, {sender_name}")
                
                if st.button("🗑️ Vorlage löschen", key=f"del_tmpl_{t['name']}"):
                    delete_template(t['name'])
                    st.rerun()
        
        # Add new template
        st.divider()
        st.subheader("➕ Neue Vorlage erstellen")
        
        with st.form("new_template_form"):
            new_name = st.text_input("Name der Vorlage*")
            new_category = st.selectbox("Kategorie", ["Bericht", "Intervention", "Lob", "Sonstiges"])
            new_subject_line = st.text_input("Betreff*")
            new_body = st.text_area("Email Text*", height=200, placeholder="Nutzen Sie Platzhalter wie {firstname}, {subject}, {average}, {grades_list}")
            
            if st.form_submit_button("💾 Vorlage speichern"):
                if new_name and new_subject_line and new_body:
                    save_new_template(new_name, new_category, new_subject_line, new_body)
                    st.success(f"Vorlage '{new_name}' gespeichert!")
                    st.rerun()
                else:
                    st.error("Bitte alle Pflichtfelder ausfüllen.")

    # --- TAB 3: LOG (ENHANCED WITH PRINT) ---
    with tab_log:
        st.subheader("📜 Email-Protokoll")
        
        # Get class name for print
        registry = get_class_registry()
        current_class = next((c for c in registry if c['id'] == st.session_state.get('current_class_id')), None)
        class_name = current_class['name'] if current_class else "Unbekannte Klasse"
        
        if 'email_log' not in st.session_state or not st.session_state.email_log:
            st.info("Keine Emails versendet.")
        else:
            # Filter and Print Controls
            col_filter, col_print = st.columns([3, 1])
            
            with col_filter:
                subject_filter = st.selectbox(
                    "Fach filtern",
                    ["Alle"] + st.session_state.config['subjects'],
                    key="email_log_filter"
                )
            
            with col_print:
                if st.button("🖨️ Drucken", use_container_width=True, help="Email-Protokoll drucken"):
                    print_html = generate_email_log_print_html(
                        class_name,
                        st.session_state.email_log,
                        subject_filter
                    )
                    components.html(
                        f"""
                        <script>
                            var printWindow = window.open('', '_blank');
                            printWindow.document.write(`{print_html.replace('`', '\\`')}`);
                            printWindow.document.close();
                        </script>
                        """,
                        height=0
                    )
            
            # Display log
            df = pd.DataFrame(st.session_state.email_log)
            
            # Filter
            if subject_filter != "Alle":
                df = df[df['subject'] == subject_filter]
            
            # Format timestamp
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%d.%m.%Y %H:%M')
                
                st.dataframe(
                    df[['timestamp', 'student_name', 'subject', 'status', 'error']],
                    column_config={
                        "timestamp": "Zeit",
                        "student_name": "Empfänger",
                        "subject": "Fach",
                        "status": "Status",
                        "error": "Fehler"
                    },
                    use_container_width=True,
                    hide_index=True
                )