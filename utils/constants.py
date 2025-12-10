import os

# Base directories
DATA_DIR = "data"
BACKUP_DIR = "backups"
CLASSES_DIR = os.path.join(DATA_DIR, "classes")

# Global Config
GLOBAL_CONFIG_FILE = os.path.join(DATA_DIR, "global_config.json")
CLASSES_REGISTRY_FILE = os.path.join(DATA_DIR, "classes.json")
TEMPLATES_FILE = os.path.join(DATA_DIR, "templates.json")

# Default Configuration
DEFAULT_CONFIG = {
    'subjects': ['GESELLSCHAFT', 'SPRACHE'],
    'scales': {
        '60% Scale': {'threshold': 0.6, 'label': 'Note 4 mit 60%'},
        '66% Scale': {'threshold': 0.66, 'label': 'Note 4 mit 66%'},
        '50% Scale': {'threshold': 0.5, 'label': 'Note 4 mit 50%'}
    },
    'weightDefaults': {
        'Test': 2.0,
        'Lernpfad': 1.0,
        'Custom Assignment': 0.5
    },
    'email': {
        'smtp_server': 'mail.bbw.ch',
        'smtp_port': 465,
        'sender_email': ''  # <--- HIER: Leer gelassen für Datenschutz
    }
}

# Default Templates
DEFAULT_TEMPLATES = [
    {
        "name": "Standard Notenbericht",
        "category": "Bericht",
        "subject_line": "Notenbericht {subject}",
        "body": "Hallo {firstname},\n\nHier ist Ihre aktuelle Übersicht für {subject}.\n\n{grades_list}\n\nIhr Schnitt: {average}\n\nLieber Gruss\n{sender_name}" # Optional: Variable für Absender
    },
    {
        "name": "Warnung (Ungenügend)",
        "category": "Intervention",
        "subject_line": "WICHTIG: Notenstand {subject}",
        "body": "Hallo {firstname},\n\nLeider ist Ihr aktueller Schnitt in {subject} ungenügend ({average}).\n\nBitte melden Sie sich bei mir für einen Termin.\n\nLieber Gruss\n{sender_name}"
    }
]