import os
import json
import random
import shutil
from datetime import datetime, timedelta

# CONFIG
DATA_DIR = "data"
CLASSES_DIR = os.path.join(DATA_DIR, "classes")
REGISTRY_FILE = os.path.join(DATA_DIR, "classes.json")

CLASS_NAME = "Demo Class 2025"
CLASS_ID = "class_demo_2025"

# NAMES DATABASE
FIRST_NAMES = ["Emma", "Liam", "Noah", "Olivia", "William", "Ava", "James", "Isabella", "Oliver", "Sophia", "Benjamin", "Mia", "Lucas", "Charlotte", "Henry", "Amelia", "Alexander", "Harper", "Michael", "Evelyn"]
LAST_NAMES = ["Smith", "Johnson", "Brown", "Taylor", "Miller", "Davis", "Garcia", "Rodriguez", "Wilson", "Martinez", "Anderson", "Thomas", "Hernandez", "Moore", "Martin", "Jackson", "Thompson", "White", "Lopez", "Lee"]

def ensure_dirs():
    if os.path.exists(os.path.join(CLASSES_DIR, CLASS_ID)):
        shutil.rmtree(os.path.join(CLASSES_DIR, CLASS_ID))
    os.makedirs(os.path.join(CLASSES_DIR, CLASS_ID), exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

def generate_students(count=15):
    students = []
    used_names = set()
    
    for _ in range(count):
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        
        # Ensure unique
        while f"{fn} {ln}" in used_names:
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
        used_names.add(f"{fn} {ln}")
        
        username = f"{fn.lower()}.{ln.lower()}"
        students.append({
            "id": f"student_{username}",
            "Anmeldename": username,
            "Vorname": fn,
            "Nachname": ln
        })
    return students

def generate_assignments(students):
    assignments = []
    subjects = ["GESELLSCHAFT", "SPRACHE"]
    
    # Create 3-4 assignments per subject
    configs = [
        ("GESELLSCHAFT", "Test 1: Grundlagen", "Test", 2.0, 30),
        ("GESELLSCHAFT", "Vortrag: Wirtschaft", "Lernpfad", 1.0, 60),
        ("GESELLSCHAFT", "Test 2: Politik", "Test", 2.0, 15),
        ("SPRACHE", "Grammatik Test", "Test", 2.0, 45),
        ("SPRACHE", "Essay: Literatur", "Custom Assignment", 1.0, 20),
    ]

    for subj, name, type_, weight, days_ago in configs:
        max_points = 100 if "Vortrag" not in name else 20
        scale = "60% Scale"
        
        assignment = {
            "id": f"assign_{random.randint(1000, 9999)}",
            "name": name,
            "subject": subj,
            "type": type_,
            "weight": weight,
            "maxPoints": max_points,
            "scaleType": scale,
            "date": (datetime.now() - timedelta(days=days_ago)).isoformat(),
            "grades": {}
        }

        # Generate grades with a distribution
        # Some good students, some struggling
        for student in students:
            # Random "skill" factor for student
            skill = random.uniform(0.4, 0.95) 
            
            # Points based on skill + randomness
            points = max_points * skill * random.uniform(0.8, 1.1)
            points = min(max_points, round(points * 2) / 2) # Round to 0.5
            
            # Calculate grade (Simple 60% logic for demo)
            pct = points / max_points
            note = (pct * 5) + 1
            note = max(1.0, min(6.0, round(note, 1)))
            
            # 10% chance of missing grade
            if random.random() > 0.1:
                assignment["grades"][student["id"]] = note
        
        assignments.append(assignment)
    
    return assignments

def generate_logs(students, assignments):
    email_log = []
    audit_log = []
    
    # Fake Email Logs
    for s in students[:5]: # First 5 students got emails
        email_log.append({
            "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
            "student_id": s["id"],
            "student_name": f"{s['Vorname']} {s['Nachname']}",
            "subject": "GESELLSCHAFT",
            "status": "sent",
            "error": ""
        })
        
    # Fake Audit Logs
    audit_log.append({
        "timestamp": datetime.now().isoformat(),
        "user": "System",
        "action": "Demo Data Generation",
        "details": "Created demo environment"
    })
    
    return email_log, audit_log

def main():
    print("🚀 Generating Demo Data...")
    ensure_dirs()
    
    # 1. Update Registry
    registry = []
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, 'r') as f:
            registry = json.load(f)
    
    # Remove old demo if exists
    registry = [c for c in registry if c['id'] != CLASS_ID]
    registry.append({
        "id": CLASS_ID,
        "name": CLASS_NAME,
        "created_at": datetime.now().isoformat()
    })
    
    with open(REGISTRY_FILE, 'w') as f:
        json.dump(registry, f, indent=2)

    # 2. Generate Content
    students = generate_students(18)
    assignments = generate_assignments(students)
    email_log, audit_log = generate_logs(students, assignments)
    
    # 3. Save Files
    base = os.path.join(CLASSES_DIR, CLASS_ID)
    
    with open(os.path.join(base, "students.json"), 'w', encoding='utf-8') as f:
        json.dump(students, f, indent=2, ensure_ascii=False)
        
    with open(os.path.join(base, "assignments.json"), 'w', encoding='utf-8') as f:
        json.dump(assignments, f, indent=2, ensure_ascii=False)
        
    with open(os.path.join(base, "email_log.json"), 'w', encoding='utf-8') as f:
        json.dump(email_log, f, indent=2, ensure_ascii=False)

    with open(os.path.join(base, "audit_log.json"), 'w', encoding='utf-8') as f:
        json.dump(audit_log, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Successfully created '{CLASS_NAME}' with {len(students)} students and {len(assignments)} assignments.")
    print("👉 Run 'streamlit run app.py' to see the data.")

if __name__ == "__main__":
    main()