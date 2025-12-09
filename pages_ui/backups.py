import streamlit as st
import pandas as pd
from datetime import datetime
import os
from utils.data_manager import (
    get_available_backups, create_backup, restore_backup, 
    create_zip_export, import_zip_backup, save_all_data
)

def render():
    st.title("💾 System & Backup")
    
    tab_overview, tab_restore, tab_audit = st.tabs(["📦 Backups", "♻️ Wiederherstellen", "📝 Audit Log"])
    
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

    # === TAB 3: AUDIT LOG ===
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