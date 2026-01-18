import streamlit as st
import pandas as pd
from datetime import datetime
import os
from utils.data_manager import (
    get_available_backups, create_backup, restore_backup, 
    create_zip_export, import_zip_backup, save_all_data,
    rename_class, create_new_class, switch_class, get_class_registry
)

def render():
    st.title("💾 System & Backup")
    
    tab_overview, tab_restore, tab_sem, tab_audit = st.tabs(["📦 Backups", "♻️ Wiederherstellen", "🎓 Semesterwechsel", "📝 Audit Log"])
    
    # === TAB 1: BACKUPS & EXPORT ===
    with tab_overview:
        st.subheader("Manuelles Backup")
        col1, col2 = st.columns(2)
        with col1:
            note = st.text_input("Notiz für Backup (optional)")
            if st.button("Jetzt Backup erstellen"):
                success, msg = create_backup(auto=False, note=note)
                if success: st.success(msg)
                else: st.error(msg)
                st.rerun()
        
        with col2:
            st.info("Dies erstellt einen lokalen Snapshot aller Klassen und Einstellungen.")

        st.write("---")
        st.subheader("Export & Import")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Alles herunterladen (.zip)"):
                zip_path = create_zip_export()
                with open(zip_path, "rb") as f:
                    st.download_button(
                        "ZIP Datei speichern",
                        f,
                        file_name=f"bbw_full_backup_{datetime.now().strftime('%Y%m%d')}.zip",
                        mime="application/zip"
                    )
        
        with col2:
            uploaded_zip = st.file_uploader("Backup wiederherstellen (.zip)", type="zip")
            if uploaded_zip:
                if st.button("🚨 System aus ZIP überschreiben", type="primary"):
                    success, msg = import_zip_backup(uploaded_zip)
                    if success:
                        st.success(msg)
                        st.session_state.clear()
                        st.rerun()
                    else:
                        st.error(msg)

    # === TAB 2: RESTORE ===
    with tab_restore:
        st.subheader("Verfügbare Snapshots")
        st.warning("⚠️ Achtung: Wiederherstellen überschreibt alle aktuellen Daten mit dem Stand des Backups.")
        
        backups = get_available_backups()
        
        if not backups:
            st.info("Keine Backups gefunden.")
        else:
            for backup in backups:
                with st.expander(f"{backup['date'].strftime('%d.%m.%Y %H:%M')} ({backup['type']}) - {backup['size_mb']} MB"):
                    # Check for note
                    note_path = os.path.join(backup['path'], "note.txt")
                    if os.path.exists(note_path):
                        with open(note_path, 'r') as f:
                            st.caption(f"📝 Notiz: {f.read()}")
                    
                    if st.button(f"♻️ Wiederherstellen auf Stand {backup['date'].strftime('%H:%M')}", key=backup['name']):
                        success, msg = restore_backup(backup['name'])
                        if success:
                            st.success(msg)
                            st.session_state.clear() # Clear state to force reload
                            st.rerun()
                        else:
                            st.error(msg)

                            st.rerun()
                        else:
                            st.error(msg)
                            
    # === TAB 3: SEMESTER START ===
    with tab_sem:
        st.subheader("🎓 Neues Semester starten")
        st.info("Hier können Sie das aktuelle Semester archivieren und sauber in ein neues starten.")
        
        current_class_id = st.session_state.get('current_class_id')
        registry = get_class_registry()
        current_cls = next((c for c in registry if c['id'] == current_class_id), None)
        
        if not current_cls:
            st.error("Keine aktive Klasse ausgewählt.")
        else:
            with st.container(border=True):
                st.markdown("### 1. Aktuelles Semester archivieren")
                archive_name = st.text_input(
                    "Name für das Archiv", 
                    value=f"{current_cls['name']} (Archiv)",
                    help="Wie soll die aktuelle Klasse im Archiv heissen?"
                )
                
                st.markdown("### 2. Neues Semester erstellen")
                new_sem_name = st.text_input(
                    "Name der neuen Klasse", 
                    placeholder="z.B. BMS 25/26 - Semester 2",
                    help="Name der neuen Klasse, die erstellt wird."
                )
                
                st.write("")
                st.warning("⚠️ Dieser Vorgang erstellt ein Backup, benennt die aktuelle Klasse um und erstellt eine neue, leere Klasse.")
                
                if st.button("🚀 Semester abschliessen & Neu starten", type="primary"):
                    if not archive_name or not new_sem_name:
                        st.error("Bitte beide Namen angeben.")
                    else:
                        # 1. Create Safety Backup
                        b_succ, b_msg = create_backup(auto=True, note=f"Semesterwechsel: {current_cls['name']} -> {new_sem_name}")
                        if not b_succ:
                            st.error(f"Backup fehlgeschlagen: {b_msg}. Abbruch.")
                        else:
                            try:
                                # 2. Rename Old Class
                                rename_class(current_class_id, archive_name)
                                
                                # 3. Create New Class
                                new_id = create_new_class(new_sem_name)
                                
                                # 4. Switch to New Class
                                switch_class(new_id)
                                
                                st.success(f"✅ Semesterwechsel erfolgreich! Willkommen in {new_sem_name}.")
                                st.balloons()
                                
                                # 5. Set Page to Dashboard
                                st.session_state.current_page = "📊 Übersicht"
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler beim Semesterwechsel: {e}")

    # === TAB 4: AUDIT LOG ===
    with tab_audit:
        st.subheader("📝 Änderungsprotokoll")
        if 'audit_log' not in st.session_state or not st.session_state.audit_log:
            st.info("Keine Änderungen protokolliert.")
        else:
            # Convert to DataFrame
            df = pd.DataFrame(st.session_state.audit_log)
            
            # Format Timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%d.%m.%Y %H:%M')
            
            # Filter
            search = st.text_input("Suche im Protokoll")
            if search:
                df = df[df['details'].str.contains(search, case=False) | df['action'].str.contains(search, case=False)]
            
            st.dataframe(
                df[['timestamp', 'action', 'details', 'user']], 
                column_config={
                    "timestamp": "Zeit",
                    "action": "Aktion",
                    "details": "Details",
                    "user": "Benutzer"
                },
                use_container_width=True,
                hide_index=True
            )