import streamlit as st
import pandas as pd
import io
from datetime import datetime
from utils.data_manager import save_all_data, log_audit_event
from utils.grading import calculate_weighted_average, get_student_trend, calculate_grade

def render(subject):
    st.title(f"📝 {subject}")
    
    subject_assignments = [a for a in st.session_state.assignments if a['subject'] == subject]
    subject_assignments.sort(key=lambda x: x['date'], reverse=True)

    # ==========================================
    # 1. ADD ASSIGNMENT (WITH TABS FOR MANUAL / IMPORT)
    # ==========================================
    with st.expander("➕ Neue Prüfung hinzufügen", expanded=False):
        
        # Tabs for Create vs Import
        tab_create, tab_import = st.tabs(["✍️ Manuell erstellen", "📥 Aus Excel importieren"])

        # --- TAB A: MANUAL (Existing Logic) ---
        with tab_create:
            # Actions: Copy / Template
            col_actions = st.columns([1, 1, 2])
            with col_actions[0]:
                if subject_assignments:
                    last_assign = subject_assignments[0]
                    if st.button(f"📋 Kopiere '{last_assign['name']}'"):
                        st.session_state['new_assign_name'] = f"{last_assign['name']} (Kopie)"
                        st.session_state['new_assign_type'] = last_assign['type']
                        st.session_state['new_assign_weight'] = last_assign['weight']
                        st.session_state['new_assign_max'] = last_assign['maxPoints']
                        st.rerun()

            with col_actions[1]:
                templates = {
                    "Standard Test": {"w": 2.0, "m": 100, "t": "Test"},
                    "Kleiner Test": {"w": 1.0, "m": 50, "t": "Test"},
                    "Vortrag": {"w": 1.0, "m": 20, "t": "Lernpfad"}
                }
                sel_tmpl = st.selectbox("Vorlage laden:", ["-"] + list(templates.keys()), label_visibility="collapsed")
                if sel_tmpl != "-":
                    t = templates[sel_tmpl]
                    st.session_state['new_assign_type'] = t['t']
                    st.session_state['new_assign_weight'] = t['w']
                    st.session_state['new_assign_max'] = t['m']

            with st.form(f"add_assignment_{subject}"):
                col1, col2 = st.columns(2)
                
                default_name = st.session_state.get('new_assign_name', '')
                type_opts = list(st.session_state.config['weightDefaults'].keys())
                default_type_idx = 0
                if 'new_assign_type' in st.session_state and st.session_state['new_assign_type'] in type_opts:
                    default_type_idx = type_opts.index(st.session_state['new_assign_type'])
                
                with col1:
                    assignment_name = st.text_input("Prüfungsname*", value=default_name)
                    assignment_type = st.selectbox("Typ*", options=type_opts, index=default_type_idx)
                
                with col2:
                    d_max = st.session_state.get('new_assign_max', 100)
                    max_points = st.number_input("Max. Punkte*", min_value=1, value=int(d_max))
                    d_weight = st.session_state.get('new_assign_weight', st.session_state.config['weightDefaults'].get(assignment_type, 1.0))
                    weight = st.number_input("Gewicht", min_value=0.1, value=float(d_weight), step=0.1)
                
                assignment_url = st.text_input("LMS Link (Optional)")
                scale_type = st.selectbox("Bewertungsskala", options=list(st.session_state.config['scales'].keys()))
                
                if st.form_submit_button("Prüfung erstellen"):
                    if assignment_name:
                        new_assignment = {
                            'id': f"assignment_{datetime.now().timestamp()}",
                            'name': assignment_name,
                            'subject': subject,
                            'type': assignment_type,
                            'weight': weight,
                            'maxPoints': max_points,
                            'scaleType': scale_type,
                            'url': assignment_url.strip(),
                            'date': datetime.now().isoformat(),
                            'grades': {}
                        }
                        st.session_state.assignments.append(new_assignment)
                        # Clear temp
                        for k in ['new_assign_name', 'new_assign_type', 'new_assign_weight', 'new_assign_max']: 
                            if k in st.session_state: del st.session_state[k]

                        log_audit_event("Prüfung erstellt", f"Name: {assignment_name}")
                        save_all_data()
                        st.success(f"✅ Prüfung '{assignment_name}' erstellt")
                        st.rerun()
                    else:
                        st.error("Bitte geben Sie einen Namen ein")

        # --- TAB B: IMPORT (New) ---
        with tab_import:
            st.info(f"Importieren Sie eine Notenliste direkt in das Fach **{subject}**.")
            
            # Download Template Helper
            template_data = []
            for s in st.session_state.students:
                template_data.append({"Anmeldename": s['Anmeldename'], "Vorname": s['Vorname'], "Nachname": s['Nachname'], "Punkte": ""})
            df_template = pd.DataFrame(template_data)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_template.to_excel(writer, index=False)
            
            st.download_button(
                "📥 Vorlage herunterladen", 
                data=buffer.getvalue(), 
                file_name=f"Vorlage_{subject}.xlsx",
                mime="application/vnd.ms-excel",
                help="Excel-Datei mit Schülerliste"
            )
            
            # Form for Import
            with st.form(f"import_assignment_{subject}"):
                up_file = st.file_uploader("Excel Datei (Spalten: Anmeldename, Punkte)", type=['xlsx', 'csv'])
                
                c1, c2 = st.columns(2)
                with c1:
                    imp_name = st.text_input("Prüfungsname (Import)*")
                    imp_type = st.selectbox("Typ", options=list(st.session_state.config['weightDefaults'].keys()), key="imp_type")
                with c2:
                    imp_max = st.number_input("Max. Punkte", value=100.0, key="imp_max")
                    imp_weight = st.number_input("Gewicht", value=1.0, step=0.1, key="imp_w")
                
                imp_url = st.text_input("LMS Link (Optional)", key="imp_url")

                if st.form_submit_button("🚀 Datei importieren & Prüfung erstellen"):
                    if not up_file or not imp_name:
                        st.error("Bitte Datei hochladen und Namen angeben.")
                    else:
                        try:
                            df_imp = pd.read_csv(up_file) if up_file.name.endswith('.csv') else pd.read_excel(up_file)
                            
                            new_assign = {
                                'id': f"assignment_{datetime.now().timestamp()}",
                                'name': imp_name,
                                'subject': subject, # Auto-set to current subject
                                'type': imp_type,
                                'weight': imp_weight,
                                'maxPoints': imp_max,
                                'scaleType': '60% Scale',
                                'url': imp_url.strip(),
                                'date': datetime.now().isoformat(),
                                'grades': {}
                            }
                            
                            count = 0
                            for _, row in df_imp.iterrows():
                                aname = str(row['Anmeldename']).strip()
                                points = row.get('Punkte', 0)
                                student = next((s for s in st.session_state.students if s['Anmeldename'] == aname), None)
                                
                                if student and pd.notna(points):
                                    try:
                                        g_info = calculate_grade(float(points), float(imp_max))
                                        if g_info: 
                                            new_assign['grades'][student['id']] = g_info['note']
                                            count += 1
                                    except: continue
                            
                            st.session_state.assignments.append(new_assign)
                            log_audit_event("Import via Fach", f"{imp_name}: {count} Noten")
                            save_all_data()
                            st.success(f"✅ Import erfolgreich! {count} Noten übernommen.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Import Fehler: {e}")

    # ==========================================
    # 2. LIST ASSIGNMENTS (Existing Logic)
    # ==========================================
    if not subject_assignments:
        st.info("Noch keine Prüfungen vorhanden.")
        return
    
    for assignment in subject_assignments:
        grades_vals = [float(g) for g in assignment['grades'].values() if g]
        avg_display = f" (Ø {sum(grades_vals) / len(grades_vals):.2f})" if grades_vals else ""
        link_icon = "🔗 " if assignment.get('url') else ""
        
        with st.expander(f"📋 {link_icon}{assignment['name']} {avg_display}"):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.caption(f"Max: {assignment['maxPoints']} Pkt | Typ: {assignment['type']}")
                current_dt = datetime.fromisoformat(assignment['date'])
                new_date = st.date_input("Datum", value=current_dt.date(), key=f"date_{assignment['id']}", format="DD.MM.YYYY")
                if new_date != current_dt.date():
                    assignment['date'] = datetime.combine(new_date, datetime.min.time()).isoformat()
                    save_all_data()
                    st.rerun()

            with col2:
                new_weight = st.number_input("Gewichtung", min_value=0.1, value=float(assignment['weight']), step=0.1, key=f"weight_{assignment['id']}")
                if new_weight != assignment['weight']:
                    assignment['weight'] = new_weight
                    save_all_data()

            with col3:
                st.write("") 
                if st.button("🗑️", key=f"del_{assignment['id']}", help="Löschen"):
                    st.session_state.assignments.remove(assignment)
                    save_all_data()
                    st.rerun()

            st.divider()
            
            # --- NOTENEINGABE ---
            if grades_vals:
                curr_avg = sum(grades_vals) / len(grades_vals)
                below_4 = len([g for g in grades_vals if g < 4.0])
                stat_col1, stat_col2 = st.columns(2)
                stat_col1.metric("Ø Live", f"{curr_avg:.2f}")
                stat_col2.metric("Unter 4.0", f"{below_4}", delta_color="inverse")
            
            with st.form(f"grades_form_{assignment['id']}"):
                input_data = {}
                for idx, student in enumerate(st.session_state.students):
                    if idx % 2 == 0: cols = st.columns([1, 1])
                    with cols[idx % 2]:
                        current_grade = assignment['grades'].get(student['id'])
                        val = float(current_grade) if current_grade else 0.0
                        trend_icon, _ = get_student_trend(student['id'], subject)
                        lbl = f"{student['Vorname']} {student['Nachname']} {trend_icon if trend_icon else ''}"
                        new_grade_input = st.number_input(lbl, min_value=0.0, max_value=6.0, value=val, step=0.5, format="%.1f", key=f"g_{assignment['id']}_{student['id']}")
                        if new_grade_input is not None: input_data[student['id']] = round(new_grade_input, 1)

                st.write("")
                if st.form_submit_button("💾 Noten speichern", type="primary", use_container_width=True):
                    changes_log = []
                    for student_id, new_grade in input_data.items():
                        old_grade = assignment['grades'].get(student_id)
                        old_grade_float = float(old_grade) if old_grade is not None else None
                        if new_grade == 0.0 and old_grade_float is not None:
                            del assignment['grades'][student_id]
                            changes_log.append("Deleted")
                        elif new_grade > 0.0 and new_grade != old_grade_float:
                            assignment['grades'][student_id] = new_grade
                            changes_log.append("Changed")
                    if changes_log:
                        save_all_data()
                        st.success(f"✅ {len(changes_log)} Änderungen gespeichert!")
                        st.rerun()