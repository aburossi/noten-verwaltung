import streamlit as st
import pandas as pd
import plotly.express as px
from utils.grading import calculate_weighted_average

def render():
    st.title("📊 Übersicht")
    
    if not st.session_state.students:
        st.info("Keine Schüler/innen geladen. Bitte importieren Sie Schülerdaten.")
        return
    
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
            st.metric("Anzahl Schüler/innen", len(st.session_state.students))
            st.metric("Anzahl Prüfungen", num_assignments)
            
            if avg_grades:
                fig = px.histogram(
                    x=avg_grades, nbins=20,
                    title=f"Notenverteilung {subject}",
                    labels={'x': 'Note', 'y': 'Anzahl'}
                )
                fig.update_layout(showlegend=False, height=300)
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