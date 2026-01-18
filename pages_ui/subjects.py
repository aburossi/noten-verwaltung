import streamlit as st
import pandas as pd
import io
from datetime import datetime
from utils.data_manager import save_all_data, log_audit_event, get_class_registry
from utils.grading import calculate_weighted_average, get_student_trend, calculate_grade

def generate_assignment_print_html(class_name, subject, assignment, students):
    """Generate printable HTML for a specific assignment including comments"""
    
    # Ensure comments dict exists
    comments = assignment.get('comments', {})

    # Build grade rows
    grade_rows = ""
    grades_list = []
    
    for s in students:
        grade = assignment['grades'].get(s['id'])
        comment = comments.get(s['id'], "")
        
        grade_text = f"{float(grade):.1f}" if grade else "-"
        
        if grade:
            grades_list.append(float(grade))
        
        color = "#d32f2f" if grade and float(grade) < 4.0 else "#388e3c" if grade and float(grade) >= 5.0 else "#333"
        
        grade_rows += f"""
        <tr>
            <td style="padding:8px; border-bottom:1px solid #ddd;">{s['Vorname']} {s['Nachname']}</td>
            <td style="padding:8px; border-bottom:1px solid #ddd;">{s['Anmeldename']}</td>
            <td style="padding:8px; border-bottom:1px solid #ddd; text-align:center; color:{color}; font-weight:bold; font-size:14px;">{grade_text}</td>
            <td style="padding:8px; border-bottom:1px solid #ddd; font-style:italic; color:#555;">{comment}</td>
            <td style="padding:8px; border-bottom:1px solid #ddd; text-align:center;">________</td>
        </tr>
        """
    
    # Calculate statistics
    class_avg = round(sum(grades_list) / len(grades_list), 2) if grades_list else 0
    below_4 = len([g for g in grades_list if g < 4.0])
    above_5 = len([g for g in grades_list if g >= 5.0])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Prüfung: {assignment['name']}</title>
        <style>
            @media print {{
                body {{ margin: 0; }}
                .no-print {{ display: none; }}
            }}
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            .header {{ margin-bottom: 20px; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            .info-box {{ background-color: #f5f5f5; padding: 15px; margin-bottom: 20px; border-left: 4px solid #333; }}
            table {{ width: 100%; border-collapse: collapse; }}
            .footer {{ margin-top: 30px; padding-top: 10px; border-top: 1px solid #ccc; font-size: 12px; color: #666; }}
            .stats {{ margin: 20px 0; }}
            .stat-box {{ display: inline-block; padding: 10px 15px; margin-right: 15px; background-color: #e8f5e9; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Prüfung: {assignment['name']}</h1>
            <p><strong>Klasse:</strong> {class_name} | <strong>Fach:</strong> {subject}</p>
        </div>
        
        <div class="info-box">
            <p style="margin:5px 0;"><strong>Typ:</strong> {assignment['type']} | <strong>Gewichtung:</strong> {assignment['weight']:.1f} | <strong>Max. Punkte:</strong> {assignment['maxPoints']}</p>
            <p style="margin:5px 0;"><strong>Datum:</strong> {datetime.fromisoformat(assignment['date']).strftime("%d.%m.%Y")} | <strong>Bewertung:</strong> {assignment['scaleType']}</p>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <strong>Klassenschnitt:</strong> {class_avg:.2f}
            </div>
            <div class="stat-box" style="background-color: #ffebee;">
                <strong>Ungenügend (&lt;4.0):</strong> {below_4}
            </div>
            <div class="stat-box" style="background-color: #e8f5e9;">
                <strong>Gut (≥5.0):</strong> {above_5}
            </div>
        </div>
        
        <table>
            <thead>
                <tr style="background-color: #f2f2f2;">
                    <th style="text-align:left; padding:8px; border-bottom:2px solid #333;">Name</th>
                    <th style="text-align:left; padding:8px; border-bottom:2px solid #333;">Anmeldename</th>
                    <th style="text-align:center; padding:8px; border-bottom:2px solid #333; width:80px;">Note</th>
                    <th style="text-align:left; padding:8px; border-bottom:2px solid #333;">Kommentar</th>
                    <th style="text-align:center; padding:8px; border-bottom:2px solid #333; width:100px;">Unterschrift</th>
                </tr>
            </thead>
            <tbody>
                {grade_rows}
            </tbody>
        </table>
        
        <div class="footer">
            <p><strong>Gedruckt am:</strong> {datetime.now().strftime("%d.%m.%Y, %H:%M Uhr")}</p>
            <p>Unterschrift Lehrperson: _________________________________</p>
        </div>
        
        <div class="no-print" style="margin-top: 20px; text-align: center;">
            <button onclick="window.print()" style="padding: 10px 20px; font-size: 16px; cursor: pointer;">🖨️ Drucken</button>
            <button onclick="window.close()" style="padding: 10px 20px; font-size: 16px; cursor: pointer; margin-left: 10px;">Schließen</button>
        </div>
    </body>
    </html>
    """
    return html

def render(subject):
    st.title(f"📝 {subject}")
    
    # Get class name
    registry = get_class_registry()
    current_class = next((c for c in registry if c['id'] == st.session_state.get('current_class_id')), None)
    class_name = current_class['name'] if current_class else "Unbekannte Klasse"
    
    subject_assignments = [a for a in st.session_state.assignments if a['subject'] == subject]
    subject_assignments.sort(key=lambda x: x['date'], reverse=True)

    # ==========================================
    # 1. ADD ASSIGNMENT
    # ==========================================
    with st.expander("➕ Neue Prüfung hinzufügen", expanded=False):
        
        tab_create, tab_import = st.tabs(["✍️ Manuell erstellen", "📥 Aus Excel importieren"])

        with tab_create:
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
                            'grades': {},
                            'points': {}, # Initialize points
                            'comments': {} # Initialize comments
                        }
                        st.session_state.assignments.append(new_assignment)
                        for k in ['new_assign_name', 'new_assign_type', 'new_assign_weight', 'new_assign_max']: 
                            if k in st.session_state: del st.session_state[k]

                        log_audit_event("Prüfung erstellt", f"Name: {assignment_name}")
                        save_all_data()
                        st.success(f"✅ Prüfung '{assignment_name}' erstellt")
                        st.rerun()
                    else:
                        st.error("Bitte geben Sie einen Namen ein")

        with tab_import:
            st.info(f"Importieren Sie eine Notenliste direkt in das Fach **{subject}**.")
            
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
                                'subject': subject,
                                'type': imp_type,
                                'weight': imp_weight,
                                'maxPoints': imp_max,
                                'scaleType': '60% Scale',
                                'url': imp_url.strip(),
                                'date': datetime.now().isoformat(),
                                'grades': {},
                                'points': {},
                                'comments': {} # Initialize comments
                            }
                            
                            count = 0
                            for _, row in df_imp.iterrows():
                                aname = str(row['Anmeldename']).strip()
                                points = row.get('Punkte', 0)
                                student = next((s for s in st.session_state.students if s['Anmeldename'] == aname), None)
                                
                                if student and pd.notna(points):
                                    try:
                                        p_val = float(points)
                                        # Save points
                                        new_assign['points'][student['id']] = p_val
                                        
                                        # Calculate Grade
                                        g_info = calculate_grade(p_val, float(imp_max))
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
    # 2. LIST ASSIGNMENTS
    # ==========================================
    if not subject_assignments:
        st.info("Noch keine Prüfungen vorhanden.")
        return
    
    for assignment in subject_assignments:
        # Backward compatibility for existing assignments without comments
        if 'comments' not in assignment:
            assignment['comments'] = {}

        grades_vals = [float(g) for g in assignment['grades'].values() if g]
        avg_display = f" (Ø {sum(grades_vals) / len(grades_vals):.2f})" if grades_vals else ""
        link_icon = "🔗 " if assignment.get('url') else ""
        
        with st.expander(f"📋 {link_icon}{assignment['name']} {avg_display}"):
            # PRINT BUTTON in header
            col_header, col_print_btn = st.columns([5, 1])
            with col_print_btn:
                if st.button("🖨️", key=f"print_{assignment['id']}", help="Prüfung drucken"):
                    print_html = generate_assignment_print_html(
                        class_name,
                        subject,
                        assignment,
                        st.session_state.students
                    )
                    st.components.v1.html(
                        f"""
                        <script>
                            var printWindow = window.open('', '_blank');
                            printWindow.document.write(`{print_html.replace('`', '\\`')}`);
                            printWindow.document.close();
                        </script>
                        """,
                        height=0
                    )
            
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
            
            if grades_vals:
                curr_avg = sum(grades_vals) / len(grades_vals)
                below_4 = len([g for g in grades_vals if g < 4.0])
                stat_col1, stat_col2 = st.columns(2)
                stat_col1.metric("Ø Live", f"{curr_avg:.2f}")
                stat_col2.metric("Unter 4.0", f"{below_4}", delta_color="inverse")
            
            # --- UPDATED: List View for Grades + Comments ---
            st.write("**Punkte & Kommentare eingeben:**")
            st.caption("Geben Sie die Punktzahl ein. Die Note wird automatisch berechnet.")
            
            # Init points dict if missing (legacy compatibility)
            if 'points' not in assignment:
                assignment['points'] = {}

            with st.form(f"grades_form_{assignment['id']}"):
                input_points = {}
                comment_data = {}
                
                # Header
                h1, h2, h3, h4 = st.columns([2, 1, 1, 2])
                h1.markdown("**Name**")
                h2.markdown("**Punkte**")
                h3.markdown("**Note**")
                h4.markdown("**Kommentar**")
                
                for student in st.session_state.students:
                    c_name, c_points, c_grade_display, c_comm = st.columns([2, 1, 1, 2])
                    
                    # 1. Name Column
                    trend_icon, _ = get_student_trend(student['id'], subject)
                    c_name.markdown(f"{student['Vorname']} {student['Nachname']} {trend_icon if trend_icon else ''}")
                    
                    # 2. Points Input
                    current_points = assignment['points'].get(student['id'])
                    # If no points but grade exists (legacy), we can't easily guess points. Leave 0.0 or None.
                    # User must enter points to update.
                    
                    val_points = float(current_points) if current_points is not None else 0.0
                    
                    new_points_input = c_points.number_input(
                        "Punkte", 
                        min_value=0.0, 
                        max_value=float(assignment['maxPoints']), 
                        value=val_points, 
                        step=0.5, 
                        format="%.1f", 
                        key=f"p_{assignment['id']}_{student['id']}",
                        label_visibility="collapsed"
                    )
                    
                    # Store input for saving
                    input_points[student['id']] = new_points_input

                    # 3. Calculated Grade Display (Dynamic Preview based on SAVED or INPUT if strictly reactive? Form submit means we see saved)
                    # Actually, we want to see the grade for the *saved* points or the *current* grade.
                    # Since we are in a form, we can't react live to input without st.session_state callbacks or rerun, but form prevents rerun.
                    # So we display the grade corresponding to the CURRENT saved state.
                    
                    # However, if points are missing but grade exists (legacy), show grade.
                    saved_grade = assignment['grades'].get(student['id'])
                    
                    # Calculate what the grade WOULD be based on current points (if we had live update).
                    # But here we just show the stored grade.
                    grade_display = "-"
                    grade_color = "#333"
                    
                    if saved_grade:
                        grade_val = float(saved_grade)
                        grade_display = f"{grade_val:.1f}"
                        if grade_val >= 5.0: grade_color = "#388e3c"
                        elif grade_val < 4.0: grade_color = "#d32f2f"
                    
                    c_grade_display.markdown(f"<span style='font-size:16px; font-weight:bold; color:{grade_color}'>{grade_display}</span>", unsafe_allow_html=True)
                        
                    # 4. Comment Column
                    current_comment = assignment['comments'].get(student['id'], "")
                    new_comment = c_comm.text_input(
                        "Kommentar",
                        value=current_comment,
                        key=f"c_{assignment['id']}_{student['id']}",
                        label_visibility="collapsed",
                        placeholder="Optional"
                    )
                    if new_comment is not None:
                        comment_data[student['id']] = new_comment

                st.write("")
                if st.form_submit_button("💾 Punkte & Kommentare speichern", type="primary", use_container_width=True):
                    changes_log = []
                    
                    max_p = float(assignment['maxPoints'])
                    
                    for student_id, new_p_val in input_points.items():
                        # Logic:
                        # If 0.0 -> Assume empty/delete? Or is 0 points valid?
                        # Usually 0 points is valid (Note 1).
                        # We need a way to clear? Maybe empty input? st.number_input doesn't allow None easily if initialized with float.
                        # Let's assume if it matches "current_points" (which might be None->0.0), no change?
                        # Check if changed
                        
                        old_p_val = assignment['points'].get(student_id)
                        old_p_float = float(old_p_val) if old_p_val is not None else 0.0
                        
                        # Only update if changed or if it was None and now is 0.0 (explicit set)
                        # Actually easier: Just save whatever is in the box?
                        # But we need to handle "Delete".
                        # For now, let's update if different.
                        
                        # Handle Legacy case where points were missing but grade existed.
                        # If user leaves it at 0.0, and grade exists, do we overwrite grade to 1.0 (0 points)?
                        # DANGER.
                        # If legacy (no points, has grade) and user submits 0.0 -> It might be they didn't touch it.
                        # We should skip if points were None and input is 0.0 ? 
                        # But what if they WANT to give 0 points?
                        
                        # Better approach: check if modified using session state? form doesn't support that easily.
                        # Let's trust the input. If legacy user wants to keep grade, they must enter points.
                        # OR: We only update if points dict has entry OR input > 0.
                        
                        if new_p_val == 0.0 and old_p_val is None and student_id in assignment['grades']:
                             # Legacy protection: User didn't enter points (default 0), but grade exists. Don't overwrite.
                             continue
                        
                        if new_p_val != old_p_float or (old_p_val is None and new_p_val == 0.0):
                             # Update Points
                             assignment['points'][student_id] = new_p_val
                             
                             # Calculate and Update Grade
                             g_res = calculate_grade(new_p_val, max_p, assignment.get('scaleType', '60% Scale'))
                             if g_res:
                                 assignment['grades'][student_id] = g_res['note']
                             
                             changes_log.append("Updated Grade")
                            
                    # Update Comments
                    for student_id, new_comment in comment_data.items():
                        old_comment = assignment['comments'].get(student_id, "")
                        if new_comment.strip() != old_comment:
                            if new_comment.strip():
                                assignment['comments'][student_id] = new_comment.strip()
                            else:
                                if student_id in assignment['comments']:
                                    del assignment['comments'][student_id]
                            changes_log.append("Changed Comment")
                    
                    if changes_log:
                        save_all_data()
                        st.success(f"✅ Noten aktualisiert!")
                        st.rerun()
