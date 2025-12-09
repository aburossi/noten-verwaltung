import streamlit as st
import pandas as pd
import json
import io  # <--- Added for in-memory file handling
from datetime import datetime
from utils.data_manager import save_all_data, log_audit_event
from utils.grading import calculate_grade

def render():
    st.title("📁 Daten & Verwaltung")
    
    # Reordered tabs: Import is now first (default)
    tab_import, tab_manage, tab_export = st.tabs(["📥 Import", "👤 Schüler verwalten", "📤 Export"])
    
    # ==========================================
    # TAB 1: IMPORT (Now Default)
    # ==========================================
    with tab_import:
        # Import Students
        st.subheader("Schüler/innen importieren")
        with st.expander("ℹ️ Hilfe zum Schüler-Import"):
            st.write("Laden Sie eine Excel- oder CSV-Datei hoch mit den Spalten: `Anmeldename`, `Vorname`, `Nachname`.")

        uploaded_file = st.file_uploader("Excel/CSV Datei (Anmeldename, Vorname, Nachname)", type=['xlsx', 'csv'], key="student_upload")
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                st.dataframe(df.head())
                
                if st.button("✅ Import starten"):
                    count = 0
                    for _, row in df.iterrows():
                        # Basic validation
                        if 'Anmeldename' not in row or pd.isna(row['Anmeldename']): continue
                        
                        student = {
                            'id': f"student_{row['Anmeldename']}",
                            'Anmeldename': str(row['Anmeldename']).strip(),
                            'Vorname': str(row['Vorname']).strip(),
                            'Nachname': str(row['Nachname']).strip()
                        }
                        # Prevent duplicates
                        if not any(s['Anmeldename'] == student['Anmeldename'] for s in st.session_state.students):
                            st.session_state.students.append(student)
                            count += 1
                            
                    if count > 0:
                        log_audit_event("Import", f"{count} Schüler/innen importiert")
                        save_all_data()
                        st.success(f"✅ {count} importiert")
                        st.rerun()
                    else:
                        st.warning("Keine neuen Schüler/innen gefunden (Duplikate?).")
            except Exception as e: st.error(f"Fehler: {e}")

        # Import Grades
        st.write("---")
        st.header("Noten importieren")

        # --- NEW TEMPLATE GENERATOR SECTION ---
        st.subheader("1. Vorlage erstellen (Optional)")
        st.caption("Laden Sie hier eine Excel-Tabelle mit allen aktuellen Schüler/innen herunter, um die Noten offline einzutragen.")
        
        if not st.session_state.students:
            st.warning("⚠️ Bitte importieren Sie zuerst Schüler/innen, um eine Vorlage zu erstellen.")
        else:
            # 1. Create Dataframe from current students
            template_data = []
            for s in st.session_state.students:
                template_data.append({
                    "Anmeldename": s['Anmeldename'],
                    "Vorname": s['Vorname'],
                    "Nachname": s['Nachname'],
                    "Punkte": "",  # Empty for teacher input
                    "Max.": 100    # Default value
                })
            
            df_template = pd.DataFrame(template_data)
            
            # 2. Convert to Excel in memory
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_template.to_excel(writer, index=False, sheet_name='Notenimport')
                
                # Auto-adjust column width (UX improvement)
                workbook = writer.book
                worksheet = writer.sheets['Notenimport']
                format_header = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3'})
                
                for col_num, value in enumerate(df_template.columns.values):
                    worksheet.write(0, col_num, value, format_header)
                    worksheet.set_column(col_num, col_num, 20) # Set width to 20
            
            # 3. Download Button
            file_name = f"Notenliste_Vorlage_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
            st.download_button(
                label="📥 Leere Notenliste herunterladen (.xlsx)",
                data=buffer.getvalue(),
                file_name=file_name,
                mime="application/vnd.ms-excel"
            )

        # --- EXISTING UPLOAD SECTION ---
        st.subheader("2. Ausgefüllte Datei hochladen")
        grades_file = st.file_uploader("Noten Datei (Anmeldename, Punkte, Max)", type=['xlsx', 'csv'], key="grades_upload")
        
        if grades_file:
            try:
                df = pd.read_csv(grades_file) if grades_file.name.endswith('.csv') else pd.read_excel(grades_file)
                st.dataframe(df.head())
                
                with st.form("import_grades_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        assignment_name = st.text_input("Prüfungsname*")
                        subject = st.selectbox("Fach*", st.session_state.config['subjects'])
                    with col2:
                        assignment_type = st.selectbox("Typ*", options=list(st.session_state.config['weightDefaults'].keys()))
                        scale_type = st.selectbox("Skala", options=list(st.session_state.config['scales'].keys()))
                    
                    weight = st.number_input("Gewicht", value=1.0, step=0.1)
                    
                    if st.form_submit_button("📥 Importieren"):
                        if not assignment_name:
                            st.error("Name fehlt")
                        else:
                            # Robustly get Max Points (check if column exists, else default)
                            if 'Max.' in df.columns and pd.notna(df['Max.'].iloc[0]):
                                max_points = df['Max.'].iloc[0]
                            else:
                                max_points = 100
                                st.warning("Spalte 'Max.' nicht gefunden oder leer. Setze Standardwert auf 100.")

                            new_assignment = {
                                'id': f"assignment_{datetime.now().timestamp()}",
                                'name': assignment_name, 'subject': subject, 'type': assignment_type,
                                'weight': weight, 'maxPoints': float(max_points), 'scaleType': scale_type,
                                'date': datetime.now().isoformat(), 'grades': {}
                            }
                            
                            count = 0
                            for _, row in df.iterrows():
                                anmeldename = str(row['Anmeldename']).strip()
                                points = row.get('Punkte', 0) # Look for 'Punkte' column
                                student = next((s for s in st.session_state.students if s['Anmeldename'] == anmeldename), None)
                                
                                if student and pd.notna(points):
                                    # Allow 0 points, but skip if empty/NaN
                                    try:
                                        p_val = float(points)
                                        grade_info = calculate_grade(p_val, float(max_points), scale_type)
                                        if grade_info: 
                                            new_assignment['grades'][student['id']] = grade_info['note']
                                            count += 1
                                    except ValueError:
                                        continue
                            
                            st.session_state.assignments.append(new_assignment)
                            log_audit_event("Noten-Import", f"Prüfung: {assignment_name}, {count} Noten")
                            save_all_data()
                            st.success(f"Erfolgreich importiert ({count} Noten)!")
                            st.rerun()
            except Exception as e: st.error(f"Fehler: {e}")

    # ==========================================
    # TAB 2: MANAGE STUDENTS
    # ==========================================
    with tab_manage:
        st.subheader("Schüler/in aus aktueller Klasse entfernen")
        
        if not st.session_state.students:
            st.info("Keine Schüler/innen in dieser Klasse.")
        else:
            # Dropdown to select student
            student_to_delete = st.selectbox(
                "Schüler/in auswählen",
                options=st.session_state.students,
                format_func=lambda s: f"{s['Vorname']} {s['Nachname']} ({s['Anmeldename']})"
            )
            
            st.warning(f"⚠️ Warnung: Dies löscht {student_to_delete['Vorname']} {student_to_delete['Nachname']} und alle zugehörigen Noten aus dieser Klasse.")
            
            if st.button("🗑️ Schüler/in endgültig löschen", type="primary"):
                # 1. Remove from students list
                st.session_state.students.remove(student_to_delete)
                
                # 2. Cleanup: Remove grades for this student from all assignments
                cleaned_grades_count = 0
                for assignment in st.session_state.assignments:
                    if student_to_delete['id'] in assignment['grades']:
                        del assignment['grades'][student_to_delete['id']]
                        cleaned_grades_count += 1
                
                # 3. Log and Save
                log_audit_event("Schüler gelöscht", f"Name: {student_to_delete['Vorname']} {student_to_delete['Nachname']}, Noten bereinigt: {cleaned_grades_count}")
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