import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from utils.grading import calculate_weighted_average

def generate_print_html(class_name, students, subjects, config):
    """Generate printable HTML for class overview"""
    
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
            
            # Color coding
            color = "#d32f2f" if avg and avg < 4.0 else "#388e3c" if avg and avg >= 5.0 else "#333"
            row += f'<td style="padding:8px; border-bottom:1px solid #ddd; color:{color}; font-weight:bold;">{avg_text}</td>'
            
            if avg:
                subject_avgs.append(avg)
        
        # Overall average
        overall_avg = round(sum(subject_avgs) / len(subject_avgs), 2) if subject_avgs else None
        overall_text = f"{overall_avg:.2f}" if overall_avg else "-"
        overall_color = "#d32f2f" if overall_avg and overall_avg < 4.0 else "#388e3c" if overall_avg and overall_avg >= 5.0 else "#333"
        
        row += f'<td style="padding:8px; border-bottom:1px solid #ddd; color:{overall_color}; font-weight:bold; background-color:#f5f5f5;">{overall_text}</td>'
        row += "</tr>"
        table_rows += row
    
    # Build subject headers
    subject_headers = "".join([f'<th style="text-align:left; padding:8px; border-bottom:2px solid #333;">{s}</th>' for s in subjects])
    
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
        
        <div class="footer">
            <p><strong>Legende:</strong> <span style="color:#d32f2f;">■</span> Ungenügend (&lt;4.0) | <span style="color:#388e3c;">■</span> Gut (≥5.0)</p>
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
            # Open in new window for printing
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
    # STANDARD OVERVIEW
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
            num_assignments = len([a for a in st.session_state.assignments if a['subject'] == subject])
            
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
    table_data = []
    for student in st.session_state.students:
        row = {
            'Name': f"{student['Vorname']} {student['Nachname']}",
            'Anmeldename': student['Anmeldename']
        }
        subject_avgs = []
        for subject in st.session_state.config['subjects']:
            avg = calculate_weighted_average(student['id'], subject)
            row[subject] = f"{avg:.2f}" if avg else "-"
            if avg:
                subject_avgs.append(avg)
        
        overall_avg = round(sum(subject_avgs) / len(subject_avgs), 2) if subject_avgs else None
        row['Gesamt Ø'] = f"{overall_avg:.2f}" if overall_avg else "-"
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)