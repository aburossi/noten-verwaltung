import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from utils.grading import calculate_weighted_average, round_to_half

def get_color_for_grade(grade):
    """Return color hex code based on grade thresholds"""
    if grade is None: return "#333333"
    
    val = float(grade)
    if val >= 4.5:
        return "#28a745" # Green
    elif val >= 4.0:
        return "#ffc107" # Yellow (Darker for readability)
    elif val >= 3.5:
        return "#fd7e14" # Orange
    else:
        return "#dc3545" # Red

def generate_print_html(class_name, students, subjects, config):
    """Generate printable HTML for class overview with new color coding"""
    
    # Build student data
    table_rows = ""
    for student in students:
        row = f"""
        <tr>
            <td style="padding:8px; border-bottom:1px solid #ddd;">{student['Vorname']} {student['Nachname']}</td>
            <td style="padding:8px; border-bottom:1px solid #ddd;">{student['Anmeldename']}</td>
        """
        
        subject_avgs = []
        for subject in subjects:
            avg = calculate_weighted_average(student['id'], subject)
            avg_text = f"{avg:.2f}" if avg else "-"
            
            # Rounded Subject Grade
            zeugnis_val = round_to_half(avg)
            zeugnis_text = f"{zeugnis_val:.1f}" if zeugnis_val else "-"
            
            # Colors
            color_avg = get_color_for_grade(avg)
            if color_avg == "#ffc107": color_avg = "#d39e00"
            
            color_zeugnis = get_color_for_grade(zeugnis_val)
            if color_zeugnis == "#ffc107": color_zeugnis = "#d39e00"
            
            row += f'<td style="padding:8px; border-bottom:1px solid #ddd; color:{color_avg};">{avg_text}</td>'
            row += f'<td style="padding:8px; border-bottom:1px solid #ddd; color:{color_zeugnis}; font-weight:bold; background-color:#f9f9f9;">{zeugnis_text}</td>'
            
            if avg:
                subject_avgs.append(avg)
        
        # Overall average
        overall_avg = round(sum(subject_avgs) / len(subject_avgs), 2) if subject_avgs else None
        overall_text = f"{overall_avg:.2f}" if overall_avg else "-"
        
        overall_color = get_color_for_grade(overall_avg)
        if overall_color == "#ffc107": overall_color = "#d39e00"
        
        row += f'<td style="padding:8px; border-bottom:1px solid #ddd; color:{overall_color}; font-weight:bold; background-color:#e8f0fe;">{overall_text}</td>'
        row += "</tr>"
        table_rows += row
    
    # Build subject headers
    # We need 2 columns per subject: Name + Note
    subject_headers = ""
    for s in subjects:
        subject_headers += f'<th style="text-align:left; padding:8px; border-bottom:2px solid #333;">{s}</th>'
        subject_headers += f'<th style="text-align:left; padding:8px; border-bottom:2px solid #333; background-color:#f9f9f9;">Note</th>'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Klassenübersicht - {class_name}</title>
        <style>
            @media print {{
                body {{ margin: 0; }}
                .no-print {{ display: none; }}
            }}
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            .header {{ margin-bottom: 20px; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            .footer {{ margin-top: 30px; padding-top: 10px; border-top: 1px solid #ccc; font-size: 12px; color: #666; }}
            .legend {{ margin-top: 10px; font-size: 12px; }}
            .legend span {{ margin-right: 15px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Klassenübersicht: {class_name}</h1>
            <p><strong>Datum:</strong> {datetime.now().strftime("%d.%m.%Y, %H:%M Uhr")}</p>
            <p><strong>Anzahl Lernende:</strong> {len(students)}</p>
        </div>
        
        <table>
            <thead>
                <tr style="background-color: #f2f2f2;">
                    <th style="text-align:left; padding:8px; border-bottom:2px solid #333;">Name</th>
                    <th style="text-align:left; padding:8px; border-bottom:2px solid #333;">Anmeldename</th>
                    {subject_headers}
                    <th style="text-align:left; padding:8px; border-bottom:2px solid #333; background-color:#e8e8e8;">Gesamt Ø</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        
        <div class="legend">
            <strong>Legende:</strong> 
            <span style="color:#28a745;">■ ≥ 4.5 (Gut)</span>
            <span style="color:#d39e00;">■ 4.0-4.5 (Genügend)</span>
            <span style="color:#fd7e14;">■ 3.5-4.0 (Ungnügend)</span>
            <span style="color:#dc3545;">■ < 3.5 (Kritisch)</span>
        </div>
        
        <div class="footer">
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

def render():
    st.title("📊 Übersicht")
    
    if not st.session_state.students:
        st.info("Keine Schüler/innen geladen. Bitte importieren Sie Schülerdaten.")
        return
    
    # Get current class name
    from utils.data_manager import get_class_registry
    registry = get_class_registry()
    current_class = next((c for c in registry if c['id'] == st.session_state.get('current_class_id')), None)
    class_name = current_class['name'] if current_class else "Unbekannte Klasse"
    
    # ==========================================
    # PRINT BUTTON
    # ==========================================
    col_title, col_print = st.columns([5, 1])
    with col_print:
        if st.button("🖨️ Drucken", help="Klassenübersicht drucken"):
            print_html = generate_print_html(
                class_name,
                st.session_state.students,
                st.session_state.config['subjects'],
                st.session_state.config
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
    
    # ==========================================
    # WEEKLY WORKFLOW SUMMARY
    # ==========================================
    with st.container(border=True):
        st.subheader("📅 Diese Woche")
        
        now = datetime.now()
        start_of_week = now - timedelta(days=now.weekday())
        
        graded_count = 0
        for a in st.session_state.assignments:
            try:
                a_date = datetime.fromisoformat(a['date'])
                if a_date >= start_of_week:
                    graded_count += 1
            except: pass
            
        at_risk_count = 0
        for s in st.session_state.students:
            is_risk = False
            for subj in st.session_state.config['subjects']:
                avg = calculate_weighted_average(s['id'], subj)
                if avg and avg < 4.0:
                    is_risk = True
            if is_risk: at_risk_count += 1
            
        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1:
            st.metric("✅ Prüfungen diese Woche", f"{graded_count}", help="Anzahl Prüfungen mit Datum in dieser Woche")
        with kpi2:
            color = "inverse" if at_risk_count > 0 else "normal"
            st.metric("⚠️ Handlungsbedarf", f"{at_risk_count} Schüler/innen", delta="unter 4.0", delta_color=color)
        with kpi3:
            st.metric("👥 Klasse", f"{len(st.session_state.students)}", "Lernende")

    st.write("---")

    # ==========================================
    # STANDARD OVERVIEW (WITH COLOR)
    # ==========================================
    col1, col2 = st.columns(2)
    
    for idx, subject in enumerate(st.session_state.config['subjects']):
        with col1 if idx == 0 else col2:
            st.subheader(subject)
            
            avg_grades = []
            for student in st.session_state.students:
                avg = calculate_weighted_average(student['id'], subject)
                if avg is not None:
                    avg_grades.append(avg)
            
            class_avg = round(sum(avg_grades) / len(avg_grades), 2) if avg_grades else 0
            
            st.metric("Klassendurchschnitt", f"{class_avg:.2f}")
            
            if avg_grades:
                fig = px.histogram(
                    x=avg_grades, nbins=20,
                    labels={'x': 'Note', 'y': 'Anzahl'}
                )
                fig.update_layout(showlegend=False, height=200, margin=dict(l=20, r=20, t=20, b=20))
                fig.update_xaxes(range=[1, 6])
                st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Alle Schüler/innen")
    
    # Sorting Control
    sort_option = st.radio("Sortierung", ["Vorname", "Nachname"], horizontal=True)
    
    sorted_students = st.session_state.students
    if sort_option == "Nachname":
        sorted_students = sorted(st.session_state.students, key=lambda s: (s['Nachname'], s['Vorname']))
    else:
        sorted_students = sorted(st.session_state.students, key=lambda s: (s['Vorname'], s['Nachname']))
    
    # 1. Prepare Data
    table_data = []
    
    # Track dynamic column names
    subject_cols = []
    
    for student in sorted_students:
        row = {
            'Name': f"{student['Vorname']} {student['Nachname']}",
            'Anmeldename': student['Anmeldename']
        }
        subject_avgs = []
        for subject in st.session_state.config['subjects']:
            avg = calculate_weighted_average(student['id'], subject)
            
            # 1. Raw Subject Average
            row[subject] = float(f"{avg:.2f}") if avg else None
            if subject not in subject_cols: subject_cols.append(subject)
            
            # 2. Rounded Subject Average (Zeugnisnote)
            zeugnis_col_name = f"{subject} (Z)"
            zeugnis_val = round_to_half(avg)
            row[zeugnis_col_name] = zeugnis_val
            if zeugnis_col_name not in subject_cols: subject_cols.append(zeugnis_col_name)

            if avg:
                subject_avgs.append(avg)

        # Overall Average (Arithmetic)
        overall_avg = round(sum(subject_avgs) / len(subject_avgs), 2) if subject_avgs else None
        row['Gesamt Ø'] = float(f"{overall_avg:.2f}") if overall_avg else None
        
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    
    # 2. Add Class Averages Row
    if not df.empty:
        avg_row = {'Name': '<b>Ø KLASSE</b>', 'Anmeldename': ''}
        
        # Calculate averages for all numeric columns
        for col in subject_cols + ['Gesamt Ø']:
            if col in df.columns:
                # Filter out None/NaN before processing
                valid_values = [x for x in df[col] if pd.notna(x)]
                if valid_values:
                    avg_val = sum(valid_values) / len(valid_values)
                    avg_row[col] = avg_val
                else:
                    avg_row[col] = None
        
        # Create a DataFrame for the average row
        avg_df = pd.DataFrame([avg_row])
        
        # Append to main DataFrame
        df = pd.concat([df, avg_df], ignore_index=True)

    # 3. Define Style Function
    def color_grades(val):
        if pd.isna(val) or isinstance(val, str):
            return ''
        
        color = ''
        if val >= 4.5:
            color = '#28a745' # Green
        elif val >= 4.0:
            color = '#d39e00' # Yellow/Gold (Darker for readability)
        elif val >= 3.5:
            color = '#fd7e14' # Orange
        else:
            color = '#dc3545' # Red
            
        return f'color: {color}; font-weight: bold'

    # 4. Apply Style & Formatting
    numeric_cols = subject_cols + ['Gesamt Ø']
    styled_df = df.style.map(color_grades, subset=numeric_cols)
    
    # Identify rows
    student_rows = df.index[:-1] if not df.empty and "Ø KLASSE" in df.iloc[-1]['Name'] else df.index
    avg_row_idx = df.index[-1] if not df.empty and "Ø KLASSE" in df.iloc[-1]['Name'] else None
    
    # Format Student Rows
    # Raw subjects & Overall -> 2 decimals
    raw_cols = [c for c in (st.session_state.config['subjects'] + ['Gesamt Ø']) if c in df.columns]
    styled_df = styled_df.format("{:.2f}", subset=pd.IndexSlice[student_rows, raw_cols], na_rep="-")
    
    # Rounded columns -> 1 decimal
    rounded_cols = [c for c in subject_cols if "(Z)" in c and c in df.columns]
    styled_df = styled_df.format("{:.1f}", subset=pd.IndexSlice[student_rows, rounded_cols], na_rep="-")
    
    # Format Average Row (All numeric -> 2 decimals)
    if avg_row_idx is not None:
         styled_df = styled_df.format("{:.2f}", subset=pd.IndexSlice[avg_row_idx, numeric_cols], na_rep="-")

    # 5. Column Configuration (Narrow columns)
    column_config = {
        "Name": st.column_config.TextColumn("Name", width="medium", pinned=True),
        "Anmeldename": st.column_config.TextColumn("Anmeldename", width="medium"),
        # Remove format here to let Styler control it
        "Gesamt Ø": st.column_config.NumberColumn("Gesamt Ø", width="small"),
    }
    
    for sub in st.session_state.config['subjects']:
         # Remove format here to let Styler control it
         column_config[sub] = st.column_config.NumberColumn(sub, width="small")
         column_config[f"{sub} (Z)"] = st.column_config.NumberColumn(f"{sub} (Note)", help=f"Zeugnisnote {sub}", width="small")

    st.dataframe(
        styled_df, 
        use_container_width=True, 
        hide_index=True, 
        height=500,
        column_config=column_config
    )
    
    st.caption("Legende: 🟢 ≥ 4.5 | 🟡 4.0 - 4.5 | 🟠 3.5 - 4.0 | 🔴 < 3.5")