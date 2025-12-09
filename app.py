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
import pages_ui.quick_entry as p_quick_entry # NEW IMPORT

# ==========================================
# NEW: LANDING PAGE (CLASS DASHBOARD)
# ==========================================
def render_class_dashboard():
    st.title("🏫 Meine Klassen")
    st.markdown("Verwalten Sie Ihre Klassen oder erstellen Sie eine neue.")

    registry = get_class_registry()
    
    # Grid Layout for Classes
    cols = st.columns(3)
    
    for idx, cls in enumerate(registry):
        with cols[idx % 3]:
            # Card Container
            with st.container(border=True):
                col_header, col_opts = st.columns([5, 1])
                with col_header:
                    st.subheader(f"🎓 {cls['name']}")
                
                # DELETE BUTTON (Popover for safety)
                with col_opts:
                    with st.popover("🗑️", help="Klasse löschen"):
                        st.markdown(f"**{cls['name']}** wirklich löschen?")
                        st.warning("Dies kann nicht rückgängig gemacht werden!")
                        
                        if st.button("Ja, löschen", key=f"del_confirm_{cls['id']}", type="primary"):
                            delete_class(cls['id'])
                            if st.session_state.get('current_class_id') == cls['id']:
                                st.session_state.current_class_id = None
                                new_reg = get_class_registry()
                                if new_reg:
                                    st.session_state.current_class_id = new_reg[0]['id']
                                    switch_class(new_reg[0]['id'])
                            st.rerun()

                # Get quick stats
                student_count = "n/a"
                try:
                    s_path = os.path.join(CLASSES_DIR, cls['id'], "students.json")
                    if os.path.exists(s_path):
                        with open(s_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            student_count = len(data)
                except:
                    student_count = "?"

                st.caption(f"Schüler: {student_count} | ID: {cls['id'][-4:]}")
                
                # The "Open" Button
                if st.button(f"Öffnen", key=f"open_{cls['id']}", use_container_width=True):
                    switch_class(cls['id'])
                    st.session_state.current_page = "📊 Übersicht"
                    st.rerun()

    # Add New Class Button
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
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Alle Klassen"

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("📚 BBW Manager")
        
        registry = get_class_registry()
        current_class = next((c for c in registry if c['id'] == st.session_state.get('current_class_id')), None)
        
        if current_class:
            st.markdown(f"### 🎓 {current_class['name']}")
        else:
            st.markdown("### 🏠 Dashboard")
        
        st.write("---")
        
        # NAVIGATION MENU
        options = [
            "🏠 Alle Klassen",
            "📊 Übersicht",
            "📝 Schnelleingabe", # NEW
            "📈 Analyse", 
            "📝 GESELLSCHAFT", 
            "📝 SPRACHE", 
            "✉️ Smart Emails", 
            "💾 Backup & Log", 
            "📁 Import/Export"
        ]
        
        if not current_class and st.session_state.current_page != "🏠 Alle Klassen":
            st.session_state.current_page = "🏠 Alle Klassen"

        if st.session_state.current_page not in options:
            st.session_state.current_page = "🏠 Alle Klassen"

        if not current_class:
            st.info("Bitte wählen Sie eine Klasse aus.")
            if st.button("Zum Dashboard"):
                st.session_state.current_page = "🏠 Alle Klassen"
                st.rerun()
        else:
            selected_page = st.radio(
                "Navigation",
                options,
                index=options.index(st.session_state.current_page),
                label_visibility="collapsed"
            )
            
            if selected_page != st.session_state.current_page:
                st.session_state.current_page = selected_page
                st.rerun()

        st.write("---")
        st.subheader("System")
        
        if current_class:
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
    if st.session_state.current_page == "🏠 Alle Klassen":
        render_class_dashboard()
        
    elif current_class:
        if st.session_state.current_page == "📊 Übersicht":
            p_overview.render()
        elif st.session_state.current_page == "📝 Schnelleingabe": # NEW ROUTE
            p_quick_entry.render()
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