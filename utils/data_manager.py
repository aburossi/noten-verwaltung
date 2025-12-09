import json
import os
import shutil
import glob
import zipfile
import streamlit as st
from datetime import datetime
from .constants import (
    DATA_DIR, BACKUP_DIR, CLASSES_DIR, CLASSES_REGISTRY_FILE, 
    GLOBAL_CONFIG_FILE, DEFAULT_CONFIG
)

# --- AUDIT LOGGING ---

def log_audit_event(action, details, class_id=None):
    """Log a change event to the class audit log"""
    if not class_id and 'current_class_id' in st.session_state:
        class_id = st.session_state.current_class_id
    
    if not class_id:
        return

    event = {
        'timestamp': datetime.now().isoformat(),
        'user': 'Teacher', # Placeholder for future auth
        'action': action,
        'details': details
    }

    # Load existing log, append, save
    log_path = os.path.join(CLASSES_DIR, class_id, "audit_log.json")
    current_log = load_json(log_path, [])
    current_log.insert(0, event) # Newest first
    save_json(log_path, current_log)

# --- BACKUP MANAGEMENT ---

def get_available_backups():
    """Return list of available backups with metadata"""
    backups = []
    # List directories in backup folder
    for entry in os.scandir(BACKUP_DIR):
        if entry.is_dir() and entry.name.startswith("backup_"):
            try:
                # Parse timestamp from folder name: backup_type_YYYY-MM-DD_HH-MM-SS
                parts = entry.name.split('_')
                ts_str = f"{parts[-2]}_{parts[-1]}"
                dt = datetime.strptime(ts_str, "%Y-%m-%d_%H-%M-%S")
                
                backups.append({
                    'name': entry.name,
                    'type': parts[1], # auto or manual
                    'date': dt,
                    'path': entry.path,
                    'size_mb': get_dir_size(entry.path)
                })
            except:
                continue
    
    # Sort by date descending
    return sorted(backups, key=lambda x: x['date'], reverse=True)

def create_backup(auto=False, note=""):
    """Create a full system backup"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"backup_{'auto' if auto else 'manual'}_{timestamp}"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        
        # Copy entire data directory
        shutil.copytree(DATA_DIR, backup_path)
        
        # Add metadata note if provided
        if note:
            with open(os.path.join(backup_path, "note.txt"), "w", encoding="utf-8") as f:
                f.write(note)
        
        # Cleanup retention policy (Keep last 30)
        backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "backup_*")))
        if len(backups) > 30:
            for old in backups[:-30]:
                shutil.rmtree(old)
                
        return True, f"Backup erstellt: {timestamp}"
    except Exception as e:
        return False, str(e)

def restore_backup(backup_name):
    """Restore data from a specific backup folder"""
    try:
        source = os.path.join(BACKUP_DIR, backup_name)
        if not os.path.exists(source):
            return False, "Backup existiert nicht mehr"
        
        # Safety: Create a temp backup of current state before restoring
        create_backup(auto=True, note="Pre-restore safety backup")
        
        # Clear current data
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        
        # Restore
        shutil.copytree(source, DATA_DIR)
        
        return True, "System erfolgreich wiederhergestellt"
    except Exception as e:
        return False, str(e)

def create_zip_export():
    """Zip the entire data directory for download"""
    zip_path = os.path.join(BACKUP_DIR, "full_export.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
        
    shutil.make_archive(zip_path.replace('.zip', ''), 'zip', DATA_DIR)
    return zip_path

def import_zip_backup(uploaded_file):
    """Restore system from an uploaded ZIP file"""
    try:
        # Create temp folder
        temp_dir = os.path.join(BACKUP_DIR, "temp_import")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        # Extract zip
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            
        # Verify structure (check for classes.json or global_config.json)
        if not os.path.exists(os.path.join(temp_dir, "classes.json")):
             return False, "Ungültiges Backup-Format (classes.json fehlt)"
        
        # Backup current
        create_backup(auto=True, note="Pre-import safety backup")
        
        # Replace data
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        shutil.copytree(temp_dir, DATA_DIR)
        
        # Cleanup
        shutil.rmtree(temp_dir)
        
        return True, "Import erfolgreich!"
    except Exception as e:
        return False, str(e)

# --- UTILS ---

def get_dir_size(path):
    total = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    return round(total / 1024 / 1024, 2) # MB

# --- EXISTING FUNCTIONS (Keep these as they were) ---

def init_directories():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(CLASSES_DIR, exist_ok=True)
    if os.path.exists(os.path.join(DATA_DIR, "students.json")):
        migrate_legacy_data()

def migrate_legacy_data():
    default_class_id = "class_default"
    class_path = os.path.join(CLASSES_DIR, default_class_id)
    os.makedirs(class_path, exist_ok=True)
    for file in ["students.json", "assignments.json", "email_log.json", "config.json"]:
        src, dst = os.path.join(DATA_DIR, file), os.path.join(class_path, file)
        if os.path.exists(src): shutil.move(src, dst)
    save_json(CLASSES_REGISTRY_FILE, [{"id": default_class_id, "name": "Standardklasse", "created_at": datetime.now().isoformat()}])

def load_json(filepath, default=None):
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f: return json.load(f)
    except: pass
    return default if default is not None else []

def save_json(filepath, data):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except: return False

def get_class_registry(): return load_json(CLASSES_REGISTRY_FILE, [])

def create_new_class(class_name):
    class_id = f"class_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    registry = get_class_registry()
    registry.append({"id": class_id, "name": class_name, "created_at": datetime.now().isoformat()})
    save_json(CLASSES_REGISTRY_FILE, registry)
    os.makedirs(os.path.join(CLASSES_DIR, class_id), exist_ok=True)
    return class_id

def switch_class(class_id):
    st.session_state.current_class_id = class_id
    class_path = os.path.join(CLASSES_DIR, class_id)
    st.session_state.students = load_json(os.path.join(class_path, "students.json"), [])
    st.session_state.assignments = load_json(os.path.join(class_path, "assignments.json"), [])
    st.session_state.email_log = load_json(os.path.join(class_path, "email_log.json"), [])
    st.session_state.audit_log = load_json(os.path.join(class_path, "audit_log.json"), []) # NEW
    
    class_config = load_json(os.path.join(class_path, "config.json"), None)
    st.session_state.config = class_config if class_config else load_json(GLOBAL_CONFIG_FILE, DEFAULT_CONFIG)

def delete_class(class_id):
    registry = [c for c in get_class_registry() if c['id'] != class_id]
    save_json(CLASSES_REGISTRY_FILE, registry)
    class_path = os.path.join(CLASSES_DIR, class_id)
    if os.path.exists(class_path): shutil.rmtree(class_path)

def initialize_session_state():
    registry = get_class_registry()
    if not registry:
        class_id = create_new_class("Meine Klasse")
        st.session_state.current_class_id = class_id
    elif 'current_class_id' not in st.session_state:
        st.session_state.current_class_id = registry[0]['id']
    if 'students' not in st.session_state:
        switch_class(st.session_state.current_class_id)

def save_all_data(create_auto_backup=True):
    # Only create auto-backup occasionally or on critical saves to save space?
    # For now, per user requirement: "Daily timestamped", but triggering on every save 
    # might be too much. Let's do it if no backup exists for today.
    
    # Simple check: do we have a backup from the last hour?
    # (Implementation simplified: just backup every time user explicitly clicks Save)
    if create_auto_backup:
        create_backup(auto=True)

    class_id = st.session_state.current_class_id
    class_path = os.path.join(CLASSES_DIR, class_id)
    
    success = True
    success &= save_json(os.path.join(class_path, "students.json"), st.session_state.students)
    success &= save_json(os.path.join(class_path, "assignments.json"), st.session_state.assignments)
    success &= save_json(os.path.join(class_path, "config.json"), st.session_state.config)
    success &= save_json(os.path.join(class_path, "email_log.json"), st.session_state.email_log)
    
    # NEW: Save Audit Log
    if 'audit_log' in st.session_state:
        success &= save_json(os.path.join(class_path, "audit_log.json"), st.session_state.audit_log)
    
    save_json(GLOBAL_CONFIG_FILE, st.session_state.config)
    return success