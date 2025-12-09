import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from utils.grading import calculate_weighted_average

def render():
    st.title("📊 Übersicht")
    
    if not st.session_state.students:
        st.info("Keine Schüler/innen geladen. Bitte importieren Sie Schülerdaten.")
        return
    
    # ==========================================
    # BONUS: WEEKLY WORKFLOW SUMMARY
    # ==========================================
    with st.container(border=True):
        st.subheader("📅 Diese Woche")
        
        # Calculate Stats
        now = datetime.now()
        start_of_week = now - timedelta(days=now.weekday())
        
        # 1. Graded this week
        graded_count = 0
        for a in st.session_state.assignments:
            try:
                a_date = datetime.fromisoformat(a['date'])
                if a_date >= start_of_week:
                    graded_count += 1
            except: pass
            
        # 2. At Risk
        at_risk_count = 0
        for s in st.session_state.students:
            # Check all subjects
            is_risk = False
            for subj in st.session_state.config['subjects']:
                avg = calculate_weighted_average(s['id'], subj)
                if avg and avg < 4.0:
                    is_risk = True
            if is_risk: at_risk_count += 1
            
        # 3. Pending Emails (Simple logic: Risk students + New Grades logic approx)
        # Just hardcode a "Need Action" logic for students < 4.0
        
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