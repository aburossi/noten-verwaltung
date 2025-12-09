import streamlit as st
from datetime import datetime
from utils.data_manager import save_all_data, log_audit_event
# from utils.grading import calculate_grade # Nicht mehr benötigt, da Note direkt eingegeben wird

def render(subject):
    """
    Renders the grading interface for a specific subject.
    Includes: Assignment creation, Weight adjustment, Grade entry, Smart Automation Tools, and LMS Linking.
    """
    st.title(f"📝 {subject}")
    
    # ==========================================
    # 1. CREATE NEW ASSIGNMENT (Unverändert)
    # ==========================================
    with st.expander("➕ Neue Prüfung hinzufügen", expanded=False):
        with st.form(f"add_assignment_{subject}"):
            col1, col2 = st.columns(2)
            
            with col1:
                assignment_name = st.text_input("Prüfungsname*")
                assignment_type = st.selectbox(
                    "Typ*",
                    options=list(st.session_state.config['weightDefaults'].keys())
                )
            
            with col2:
                max_points = st.number_input("Max. Punkte*", min_value=1, value=100)
                default_weight = st.session_state.config['weightDefaults'][assignment_type]
                weight = st.number_input("Gewicht", min_value=0.1, value=default_weight, step=0.1)
            
            # NEW: LMS Link Input
            assignment_url = st.text_input("LMS Link (Optional)", placeholder="https://moodle.bbw.ch/...", help="Link zum Test im LMS")
            
            # ACHTUNG: Skala ist nicht mehr relevant für direkte Noteneingabe, aber beibehalten für Datensatz
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
                        'url': assignment_url.strip(),  # Save URL
                        'date': datetime.now().isoformat(),
                        'grades': {}
                    }
                    st.session_state.assignments.append(new_assignment)
                    
                    # Log & Save
                    log_audit_event("Prüfung erstellt", f"Name: {assignment_name}, Fach: {subject}")
                    save_all_data()
                    
                    st.success(f"✅ Prüfung '{assignment_name}' erstellt")
                    st.rerun()
                else:
                    st.error("Bitte geben Sie einen Prüfungsnamen ein")
    
    # ==========================================
    # 2. LIST ASSIGNMENTS (mit direktem Noten-Input)
    # ==========================================
    subject_assignments = [a for a in st.session_state.assignments if a['subject'] == subject]
    
    if not subject_assignments:
        st.info("Noch keine Prüfungen vorhanden.")
        return
    
    # Sort by date (newest first usually better for grading)
    subject_assignments.sort(key=lambda x: x['date'], reverse=True)
    
    for assignment in subject_assignments:
        # Dynamic label with average if available
        grades_vals = [float(g) for g in assignment['grades'].values() if g]
        avg_display = ""
        if grades_vals:
            avg = sum(grades_vals) / len(grades_vals)
            avg_display = f" (Ø {avg:.2f})"
        
        # Indicator if Link is present
        link_icon = "🔗 " if assignment.get('url') else ""
        
        with st.expander(f"📋 {link_icon}{assignment['name']} {avg_display}"):
            
            # --- HEADER: METADATA & ACTIONS (Unverändert) ---
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.caption(f"Max: {assignment['maxPoints']} Pkt | Skala: {assignment['scaleType']}")
                st.caption(f"Datum: {datetime.fromisoformat(assignment['date']).strftime('%d.%m.%Y')}")
                # NEW: URL Editor
                current_url = assignment.get('url', '')
                new_url = st.text_input("LMS Link", value=current_url, key=f"url_{assignment['id']}", placeholder="https://...")
                
                if new_url != current_url:
                    assignment['url'] = new_url.strip()
                    save_all_data() # Save immediately on change (Streamlit rerun triggers on blur/enter)

            with col2:
                # Edit Weight on the fly
                new_weight = st.number_input(
                    "Gewichtung",
                    min_value=0.1,
                    value=float(assignment['weight']),
                    step=0.1,
                    key=f"weight_{assignment['id']}"
                )
                if new_weight != assignment['weight']:
                    old_w = assignment['weight']
                    assignment['weight'] = new_weight
                    log_audit_event("Gewichtung geändert", f"{assignment['name']}: {old_w} -> {new_weight}")
                    save_all_data()
            
            with col3:
                if st.button("🗑️", key=f"del_{assignment['id']}", help="Prüfung löschen"):
                    log_audit_event("Prüfung gelöscht", f"Name: {assignment['name']}")
                    st.session_state.assignments.remove(assignment)
                    save_all_data()
                    st.rerun()

            # --- PHASE 5: SMART TOOLS (BATCH OPERATIONS) (Unverändert) ---
            # NOTE: Tool 2 (Fill Missing) funktioniert weiterhin, da es Noten setzt.
            with st.popover("⚡ Smart Tools / Automation"):
                st.markdown("#### Batch Operations")
                
                # Tool 1: Curve (Note anheben)
                st.caption("Alle Noten um X anheben (Max 6.0)")
                curve_value = st.number_input("Anhebung", value=0.0, step=0.1, key=f"curve_{assignment['id']}")
                
                if st.button("Curve anwenden", key=f"btn_curve_{assignment['id']}"):
                    count = 0
                    for sid, grade in assignment['grades'].items():
                        try:
                            # Apply curve to existing grades
                            new_grade = min(6.0, float(grade) + curve_value)
                            assignment['grades'][sid] = round(new_grade, 1)
                            count += 1
                        except: pass
                    
                    if count > 0:
                        log_audit_event("Curve angewendet", f"Prüfung: {assignment['name']}, +{curve_value} Note")
                        save_all_data()
                        st.success(f"Curve auf {count} Noten angewendet!")
                        st.rerun()
                
                st.divider()
                
                # Tool 2: Fill Missing (Fehlende auffüllen)
                st.caption("Leere Noten auffüllen (z.B. mit 1.0)")
                default_grade = st.number_input("Standardnote", value=1.0, step=0.5, key=f"def_{assignment['id']}")
                
                if st.button("Fehlende auffüllen", key=f"btn_fill_{assignment['id']}"):
                    count = 0
                    for student in st.session_state.students:
                        if student['id'] not in assignment['grades']:
                            assignment['grades'][student['id']] = default_grade
                            count += 1
                    
                    if count > 0:
                        log_audit_event("Fehlende aufgefüllt", f"Prüfung: {assignment['name']}, Note: {default_grade}")
                        save_all_data()
                        st.success(f"{count} leere Noten aufgefüllt!")
                        st.rerun()
                    else:
                        st.info("Keine fehlenden Noten gefunden.")

            st.write("---")
            
            # --- GRADE ENTRY FORM: GEÄNDERT AUF NOTE STATT PUNKTE ---
            st.write("**Noteneingabe (Note 1.0 bis 6.0):**")
            
            with st.form(f"grades_form_{assignment['id']}"):
                # Grid Layout for inputs
                cols = st.columns(3)
                
                # We need to capture inputs to process them on submit
                input_data = {}
                
                for idx, student in enumerate(st.session_state.students):
                    with cols[idx % 3]:
                        # Note: We display the current grade as the initial value
                        current_grade = assignment['grades'].get(student['id'])
                        
                        # Label construction
                        label = f"{student['Vorname']} {student['Nachname']}"
                        
                        # Input: DIRECT GRADE (Teacher enters grade 1.0-6.0)
                        new_grade_input = st.number_input(
                            label,
                            min_value=1.0,
                            max_value=6.0,
                            value=float(current_grade) if current_grade else None, # Set current grade as default
                            step=0.1, # Allow 0.1 increments
                            format="%.1f", # Display with one decimal place
                            key=f"g_{assignment['id']}_{student['id']}"
                        )
                        
                        # Only store if a valid grade (1.0 to 6.0) is entered
                        if new_grade_input is not None and 1.0 <= new_grade_input <= 6.0:
                            # Round to one decimal place before storing
                            input_data[student['id']] = round(new_grade_input, 1)

                # Submit Button
                if st.form_submit_button("💾 Noten speichern"):
                    changes_log = []
                    
                    for student_id, new_grade in input_data.items():
                        old_grade = assignment['grades'].get(student_id)
                        
                        # Ensure comparison works even if old_grade is stored as string/float
                        old_grade_float = float(old_grade) if old_grade is not None else None
                        
                        # Only update if value is different
                        if old_grade_float != new_grade:
                            # Update assignment data directly with the new grade
                            assignment['grades'][student_id] = new_grade
                            
                            # Find student name for log
                            s_obj = next((s for s in st.session_state.students if s['id'] == student_id), None)
                            s_name = f"{s_obj['Vorname']} {s_obj['Nachname']}" if s_obj else student_id
                            
                            changes_log.append(f"{s_name}: {old_grade_float if old_grade_float else 'N/A'} -> {new_grade}")
                        
                    
                    if changes_log:
                        # Save and Log
                        details = f"Prüfung: {assignment['name']}. {len(changes_log)} Änderung(en) (Direkte Note)."
                        log_audit_event("Noten eingetragen", details)
                        save_all_data()
                        st.success("✅ Noten gespeichert!")
                        st.rerun()
                    else:
                        st.info("Keine Änderungen erkannt (Note ändern zum Speichern).")