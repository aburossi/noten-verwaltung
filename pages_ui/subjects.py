import streamlit as st
from datetime import datetime
from utils.data_manager import save_all_data, log_audit_event
from utils.grading import calculate_weighted_average, get_student_trend

def render(subject):
    st.title(f"📝 {subject}")
    
    # Get assignments for this subject
    subject_assignments = [a for a in st.session_state.assignments if a['subject'] == subject]
    subject_assignments.sort(key=lambda x: x['date'], reverse=True)

    # ==========================================
    # 1. IMPROVED ADD ASSIGNMENT (Templates & Copy)
    # ==========================================
    with st.expander("➕ Neue Prüfung hinzufügen", expanded=False):
        
        # --- Improvement 4: Quick Copy & Templates ---
        col_actions = st.columns([1, 1, 2])
        with col_actions[0]:
            # Copy previous
            if subject_assignments:
                last_assign = subject_assignments[0]
                if st.button(f"📋 Kopiere '{last_assign['name']}'"):
                    st.session_state['new_assign_name'] = f"{last_assign['name']} (Kopie)"
                    st.session_state['new_assign_type'] = last_assign['type']
                    st.session_state['new_assign_weight'] = last_assign['weight']
                    st.session_state['new_assign_max'] = last_assign['maxPoints']
                    st.rerun()

        with col_actions[1]:
            # Template select
            templates = {
                "Standard Test": {"w": 2.0, "m": 100, "t": "Test"},
                "Kleiner Test": {"w": 1.0, "m": 50, "t": "Test"},
                "Vortrag": {"w": 1.0, "m": 20, "t": "Lernpfad"}
            }
            sel_tmpl = st.selectbox("Oder Vorlage:", ["-"] + list(templates.keys()), label_visibility="collapsed")
            if sel_tmpl != "-":
                t = templates[sel_tmpl]
                st.session_state['new_assign_type'] = t['t']
                st.session_state['new_assign_weight'] = t['w']
                st.session_state['new_assign_max'] = t['m']

        with st.form(f"add_assignment_{subject}"):
            col1, col2 = st.columns(2)
            
            # Use session state values for pre-filling if available
            default_name = st.session_state.get('new_assign_name', '')
            default_type_idx = 0
            
            # Resolve Type Index
            type_opts = list(st.session_state.config['weightDefaults'].keys())
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
            
            assignment_url = st.text_input("LMS Link (Optional)", placeholder="https://moodle.bbw.ch/...")
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
                    
                    # Clear temp state
                    keys_to_clear = ['new_assign_name', 'new_assign_type', 'new_assign_weight', 'new_assign_max']
                    for k in keys_to_clear: 
                        if k in st.session_state: del st.session_state[k]

                    log_audit_event("Prüfung erstellt", f"Name: {assignment_name}, Fach: {subject}")
                    save_all_data()
                    st.success(f"✅ Prüfung '{assignment_name}' erstellt")
                    st.rerun()
                else:
                    st.error("Bitte geben Sie einen Prüfungsnamen ein")

    # ==========================================
    # 2. LIST ASSIGNMENTS
    # ==========================================
    if not subject_assignments:
        st.info("Noch keine Prüfungen vorhanden.")
        return
    
    for assignment in subject_assignments:
        grades_vals = [float(g) for g in assignment['grades'].values() if g]
        avg_display = f" (Ø {sum(grades_vals) / len(grades_vals):.2f})" if grades_vals else ""
        link_icon = "🔗 " if assignment.get('url') else ""
        
        with st.expander(f"📋 {link_icon}{assignment['name']} {avg_display}"):
            
            # --- META DATA & TOOLS ---
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

            # --- IMPROVEMENT 3 & 5: VISUAL GRADE ENTRY & MOBILE FRIENDLY ---
            st.markdown("**Noteneingabe**")
            
            # Calculate Live Stats for Context
            if grades_vals:
                curr_avg = sum(grades_vals) / len(grades_vals)
                below_4 = len([g for g in grades_vals if g < 4.0])
                stat_col1, stat_col2 = st.columns(2)
                stat_col1.metric("Ø Live", f"{curr_avg:.2f}")
                stat_col2.metric("Unter 4.0", f"{below_4}", delta_color="inverse")
            
            with st.form(f"grades_form_{assignment['id']}"):
                input_data = {}
                
                # Grid Layout
                for idx, student in enumerate(st.session_state.students):
                    if idx % 2 == 0: cols = st.columns([1, 1]) # 2 cols for mobile friendliness
                    
                    with cols[idx % 2]:
                        current_grade = assignment['grades'].get(student['id'])
                        val = float(current_grade) if current_grade else 0.0
                        
                        # Context: Student Trend
                        trend_icon, trend_val = get_student_trend(student['id'], subject)
                        trend_label = f"{trend_icon}" if trend_icon else ""
                        
                        # Label construction
                        lbl = f"{student['Vorname']} {student['Nachname']} {trend_label}"
                        
                        # Color coding helper (not directly on input, but via help/caption)
                        help_txt = "Note < 4.0" if val > 0 and val < 4.0 else ""
                        
                        # INPUT
                        new_grade_input = st.number_input(
                            lbl,
                            min_value=0.0, max_value=6.0,
                            value=val, step=0.5, # Mobile friendly step
                            format="%.1f",
                            key=f"g_{assignment['id']}_{student['id']}",
                            help=help_txt
                        )
                        
                        if new_grade_input is not None:
                            input_data[student['id']] = round(new_grade_input, 1)

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