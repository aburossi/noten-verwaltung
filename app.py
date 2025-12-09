import streamlit as st
import os
import glob
import json
from utils.data_manager import (
    initialize_session_state, save_all_data, 
    create_backup, init_directories,
    get_class_registry, create_new_class, switch_class, delete_class,
    CLASSES_DIR
)
from utils.constants import BACKUP_DIR
import pages_ui.overview as p_overview
import pages_ui.subjects as p_subjects
import pages_ui.analytics as p_analytics
import pages_ui.emails as p_emails
import pages_ui.backups as p_backups
import pages_ui.data_io as p_data_io

# ==========================================
# NEW: LANDING PAGE (CLASS DASHBOARD)
# ==========================================
def render_class_dashboard():
    st.title("🏫 Meine Klassen")
    st.markdown("Wähle eine Klasse aus, um die Noten zu verwalten.")

    registry = get_class_registry()
    
    # Grid Layout for Classes
    cols = st.columns(3)
    
    for idx, cls in enumerate(registry):
        with cols[idx % 3]:
            # Card Container
            with st.container(border=True):
                st.subheader(f"🎓 {cls['name']}")
                
                # Get quick stats without loading full state if possible, 
                # or just use what is in state if it matches
                student_count = "n/a"
                try:
                    s_path = os.path.join(CLASSES_DIR, cls['id'], "students.json")
                    if os.path.exists(s_path):
                        with open(s_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            student_count = len(data)
                except:
                    student_count = "?"

                st.caption(f"Schüler: {student_count}")
                st.caption(f"ID: {cls['id']}")
                
                # The "Open" Button
                # We use a callback to switch class BEFORE the rerun
                if st.button(f"Öffnen", key=f"open_{cls['id']}", use_container_width=True):
                    switch_class(cls['id'])
                    # Set the navigation to Overview so we don't stay on the dashboard
                    st.session_state.current_page = "📊 Übersicht"
                    st.rerun()

    # Add New Class Button (Clean UI)
    with cols[(len(registry)) % 3]:
        with st.container(border=True):
            st.markdown("#### ➕ Neue Klasse")
            st.write("") # Spacer
            new_name = st.text_input("Klassenname", key="new_class_dash", placeholder="z.B. 4PK26a")
            if st.button("Erstellen", key="btn_create_dash", use_container_width=True):
                if new_name:
                    new_id = create_new_class(new_name)
                    switch_class(new_id)
                    st.session_state.current_page = "📊 Übersicht"
                    st.rerun()

# ==========================================
# MAIN APP
# ==========================================

def main():
    st.set_page_config(
        page_title="BBW Notenverwaltung",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize system & Migration
    init_directories()
    initialize_session_state()
    
    # Initialize Navigation State if not present
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Alle Klassen"

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("📚 BBW Manager")
        
        # Display Current Class Name prominently
        registry = get_class_registry()
        current_class = next((c for c in registry if c['id'] == st.session_state.current_class_id), None)
        if current_class:
            st.markdown(f"### 🎓 {current_class['name']}")
        
        st.write("---")
        
        # NAVIGATION MENU
        # We handle navigation manually to allow programmatic switching
        options = [
            "🏠 Alle Klassen",
            "📊 Übersicht",
            "📈 Analyse", 
            "📝 GESELLSCHAFT", 
            "📝 SPRACHE", 
            "✉️ Smart Emails", 
            "💾 Backup & Log", 
            "📁 Import/Export"
        ]
        
        # If the state is not in options (e.g. after a reload), default to Home
        if st.session_state.current_page not in options:
            st.session_state.current_page = "🏠 Alle Klassen"

        selected_page = st.radio(
            "Navigation",
            options,
            index=options.index(st.session_state.current_page),
            label_visibility="collapsed"
        )
        
        # Update state if user clicked something new
        if selected_page != st.session_state.current_page:
            st.session_state.current_page = selected_page
            st.rerun()

        st.write("---")
        st.subheader("System")
        
        if st.button("💾 Speichern", use_container_width=True):
            if save_all_data(create_auto_backup=True):
                st.success("✅ Gespeichert!")
            else:
                st.error("❌ Fehler")
        
        if st.button("📦 Backup", use_container_width=True):
            success, msg = create_backup(auto=False)
            if success: st.info(msg)
            else: st.error(msg)
            
    # --- PAGE ROUTING ---
    
    # 1. Landing Page (Dashboard)
    if st.session_state.current_page == "🏠 Alle Klassen":
        render_class_dashboard()
        
    # 2. Standard Pages (require a loaded class)
    else:
        # Ensure a class is actually loaded (safety check)
        if not st.session_state.students and not st.session_state.assignments:
             # If empty, it might just be a fresh class, which is fine.
             pass

        if st.session_state.current_page == "📊 Übersicht":
            p_overview.render()
        elif st.session_state.current_page == "📈 Analyse":
            p_analytics.render()
        elif st.session_state.current_page == "📝 GESELLSCHAFT":
            p_subjects.render("GESELLSCHAFT")
        elif st.session_state.current_page == "📝 SPRACHE":
            p_subjects.render("SPRACHE")
        elif st.session_state.current_page == "✉️ Smart Emails":
            p_emails.render()
        elif st.session_state.current_page == "💾 Backup & Log":
            p_backups.render()
        elif st.session_state.current_page == "📁 Import/Export":
            p_data_io.render()

if __name__ == "__main__":
    main()