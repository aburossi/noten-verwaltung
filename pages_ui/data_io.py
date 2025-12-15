import streamlit as st
import pandas as pd
import io 
from datetime import datetime
import os
import json
from utils.data_manager import (
    save_all_data, log_audit_event, get_available_backups, 
    create_backup, restore_backup, create_zip_export, import_zip_backup,
    get_class_registry, load_json, save_json, CLASSES_DIR
)
from utils.grading import calculate_grade

def render():
    st.title("📁 Daten & System")
    
    # Tabs Setup
    tab_import, tab_manage, tab_export, tab_backup = st.tabs([
        "📥 Import", 
        "👤 Schüler verwalten", 
        "📤 Export",
        "💾 Backup & Log" 
    ])
    
    # ==========================================
    # TAB 1: IMPORT
    # ==========================================
    with tab_import:
        st.header("📊 Noten importieren")
        
        # --- NOTEN IMPORT LOGIK ---
        with st.expander("📄 Excel-Vorlage für Noten erstellen (Optional)", expanded=False):
            st.caption("Laden Sie hier eine Liste Ihrer Schüler herunter.")
            if not st.session_state.students:
                st.warning("Keine Schüler vorhanden.")
            else:
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
                
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_template.to_excel(writer, index=False, sheet_name='Notenimport')
                    writer.sheets['Notenimport'].set_column(0, 4, 20)
                
                st.download_button(
                    label="📥 Leere Notenliste herunterladen (.xlsx)",
                    data=buffer.getvalue(),
                    file_name=f"Notenliste_Vorlage_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
                    mime="application/vnd.ms-excel"
                )

        st.write("###### Noten hochladen")
        import_mode = st.radio(
            "Modus wählen", 
            ["🆕 Neue Prüfung erstellen", "🔄 Bestehende Prüfung aktualisieren"], 
            horizontal=True,
            label_visibility="collapsed"
        )

        grades_file = st.file_uploader("Excel-Datei (Spalten: Anmeldename, Punkte)", type=['xlsx', 'csv'], key="grades_main_upload")
        
        if grades_file:
            try:
                df = pd.read_csv(grades_file) if grades_file.name.endswith('.csv') else pd.read_excel(grades_file)
                st.dataframe(df.head(3), height=100)
                
                if import_mode == "🆕 Neue Prüfung erstellen":
                    with st.form("import_new_grades_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            assignment_name = st.text_input("Prüfungsname*")
                            subject = st.selectbox("Fach*", st.session_state.config['subjects'])
                        with col2:
                            assignment_type = st.selectbox("Typ*", options=list(st.session_state.config['weightDefaults'].keys()))
                            weight = st.number_input("Gewicht", value=1.0, step=0.1)
                            
                            file_max = 100
                            if 'Max.' in df.columns and pd.notna(df['Max.'].iloc[0]):
                                file_max = df['Max.'].iloc[0]
                            max_points = st.number_input("Max. Punkte", value=float(file_max))
                        
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
                                    'scaleType': '60% Scale',
                                    'url': assignment_url.strip(),
                                    'date': datetime.now().isoformat(),
                                    'grades': {},
                                    'comments': {} # Ensure comments dict is initialized
                                }
                                
                                count = 0
                                for _, row in df.iterrows():
                                    aname = str(row['Anmeldename']).strip()
                                    points = row.get('Punkte', 0)
                                    student = next((s for s in st.session_state.students if s['Anmeldename'] == aname), None)
                                    
                                    if student and pd.notna(points):
                                        try:
                                            g_info = calculate_grade(float(points), float(max_points))
                                            if g_info: 
                                                new_assignment['grades'][student['id']] = g_info['note']
                                                count += 1
                                        except: continue
                                
                                st.session_state.assignments.append(new_assignment)
                                log_audit_event("Noten-Import (Neu)", f"Prüfung: {assignment_name}, {count} Noten")
                                save_all_data()
                                st.success(f"Erfolgreich erstellt ({count} Noten)!")
                                st.rerun()

                else: # UPDATE MODE
                    sel_subject = st.selectbox("Fach auswählen", st.session_state.config['subjects'], key="update_subj_sel")
                    existing_assigns = [a for a in st.session_state.assignments if a['subject'] == sel_subject]
                    
                    if existing_assigns:
                        selected_assign_name = st.selectbox("Welche Prüfung?", [a['name'] for a in existing_assigns])
                        target_assignment = next(a for a in existing_assigns if a['name'] == selected_assign_name)
                        
                        if st.button("🔄 Update starten", type="primary"):
                            update_count = 0
                            for _, row in df.iterrows():
                                aname = str(row['Anmeldename']).strip()
                                points = row.get('Punkte', None)
                                student = next((s for s in st.session_state.students if s['Anmeldename'] == aname), None)
                                
                                if student and pd.notna(points):
                                    try:
                                        g_info = calculate_grade(float(points), float(target_assignment['maxPoints']))
                                        if g_info:
                                            target_assignment['grades'][student['id']] = g_info['note']
                                            update_count += 1
                                    except: continue
                            
                            log_audit_event("Noten-Import (Update)", f"{target_assignment['name']}: {update_count} Updates.")
                            save_all_data()
                            st.success(f"✅ {update_count} Updates.")
                            st.rerun()
                    else:
                        st.warning("Keine Prüfungen vorhanden.")

            except Exception as e: st.error(f"Fehler: {e}")

        st.divider()
        
        # --- STUDENT IMPORT ---
        with st.expander("🏫 Neue Klasse / Schüler importieren (Semesterstart)", expanded=True):
            st.info("Laden Sie eine Excel- oder CSV-Datei hoch.")
            uploaded_file = st.file_uploader("Schüler-Liste hochladen", type=['xlsx', 'csv'], key="student_upload")
            
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df_students = pd.read_csv(uploaded_file)
                    else:
                        df_students = pd.read_excel(uploaded_file)

                    df_students.columns = df_students.columns.str.strip()
                    required = ['Anmeldename', 'Vorname', 'Nachname']
                    missing = [col for col in required if col not in df_students.columns]

                    if missing:
                        st.error(f"❌ Datei ungültig. Fehlende Spalten: {', '.join(missing)}")
                    else:
                        st.write("---")
                        st.markdown("#### 🎯 Ziel-Klasse auswählen")
                        
                        registry = get_class_registry()
                        current_id = st.session_state.get('current_class_id')
                        
                        default_idx = 0
                        for i, c in enumerate(registry):
                            if c['id'] == current_id:
                                default_idx = i
                                break
                        
                        target_class = st.selectbox(
                            "In welche Klasse sollen die Schüler importiert werden?",
                            registry,
                            format_func=lambda x: x['name'],
                            index=default_idx
                        )

                        is_current_class = (target_class['id'] == current_id)
                        
                        if not is_current_class:
                            st.warning(f"⚠️ Achtung: Sie importieren in **{target_class['name']}**, nicht in die aktuell geöffnete Klasse.")

                        valid_rows = df_students.dropna(subset=['Anmeldename']).shape[0]
                        st.caption(f"Gefundene Einträge: {valid_rows}")

                        if st.button(f"🚀 Import in '{target_class['name']}' bestätigen", type="primary"):
                            
                            count_new = 0
                            count_skipped = 0
                            
                            target_students = []
                            if is_current_class:
                                target_students = st.session_state.students
                            else:
                                path = os.path.join(CLASSES_DIR, target_class['id'], "students.json")
                                target_students = load_json(path, [])

                            for _, row in df_students.iterrows():
                                aname = str(row['Anmeldename']).strip()
                                vname = str(row['Vorname']).strip()
                                nname = str(row['Nachname']).strip()

                                if not aname or aname.lower() == 'nan':
                                    continue

                                if any(s['Anmeldename'] == aname for s in target_students):
                                    count_skipped += 1
                                    continue
                                
                                new_student = {
                                    "id": f"student_{aname}",
                                    "Anmeldename": aname,
                                    "Vorname": vname,
                                    "Nachname": nname
                                }
                                target_students.append(new_student)
                                count_new += 1
                            
                            if count_new > 0:
                                if is_current_class:
                                    save_all_data()
                                    st.success(f"✅ {count_new} Schüler in aktuelle Klasse importiert!")
                                    st.rerun()
                                else:
                                    path = os.path.join(CLASSES_DIR, target_class['id'], "students.json")
                                    save_json(path, target_students)
                                    log_audit_event("Schüler-Import (Extern)", f"{count_new} hinzugefügt", class_id=target_class['id'])
                                    st.success(f"✅ {count_new} Schüler in Klasse '{target_class['name']}' gespeichert!")
                            else:
                                st.warning("⚠️ Keine neuen Schüler hinzugefügt (alle existierten bereits).")

                except Exception as e:
                    st.error(f"Fehler beim Lesen der Datei: {e}")

    # ==========================================
    # TAB 2: MANAGE STUDENTS
    # ==========================================
    with tab_manage:
        st.subheader("Schüler/in entfernen")
        if st.session_state.students:
            student_to_delete = st.selectbox(
                "Schüler/in auswählen",
                options=st.session_state.students,
                format_func=lambda s: f"{s['Vorname']} {s['Nachname']} ({s['Anmeldename']})"
            )
            if st.button("🗑️ Löschen", type="primary"):
                st.session_state.students.remove(student_to_delete)
                # Cleanup grades and comments
                for a in st.session_state.assignments:
                    if student_to_delete['id'] in a['grades']:
                        del a['grades'][student_to_delete['id']]
                    if 'comments' in a and student_to_delete['id'] in a['comments']:
                        del a['comments'][student_to_delete['id']]
                        
                save_all_data()
                st.success("Gelöscht!")
                st.rerun()
        else:
            st.info("Keine Schüler in dieser Klasse.")

    # ==========================================
    # TAB 3: EXPORT
    # ==========================================
    with tab_export:
        st.subheader("Schülerliste")
        if st.button("📥 Als CSV herunterladen"):
            df = pd.DataFrame(st.session_state.students)
            st.download_button("Download CSV", df.to_csv(index=False), "students.csv", "text/csv")

    # ==========================================
    # TAB 4: BACKUP & LOG
    # ==========================================
    with tab_backup:
        st.subheader("📦 Backup Management")
        
        c1, c2 = st.columns(2)
        with c1:
            note = st.text_input("Notiz für Backup")
            if st.button("Backup erstellen"):
                success, msg = create_backup(auto=False, note=note)
                if success: st.success(msg)
                else: st.error(msg)
                st.rerun()
        
        with c2:
            st.info("Export/Import (.zip)")
            if st.button("📥 Alles herunterladen (.zip)"):
                zip_path = create_zip_export()
                with open(zip_path, "rb") as f:
                    st.download_button("ZIP speichern", f, file_name=f"bbw_full_{datetime.now().strftime('%Y%m%d')}.zip", mime="application/zip")
            
            up_zip = st.file_uploader("Backup wiederherstellen (.zip)", type="zip")
            if up_zip and st.button("🚨 System überschreiben"):
                success, msg = import_zip_backup(up_zip)
                if success: 
                    st.success(msg)
                    st.session_state.clear()
                    st.rerun()
                else: st.error(msg)

        st.divider()
        st.subheader("Verfügbare Snapshots (Wiederherstellen)")
        backups = get_available_backups()
        for b in backups:
            with st.expander(f"{b['date'].strftime('%d.%m.%Y %H:%M')} ({b['type']})"):
                if st.button("♻️ Wiederherstellen", key=b['name']):
                    success, msg = restore_backup(b['name'])
                    if success: 
                        st.session_state.clear()
                        st.rerun()
                    else: st.error(msg)

        st.divider()
        st.subheader("📝 Audit Log")
        if 'audit_log' in st.session_state and st.session_state.audit_log:
             st.dataframe(pd.DataFrame(st.session_state.audit_log), use_container_width=True)