import streamlit as st
import pandas as pd
import io 
from datetime import datetime
from utils.data_manager import save_all_data, log_audit_event
from utils.grading import calculate_grade

def render():
    st.title("📁 Daten & Verwaltung")
    
    # Tabs für bessere Struktur
    tab_import, tab_manage, tab_export = st.tabs(["📥 Import", "👤 Schüler verwalten", "📤 Export"])
    
    # ==========================================
    # TAB 1: IMPORT
    # ==========================================
    with tab_import:
        
        # ------------------------------------------
        # 1. NOTEN IMPORT (WICHTIGSTE FUNKTION OBEN)
        # ------------------------------------------
        st.header("📊 Noten importieren")
        
        # A) Vorlage (Optional) in einem Expander verstecken, um Platz zu sparen
        with st.expander("📄 Excel-Vorlage erstellen (Optional)", expanded=False):
            st.caption("Laden Sie hier eine Liste Ihrer Schüler herunter, um die Punkte offline einzutragen.")
            
            if not st.session_state.students:
                st.warning("⚠️ Keine Schüler vorhanden. Bitte importieren Sie zuerst eine Klasse (unten).")
            else:
                # Create Dataframe
                template_data = []
                for s in st.session_state.students:
                    template_data.append({
                        "Anmeldename": s['Anmeldename'],
                        "Vorname": s['Vorname'],
                        "Nachname": s['Nachname'],
                        "Punkte": "",  
                        "Max.": 100    
                    })
                df_template = pd.DataFrame(template_data)
                
                # Excel Buffer
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_template.to_excel(writer, index=False, sheet_name='Notenimport')
                    workbook = writer.book
                    worksheet = writer.sheets['Notenimport']
                    format_header = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3'})
                    for col_num, value in enumerate(df_template.columns.values):
                        worksheet.write(0, col_num, value, format_header)
                        worksheet.set_column(col_num, col_num, 20)
                
                st.download_button(
                    label="📥 Leere Notenliste herunterladen (.xlsx)",
                    data=buffer.getvalue(),
                    file_name=f"Notenliste_Vorlage_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
                    mime="application/vnd.ms-excel"
                )

        # B) Der eigentliche Import-Prozess
        st.write("###### Datei hochladen")
        
        # Modus Auswahl
        import_mode = st.radio(
            "Modus wählen", 
            ["🆕 Neue Prüfung erstellen", "🔄 Bestehende Prüfung aktualisieren/ergänzen"], 
            horizontal=True,
            label_visibility="collapsed"
        )

        # File Uploader
        grades_file = st.file_uploader("Excel-Datei (Spalten: Anmeldename, Punkte)", type=['xlsx', 'csv'], key="grades_main_upload")
        
        if grades_file:
            try:
                df = pd.read_csv(grades_file) if grades_file.name.endswith('.csv') else pd.read_excel(grades_file)
                st.caption("Vorschau:")
                st.dataframe(df.head(3), height=100)
                
                # --- LOGIC BRANCHING ---
                
                # MODUS 1: NEUE PRÜFUNG
                if import_mode == "🆕 Neue Prüfung erstellen":
                    with st.form("import_new_grades_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            assignment_name = st.text_input("Prüfungsname*")
                            subject = st.selectbox("Fach*", st.session_state.config['subjects'])
                        with col2:
                            assignment_type = st.selectbox("Typ*", options=list(st.session_state.config['weightDefaults'].keys()))
                            scale_type = st.selectbox("Skala", options=list(st.session_state.config['scales'].keys()))
                        
                        weight = st.number_input("Gewicht", value=1.0, step=0.1)
                        
                        # Max Points from file or default
                        file_max = 100
                        if 'Max.' in df.columns and pd.notna(df['Max.'].iloc[0]):
                            file_max = df['Max.'].iloc[0]
                        max_points = st.number_input("Max. Punkte", value=float(file_max))
                        
                        # New: URL Input
                        assignment_url = st.text_input("LMS Link (Optional)")

                        if st.form_submit_button("📥 Als NEUE Prüfung importieren", type="primary"):
                            if not assignment_name:
                                st.error("Name fehlt")
                            else:
                                new_assignment = {
                                    'id': f"assignment_{datetime.now().timestamp()}",
                                    'name': assignment_name,
                                    'subject': subject,
                                    'type': assignment_type,
                                    'weight': weight,
                                    'maxPoints': float(max_points),
                                    'scaleType': scale_type,
                                    'url': assignment_url.strip(),
                                    'date': datetime.now().isoformat(),
                                    'grades': {}
                                }
                                
                                count = 0
                                for _, row in df.iterrows():
                                    anmeldename = str(row['Anmeldename']).strip()
                                    points = row.get('Punkte', 0)
                                    student = next((s for s in st.session_state.students if s['Anmeldename'] == anmeldename), None)
                                    
                                    if student and pd.notna(points):
                                        try:
                                            # Note berechnen
                                            grade_info = calculate_grade(float(points), float(max_points), scale_type)
                                            if grade_info: 
                                                new_assignment['grades'][student['id']] = grade_info['note']
                                                count += 1
                                        except: continue
                                
                                st.session_state.assignments.append(new_assignment)
                                log_audit_event("Noten-Import (Neu)", f"Prüfung: {assignment_name}, {count} Noten")
                                save_all_data()
                                st.success(f"Erfolgreich erstellt ({count} Noten)!")
                                st.rerun()

                # MODUS 2: UPDATE
                else: # "🔄 Bestehende Prüfung aktualisieren"
                    sel_subject = st.selectbox("Fach auswählen", st.session_state.config['subjects'], key="update_subj_sel")
                    existing_assigns = [a for a in st.session_state.assignments if a['subject'] == sel_subject]
                    
                    if not existing_assigns:
                        st.warning("Keine Prüfungen in diesem Fach gefunden.")
                    else:
                        selected_assign_name = st.selectbox("Welche Prüfung aktualisieren?", options=[a['name'] for a in existing_assigns])
                        target_assignment = next(a for a in existing_assigns if a['name'] == selected_assign_name)
                        
                        st.info(f"Fügt Noten zu '{target_assignment['name']}' hinzu oder aktualisiert diese.")
                        
                        if st.button("🔄 Update starten", type="primary"):
                            update_count = 0
                            new_entry_count = 0
                            max_p = target_assignment['maxPoints']
                            scale = target_assignment['scaleType']
                            
                            for _, row in df.iterrows():
                                anmeldename = str(row['Anmeldename']).strip()
                                points = row.get('Punkte', None)
                                student = next((s for s in st.session_state.students if s['Anmeldename'] == anmeldename), None)
                                
                                if student and pd.notna(points):
                                    try:
                                        grade_info = calculate_grade(float(points), float(max_p), scale)
                                        if grade_info:
                                            new_grade = grade_info['note']
                                            current_grade = target_assignment['grades'].get(student['id'])
                                            
                                            if current_grade and current_grade != new_grade:
                                                target_assignment['grades'][student['id']] = new_grade
                                                update_count += 1
                                            elif current_grade is None:
                                                target_assignment['grades'][student['id']] = new_grade
                                                new_entry_count += 1
                                    except ValueError: continue
                            
                            if update_count > 0 or new_entry_count > 0:
                                log_audit_event("Noten-Import (Update)", f"{target_assignment['name']}: {new_entry_count} neu, {update_count} geändert.")
                                save_all_data()
                                st.success(f"✅ Fertig! {new_entry_count} neue Noten, {update_count} Updates.")
                                st.rerun()
                            else:
                                st.warning("Keine Änderungen gefunden.")

            except Exception as e: st.error(f"Fehler: {e}")

        st.divider()

        # ------------------------------------------
        # 2. SCHÜLER IMPORT (NUR SEMESTERSTART)
        # ------------------------------------------
        # In Expander versteckt, da selten gebraucht
        with st.expander("🏫 Neue Klasse / Schüler importieren (Semesterstart)", expanded=False):
            st.info("Laden Sie eine Excel- oder CSV-Datei hoch mit den Spalten: `Anmeldename`, `Vorname`, `Nachname`.")
            
            uploaded_file = st.file_uploader("Schüler-Liste hochladen", type=['xlsx', 'csv'], key="student_upload")
            
            if uploaded_file:
                try:
                    df_s = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                    st.dataframe(df_s.head(3))
                    
                    if st.button("✅ Schüler importieren"):
                        count = 0
                        for _, row in df_s.iterrows():
                            if 'Anmeldename' not in row or pd.isna(row['Anmeldename']): continue
                            
                            student = {
                                'id': f"student_{row['Anmeldename']}",
                                'Anmeldename': str(row['Anmeldename']).strip(),
                                'Vorname': str(row['Vorname']).strip(),
                                'Nachname': str(row['Nachname']).strip()
                            }
                            # Duplikate vermeiden
                            if not any(s['Anmeldename'] == student['Anmeldename'] for s in st.session_state.students):
                                st.session_state.students.append(student)
                                count += 1
                                
                        if count > 0:
                            log_audit_event("Import", f"{count} Schüler/innen importiert")
                            save_all_data()
                            st.success(f"✅ {count} Schüler/innen importiert")
                            st.rerun()
                        else:
                            st.warning("Keine neuen Schüler gefunden (evtl. schon vorhanden?).")
                except Exception as e: st.error(f"Fehler: {e}")

    # ==========================================
    # TAB 2: MANAGE STUDENTS
    # ==========================================
    with tab_manage:
        st.subheader("Schüler/in aus aktueller Klasse entfernen")
        
        if not st.session_state.students:
            st.info("Keine Schüler/innen in dieser Klasse.")
        else:
            student_to_delete = st.selectbox(
                "Schüler/in auswählen",
                options=st.session_state.students,
                format_func=lambda s: f"{s['Vorname']} {s['Nachname']} ({s['Anmeldename']})"
            )
            
            st.warning(f"⚠️ Warnung: Dies löscht {student_to_delete['Vorname']} {student_to_delete['Nachname']} und alle zugehörigen Noten aus dieser Klasse.")
            
            if st.button("🗑️ Schüler/in endgültig löschen", type="primary"):
                st.session_state.students.remove(student_to_delete)
                
                cleaned_grades_count = 0
                for assignment in st.session_state.assignments:
                    if student_to_delete['id'] in assignment['grades']:
                        del assignment['grades'][student_to_delete['id']]
                        cleaned_grades_count += 1
                
                log_audit_event("Schüler gelöscht", f"Name: {student_to_delete['Vorname']} {student_to_delete['Nachname']}")
                save_all_data()
                
                st.success(f"✅ {student_to_delete['Vorname']} wurde entfernt.")
                st.rerun()

            st.divider()
            st.caption(f"Anzahl Schüler/innen in dieser Klasse: {len(st.session_state.students)}")

    # ==========================================
    # TAB 3: EXPORT
    # ==========================================
    with tab_export:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Schülerliste")
            if st.button("📥 Als CSV herunterladen"):
                df = pd.DataFrame(st.session_state.students)
                st.download_button("Download CSV", df.to_csv(index=False), "students.csv", "text/csv")
        
        with col2:
            st.subheader("System Backup")
            st.info("Für vollständige Backups, siehe '💾 Backup & Log' im Menü.")