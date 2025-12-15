import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.grading import calculate_weighted_average

def get_class_performance_data(subject):
    """Prepare dataframe for class analytics"""
    assignments = [a for a in st.session_state.assignments if a['subject'] == subject]
    students = st.session_state.students
    
    if not assignments:
        return None
    
    # Sort assignments by date
    assignments.sort(key=lambda x: x['date'])
    
    data = []
    for a in assignments:
        grades = [float(g) for g in a['grades'].values() if g]
        if grades:
            avg = sum(grades) / len(grades)
            data.append({
                'Assignment': a['name'],
                'Date': datetime.fromisoformat(a['date']),
                'Average': avg,
                'Type': a['type'],
                'MaxPoints': a['maxPoints']
            })
            
    return pd.DataFrame(data)

def get_student_performance_data(student_id, subject):
    """Prepare dataframe for individual student analytics"""
    assignments = [a for a in st.session_state.assignments if a['subject'] == subject]
    assignments.sort(key=lambda x: x['date'])
    
    data = []
    for a in assignments:
        student_grade = a['grades'].get(student_id)
        
        # Calculate class average for this specific assignment
        all_grades = [float(g) for g in a['grades'].values() if g]
        class_avg = sum(all_grades) / len(all_grades) if all_grades else 0
        
        if student_grade:
            data.append({
                'Assignment': a['name'],
                'Date': datetime.fromisoformat(a['date']),
                'Grade': float(student_grade),
                'ClassAverage': class_avg,
                'Difference': float(student_grade) - class_avg
            })
            
    return pd.DataFrame(data)

def render():
    st.title("📈 Analyse & Berichte")
    
    subject = st.selectbox("Fach auswählen", st.session_state.config['subjects'])
    
    tab_class, tab_student = st.tabs(["🏫 Klassenanalyse", "👤 Schülerdetails"])
    
    # === TAB 1: CLASS ANALYTICS ===
    with tab_class:
        df_class = get_class_performance_data(subject)
        
        if df_class is None or df_class.empty:
            st.info("Keine Daten verfügbar.")
        else:
            # 1. KPIs and Alerts
            st.subheader("Aktueller Status")
            col1, col2, col3 = st.columns(3)
            
            # Identify "At Risk" students (< 4.0) with Grades
            at_risk = []
            for s in st.session_state.students:
                avg = calculate_weighted_average(s['id'], subject)
                if avg and avg < 4.0:
                    at_risk.append({
                        "name": f"{s['Vorname']} {s['Nachname']}",
                        "avg": avg,
                        "id": s['id']
                    })
            
            # Sort by lowest grade first
            at_risk.sort(key=lambda x: x['avg'])

            with col1:
                st.metric("Anzahl Prüfungen", len(df_class))
            with col2:
                all_avgs = [calculate_weighted_average(s['id'], subject) for s in st.session_state.students]
                all_avgs = [a for a in all_avgs if a is not None]
                real_class_avg = sum(all_avgs)/len(all_avgs) if all_avgs else 0
                st.metric("Klassendurchschnitt (Gesamt)", f"{real_class_avg:.2f}")
            with col3:
                if at_risk:
                    st.metric("⚠️ Risikoschüler (< 4.0)", len(at_risk), delta_color="inverse")
                else:
                    st.metric("Risikoschüler", "0", "✅")

            if at_risk:
                # NEW: Clickable list (Expander)
                with st.expander(f"🚨 {len(at_risk)} Schüler/innen unter 4.0 anzeigen (Klicken für Details)", expanded=True):
                    
                    risk_df = pd.DataFrame(at_risk)
                    risk_df['avg'] = risk_df['avg'].apply(lambda x: f"{x:.2f}")
                    
                    st.dataframe(
                        risk_df[['name', 'avg']], 
                        column_config={
                            "name": "Name",
                            "avg": "Durchschnitt"
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                    st.caption("Wechseln Sie zum Reiter '👤 Schülerdetails' um einzelne Verläufe zu sehen.")

            st.write("---")

            # 2. Charts
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("Verlauf Klassendurchschnitt")
                fig_trend = px.line(df_class, x='Date', y='Average', markers=True, 
                                   title='Durchschnitt pro Prüfung', hover_data=['Assignment'])
                fig_trend.add_hline(y=4.0, line_dash="dash", line_color="red", annotation_text="Genügend (4.0)")
                fig_trend.update_yaxes(range=[1, 6])
                st.plotly_chart(fig_trend, use_container_width=True)
            
            with c2:
                st.subheader("Schwierigkeitsgrad (Härteste Prüfungen)")
                # Sort by lowest average
                df_difficulty = df_class.sort_values('Average')
                fig_diff = px.bar(df_difficulty, x='Average', y='Assignment', orientation='h',
                                 title='Prüfungen sortiert nach Durchschnitt', color='Average',
                                 color_continuous_scale='RdYlGn')
                fig_diff.update_xaxes(range=[1, 6])
                st.plotly_chart(fig_diff, use_container_width=True)

    # === TAB 2: STUDENT DETAILS ===
    with tab_student:
        selected_student = st.selectbox(
            "Schüler/in auswählen", 
            st.session_state.students, 
            format_func=lambda s: f"{s['Vorname']} {s['Nachname']}"
        )
        
        if selected_student:
            df_student = get_student_performance_data(selected_student['id'], subject)
            
            if df_student.empty:
                st.info("Keine Noten vorhanden.")
            else:
                st.write("---")
                # Student Header
                cols = st.columns([1, 3])
                student_avg = calculate_weighted_average(selected_student['id'], subject)
                
                with cols[0]:
                    st.metric("Durchschnitt", f"{student_avg:.2f}", 
                             delta=f"{student_avg - 4.0:.2f} zu Note 4",
                             delta_color="normal")
                
                with cols[1]:
                    # Comparison Chart
                    fig_comp = go.Figure()
                    fig_comp.add_trace(go.Scatter(
                        x=df_student['Date'], y=df_student['Grade'],
                        mode='lines+markers', name='Note',
                        line=dict(color='blue', width=3)
                    ))
                    fig_comp.add_trace(go.Scatter(
                        x=df_student['Date'], y=df_student['ClassAverage'],
                        mode='lines', name='Klassenschnitt',
                        line=dict(color='gray', dash='dot')
                    ))
                    fig_comp.update_layout(title="Vergleich zur Klasse", yaxis_range=[1, 6], height=300)
                    st.plotly_chart(fig_comp, use_container_width=True)
                
                # Detailed Table
                st.subheader("Notenliste")
                
                # Add conditional formatting visual
                def highlight_grade(val):
                    color = 'red' if val < 4.0 else 'green'
                    return f'color: {color}; font-weight: bold'

                st.dataframe(
                    df_student[['Assignment', 'Grade', 'ClassAverage', 'Difference']],
                    column_config={
                        "Assignment": "Prüfung",
                        "Grade": "Note",
                        "ClassAverage": "Ø Klasse",
                        "Difference": "Abweichung"
                    },
                    use_container_width=True
                )
                
                # Print View (Simple HTML generation)
                with st.expander("🖨️ Bericht drucken (Vorschau)"):
                    date_str = datetime.now().strftime("%d.%m.%Y")
                    report_html = f"""
                    <div style="padding: 20px; border: 1px solid #ccc; font-family: Arial;">
                        <h2>Notenblatt: {subject}</h2>
                        <p><strong>Schüler/in:</strong> {selected_student['Vorname']} {selected_student['Nachname']}<br>
                        <strong>Klasse:</strong> {st.session_state.get('current_class_id', 'Unbekannt')}<br>
                        <strong>Datum:</strong> {date_str}</p>
                        <hr>
                        <h3>Gesamtschnitt: {student_avg:.2f}</h3>
                        <table style="width:100%; border-collapse: collapse;">
                            <tr style="background-color: #f2f2f2;">
                                <th style="text-align:left; padding: 8px;">Prüfung</th>
                                <th style="text-align:left; padding: 8px;">Typ</th>
                                <th style="text-align:left; padding: 8px;">Gewicht</th>
                                <th style="text-align:left; padding: 8px;">Datum</th>
                                <th style="text-align:left; padding: 8px;">Note</th>
                            </tr>
                            {''.join([f'<tr><td style="padding:8px; border-bottom:1px solid #ddd">{df_row["Assignment"]}</td><td style="padding:8px; border-bottom:1px solid #ddd">{next(a["type"] for a in st.session_state.assignments if a["name"] == df_row["Assignment"] and a["subject"] == subject)}</td><td style="padding:8px; border-bottom:1px solid #ddd">{next(a["weight"] for a in st.session_state.assignments if a["name"] == df_row["Assignment"] and a["subject"] == subject):.1f}</td><td style="padding:8px; border-bottom:1px solid #ddd">{df_row["Date"].strftime("%d.%m.%Y")}</td><td style="padding:8px; border-bottom:1px solid #ddd"><strong>{df_row["Grade"]}</strong></td></tr>' for _, df_row in df_student.iterrows()])}
                        </table>
                        <br>
                        <p>Unterschrift Lehrperson: ___________________</p>
                    </div>
                    """
                    st.markdown(report_html, unsafe_allow_html=True)
                    st.caption("Zum Drucken: Rechtsklick auf den Bereich oben -> 'Drucken' oder Screenshot erstellen.")