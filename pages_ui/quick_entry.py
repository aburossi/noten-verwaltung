import streamlit as st
import pandas as pd
from datetime import datetime
from utils.data_manager import save_all_data, log_audit_event, get_class_registry
from utils.grading import calculate_grade

def generate_quick_entry_print_html(class_name, students, assignments):
    """Generate printable HTML for grade matrix"""
    
    # Build header row
    header_cells = ""
    for a in assignments:
        header_cells += f'<th style="text-align:center; padding:6px; border:1px solid #333; font-size:11px; background-color:#e8e8e8;">{a["name"]}<br><small>({a["subject"][0:3]}, {a["maxPoints"]}P)</small></th>'
    
    # Build data rows
    data_rows = ""
    for s in students:
        row = f'<tr><td style="padding:6px; border:1px solid #333; background-color:#f9f9f9;"><strong>{s["Vorname"]} {s["Nachname"]}</strong></td>'
        
        for a in assignments:
            grade = a['grades'].get(s['id'])
            grade_text = f"{float(grade):.1f}" if grade else "-"
            
            # Color coding
            color = "#d32f2f" if grade and float(grade) < 4.0 else "#388e3c" if grade and float(grade) >= 5.0 else "#333"
            row += f'<td style="text-align:center; padding:6px; border:1px solid #333; color:{color}; font-weight:bold;">{grade_text}</td>'
        
        row += '</tr>'
        data_rows += row
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Notenmatrix - {class_name}</title>
        <style>
            @media print {{
                body {{ margin: 0; }}
                .no-print {{ display: none; }}
                @page {{ size: landscape; }}
            }}
            body {{ font-family: Arial, sans-serif; padding: 15px; font-size: 12px; }}
            .header {{ margin-bottom: 15px; border-bottom: 2px solid #333; padding-bottom: 8px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            .footer {{ margin-top: 20px; padding-top: 8px; border-top: 1px solid #ccc; font-size: 11px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>Notenmatrix: {class_name}</h2>
            <p><strong>Datum:</strong> {datetime.now().strftime("%d.%m.%Y, %H:%M Uhr")} | <strong>Lernende:</strong> {len(students)} | <strong>Prüfungen:</strong> {len(assignments)}</p>
        </div>
        
        <table>
            <thead>
                <tr style="background-color: #f2f2f2;">
                    <th style="text-align:left; padding:6px; border:1px solid #333;">Schüler/in</th>
                    {header_cells}
                </tr>
            </thead>
            <tbody>
                {data_rows}
            </tbody>
        </table>
        
        <div class="footer">
            <p><strong>Legende:</strong> <span style="color:#d32f2f;">■</span> Ungenügend (&lt;4.0) | <span style="color:#388e3c;">■</span> Gut (≥5.0) | <strong>Format:</strong> Querformat empfohlen</p>
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
    st.title("⚡ Schnelleingabe")
    st.caption("Bearbeiten Sie Noten verschiedener Fächer in einer einzigen Ansicht.")

    if not st.session_state.students:
        st.warning("Keine Schüler/innen vorhanden.")
        return

    # Get class name
    registry = get_class_registry()
    current_class = next((c for c in registry if c['id'] == st.session_state.get('current_class_id')), None)
    class_name = current_class['name'] if current_class else "Unbekannte Klasse"

    # 1. Configuration / Filter
    col_filter1, col_filter2, col_print = st.columns([2, 2, 1])
    with col_filter1:
        selected_subjects = st.multiselect(
            "Fächer anzeigen", 
            st.session_state.config['subjects'], 
            default=st.session_state.config['subjects']
        )
    
    with col_filter2:
        recent_limit = st.slider("Nur die letzten X Prüfungen anzeigen", 1, 10, 5)
    
    # 2. Prepare Data for Grid
    visible_assignments = [
        a for a in st.session_state.assignments 
        if a['subject'] in selected_subjects
    ]
    visible_assignments.sort(key=lambda x: x['date'], reverse=True)
    visible_assignments = visible_assignments[:recent_limit]

    if not visible_assignments:
        st.info("Keine Prüfungen gefunden.")
        return

    # PRINT BUTTON
    with col_print:
        if st.button("🖨️ Drucken", help="Notenmatrix drucken"):
            print_html = generate_quick_entry_print_html(
                class_name,
                st.session_state.students,
                visible_assignments
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

    # Build the Dataframe structure
    data = []
    col_map = {} 
    
    for s in st.session_state.students:
        row = {
            "Student_ID": s['id'],
            "Name": f"{s['Vorname']} {s['Nachname']}"
        }
        
        for a in visible_assignments:
            col_name = f"{a['name']} ({a['subject'][0:3]})"
            col_map[col_name] = a['id']
            grade = a['grades'].get(s['id'])
            row[col_name] = float(grade) if grade else None
            
        data.append(row)

    df = pd.DataFrame(data)
    
    # Configure the Data Editor
    column_config = {
        "Student_ID": None,
        "Name": st.column_config.TextColumn("Schüler/in", disabled=True)
    }
    
    for col in df.columns:
        if col not in ["Student_ID", "Name"]:
            column_config[col] = st.column_config.NumberColumn(
                col,
                min_value=0.0,
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
        
        for index, row in edited_df.iterrows():
            s_id = row['Student_ID']
            
            for col_name, assign_id in col_map.items():
                new_val = row[col_name]
                assignment = next((a for a in st.session_state.assignments if a['id'] == assign_id), None)
                if not assignment: continue

                old_val = assignment['grades'].get(s_id)
                
                if pd.notna(new_val):
                    if float(new_val) == 0.0:
                        if s_id in assignment['grades']:
                            del assignment['grades'][s_id]
                            changes_count += 1
                    elif float(new_val) != float(old_val if old_val else 0):
                        assignment['grades'][s_id] = round(float(new_val), 1)
                        changes_count += 1
                
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