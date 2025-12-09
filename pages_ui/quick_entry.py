import streamlit as st
import pandas as pd
from datetime import datetime
from utils.data_manager import save_all_data, log_audit_event
from utils.grading import calculate_grade

def render():
    st.title("⚡ Schnelleingabe")
    st.caption("Bearbeiten Sie Noten verschiedener Fächer in einer einzigen Ansicht.")

    if not st.session_state.students:
        st.warning("Keine Schüler/innen vorhanden.")
        return

    # 1. Configuration / Filter
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        # Select Subjects to show
        selected_subjects = st.multiselect(
            "Fächer anzeigen", 
            st.session_state.config['subjects'], 
            default=st.session_state.config['subjects']
        )
    
    with col_filter2:
        # Limit to recent assignments to keep table clean
        recent_limit = st.slider("Nur die letzten X Prüfungen anzeigen", 1, 10, 5)

    # 2. Prepare Data for Grid
    # We need a matrix: Rows = Students, Cols = Assignments
    
    # Filter assignments based on selection
    visible_assignments = [
        a for a in st.session_state.assignments 
        if a['subject'] in selected_subjects
    ]
    # Sort by date descending and take top X
    visible_assignments.sort(key=lambda x: x['date'], reverse=True)
    visible_assignments = visible_assignments[:recent_limit]

    if not visible_assignments:
        st.info("Keine Prüfungen gefunden.")
        return

    # Build the Dataframe structure
    data = []
    
    # Map Column Names to Assignment IDs (to save back later)
    col_map = {} 
    
    for s in st.session_state.students:
        row = {
            "Student_ID": s['id'], # Hidden ID column
            "Name": f"{s['Vorname']} {s['Nachname']}"
        }
        
        for a in visible_assignments:
            # Create a unique column name
            col_name = f"{a['name']} ({a['subject'][0:3]})"
            col_map[col_name] = a['id']
            
            # Get existing grade
            grade = a['grades'].get(s['id'])
            row[col_name] = float(grade) if grade else None
            
        data.append(row)

    df = pd.DataFrame(data)
    
    # Configure the Data Editor
    column_config = {
        "Student_ID": None, # Hide ID
        # FIXED: Removed 'frozen=True' which caused the error
        "Name": st.column_config.TextColumn("Schüler/in", disabled=True)
    }
    
    # Set config for grade columns (0.0 - 6.0)
    for col in df.columns:
        if col not in ["Student_ID", "Name"]:
            column_config[col] = st.column_config.NumberColumn(
                col,
                min_value=0.0, # 0 allows deletion logically
                max_value=6.0,
                step=0.1,
                format="%.1f"
            )

    # 3. Render Editor
    st.info("💡 Tipp: Navigieren Sie mit Pfeiltasten. Änderungen werden erst beim Klick auf 'Speichern' übernommen.")
    
    edited_df = st.data_editor(
        df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        height=400 if len(data) > 10 else None
    )

    # 4. Save Logic
    if st.button("💾 Alle Änderungen speichern", type="primary", use_container_width=True):
        changes_count = 0
        
        # Iterate over edited dataframe rows
        for index, row in edited_df.iterrows():
            s_id = row['Student_ID']
            
            # Check each assignment column
            for col_name, assign_id in col_map.items():
                new_val = row[col_name]
                
                # Find the actual assignment object in session state
                assignment = next((a for a in st.session_state.assignments if a['id'] == assign_id), None)
                if not assignment: continue

                old_val = assignment['grades'].get(s_id)
                
                # Check for changes
                # Case A: Value entered (not None, not NaN)
                if pd.notna(new_val):
                    # If strictly 0.0 -> Treat as delete request? 
                    # Or valid grade? Assuming 1.0 is min, let's say 0 deletes.
                    if float(new_val) == 0.0:
                        if s_id in assignment['grades']:
                            del assignment['grades'][s_id]
                            changes_count += 1
                    elif float(new_val) != float(old_val if old_val else 0):
                        assignment['grades'][s_id] = round(float(new_val), 1)
                        changes_count += 1
                
                # Case B: Value removed (became None/NaN in editor) but existed before
                elif pd.isna(new_val) and old_val is not None:
                    del assignment['grades'][s_id]
                    changes_count += 1

        if changes_count > 0:
            log_audit_event("Schnelleingabe", f"{changes_count} Noten aktualisiert.")
            save_all_data()
            st.success(f"✅ {changes_count} Änderungen erfolgreich gespeichert!")
            st.rerun()
        else:
            st.info("Keine Änderungen erkannt.")