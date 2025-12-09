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
    if not os.path.exists(BACKUP_DIR):
        return []
        
    for entry in os.scandir(BACKUP_DIR):
        if entry.is_dir() and entry.name.startswith("backup_"):
            try:
                parts = entry.name.split('_')
                ts_str = f"{parts[-2]}_{parts[-1]}"
                dt = datetime.strptime(ts_str, "%Y-%m-%d_%H-%M-%S")
                
                backups.append({
                    'name': entry.name,
                    'type': parts[1], 
                    'date': dt,
                    'path': entry.path,
                    'size_mb': get_dir_size(entry.path)
                })
            except:
                continue
    
    return sorted(backups, key=lambda x: x['date'], reverse=True)

def create_backup(auto=False, note=""):
    """Create a full system backup"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"backup_{'auto' if auto else 'manual'}_{timestamp}"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        
        if os.path.exists(DATA_DIR):
            shutil.copytree(DATA_DIR, backup_path)
        
        if note:
            with open(os.path.join(backup_path, "note.txt"), "w", encoding="utf-8") as f:
                f.write(note)
        
        # Cleanup retention (Keep last 30)
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
        
        create_backup(auto=True, note="Pre-restore safety backup")
        
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        
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
    try:
        temp_dir = os.path.join(BACKUP_DIR, "temp_import")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            
        if not os.path.exists(os.path.join(temp_dir, "classes.json")):
             return False, "Ungültiges Backup-Format (classes.json fehlt)"
        
        create_backup(auto=True, note="Pre-import safety backup")
        
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        shutil.copytree(temp_dir, DATA_DIR)
        
        shutil.rmtree(temp_dir)
        return True, "Import erfolgreich!"
    except Exception as e:
        return False, str(e)

def get_dir_size(path):
    total = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += get_dir_size(entry.path)
    except: pass
    return round(total / 1024 / 1024, 2)

# --- CORE DATA FUNCTIONS ---

def init_directories():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(CLASSES_DIR, exist_ok=True)

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

def get_class_registry():
    registry = load_json(CLASSES_REGISTRY_FILE, [])
    # Optional: Filter for demo mode if env var is set
    if os.environ.get("DEMO_MODE") == "TRUE":
        return [c for c in registry if c['id'] == "class_demo_2025"]
    return registry

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
    
    if os.path.exists(class_path):
        st.session_state.students = load_json(os.path.join(class_path, "students.json"), [])
        st.session_state.assignments = load_json(os.path.join(class_path, "assignments.json"), [])
        st.session_state.email_log = load_json(os.path.join(class_path, "email_log.json"), [])
        st.session_state.audit_log = load_json(os.path.join(class_path, "audit_log.json"), [])
        
        class_config = load_json(os.path.join(class_path, "config.json"), None)
        st.session_state.config = class_config if class_config else load_json(GLOBAL_CONFIG_FILE, DEFAULT_CONFIG)
    else:
        # Fallback if folder deleted but id in session
        st.session_state.students = []
        st.session_state.assignments = []
        st.session_state.config = load_json(GLOBAL_CONFIG_FILE, DEFAULT_CONFIG)

def delete_class(class_id):
    """
    Deletes a class from the registry and removes its data folder.
    """
    # 1. Update Registry
    registry = [c for c in get_class_registry() if c['id'] != class_id]
    save_json(CLASSES_REGISTRY_FILE, registry)
    
    # 2. Delete Folder
    class_path = os.path.join(CLASSES_DIR, class_id)
    if os.path.exists(class_path):
        try:
            shutil.rmtree(class_path)
        except Exception as e:
            print(f"Error deleting folder {class_path}: {e}")

def initialize_session_state():
    registry = get_class_registry()
    
    # If no classes exist, create default or handle empty state
    if not registry and 'current_class_id' not in st.session_state:
        # Optionally create a default class if completely empty
        pass
    
    if 'current_class_id' not in st.session_state and registry:
        st.session_state.current_class_id = registry[0]['id']
        
    if 'current_class_id' in st.session_state and st.session_state.current_class_id:
        if 'students' not in st.session_state:
            switch_class(st.session_state.current_class_id)
    else:
        # Empty state initialization
        st.session_state.students = []
        st.session_state.assignments = []
        st.session_state.config = load_json(GLOBAL_CONFIG_FILE, DEFAULT_CONFIG)

def save_all_data(create_auto_backup=True):
    if create_auto_backup:
        create_backup(auto=True)

    class_id = st.session_state.get('current_class_id')
    if not class_id: return False
    
    class_path = os.path.join(CLASSES_DIR, class_id)
    os.makedirs(class_path, exist_ok=True)
    
    success = True
    success &= save_json(os.path.join(class_path, "students.json"), st.session_state.students)
    success &= save_json(os.path.join(class_path, "assignments.json"), st.session_state.assignments)
    success &= save_json(os.path.join(class_path, "config.json"), st.session_state.config)
    success &= save_json(os.path.join(class_path, "email_log.json"), st.session_state.email_log)
    if 'audit_log' in st.session_state:
        success &= save_json(os.path.join(class_path, "audit_log.json"), st.session_state.audit_log)
    
    save_json(GLOBAL_CONFIG_FILE, st.session_state.config)
    return success