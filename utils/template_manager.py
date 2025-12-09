import json
import os
import streamlit as st
from .constants import TEMPLATES_FILE, DEFAULT_TEMPLATES
from .data_manager import load_json, save_json

def get_templates():
    """Load templates or return defaults"""
    return load_json(TEMPLATES_FILE, DEFAULT_TEMPLATES)

def save_new_template(name, category, subject_line, body):
    templates = get_templates()
    # Overwrite if exists
    templates = [t for t in templates if t['name'] != name]
    templates.append({
        "name": name,
        "category": category,
        "subject_line": subject_line,
        "body": body
    })
    save_json(TEMPLATES_FILE, templates)

def delete_template(name):
    templates = get_templates()
    templates = [t for t in templates if t['name'] != name]
    save_json(TEMPLATES_FILE, templates)

def render_template(template, student, subject_name, weighted_avg, assignments):
    """Replace variables in template text"""
    
    # 1. Build Grades List string
    grades_list = ""
    for a in assignments:
        grade = a['grades'].get(student['id'])
        if grade:
            grades_list += f"• {a['name']}: {grade}\n"
    
    # 2. Variable Map
    variables = {
        "{firstname}": student['Vorname'],
        "{lastname}": student['Nachname'],
        "{subject}": subject_name,
        "{average}": f"{weighted_avg:.2f}" if weighted_avg else "-",
        "{grades_list}": grades_list,
        "{date}": datetime.now().strftime("%d.%m.%Y")
    }
    
    # 3. Replace
    subject_line = template['subject_line']
    body = template['body']
    
    for key, val in variables.items():
        subject_line = subject_line.replace(key, str(val))
        body = body.replace(key, str(val))
        
    # 4. Conditional Logic (Simple)
    # If average < 4.0, we could append a warning automatically if configured
    # For now, we rely on the specific template selected (e.g., "Warning Template")
    
    return subject_line, body

from datetime import datetime