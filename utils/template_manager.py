import json
import os
from datetime import datetime
from .constants import TEMPLATES_FILE, DEFAULT_TEMPLATES
from .data_manager import load_json, save_json

def get_templates():
    return load_json(TEMPLATES_FILE, DEFAULT_TEMPLATES)

def save_new_template(name, category, subject_line, body):
    templates = get_templates()
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

# === UPDATED RENDER FUNCTION ===
def render_template(template, student, subject_name, weighted_avg, assignments, sender_name="Deine Lehrperson"):
    """
    Returns:
        subject_line (str)
        body_text (str): For plain text email clients
        body_html (str): For modern email clients (with table layout)
    """
    
    # 1. Sort assignments by date
    assignments = sorted(assignments, key=lambda x: x['date'])

    # 2. Build Text List (Fallback)
    grades_list_text = ""
    for a in assignments:
        grade = a['grades'].get(student['id'])
        if grade:
            date_str = datetime.fromisoformat(a['date']).strftime("%d.%m.%Y")
            grades_list_text += f"• {a['name']} ({date_str}): {grade}\n"

    # 3. Build HTML Table
    rows_html = ""
    for a in assignments:
        grade = a['grades'].get(student['id'])
        if grade:
            date_str = datetime.fromisoformat(a['date']).strftime("%d.%m.%Y")
            rows_html += f"""
            <tr>
                <td style="padding:8px; border-bottom:1px solid #ddd;">{a['name']}</td>
                <td style="padding:8px; border-bottom:1px solid #ddd;">{date_str}</td>
                <td style="padding:8px; border-bottom:1px solid #ddd;"><strong>{grade}</strong></td>
            </tr>
            """

    grades_table_html = f"""
    <div style="font-family: Arial, sans-serif; color: #333;">
        <div style="padding: 15px; border: 1px solid #ccc; background-color: #fafafa;">
            <h2 style="margin-top: 0;">Notenblatt: {subject_name}</h2>
            <p>
                <strong>Schüler/in:</strong> {student['Vorname']} {student['Nachname']}<br>
                <strong>Datum:</strong> {datetime.now().strftime("%d.%m.%Y")}
            </p>
            <hr style="border: 0; border-top: 1px solid #eee;">
            <h3 style="color: #444;">Gesamtschnitt: {f"{weighted_avg:.2f}" if weighted_avg else "-"}</h3>
            
            <table style="width:100%; border-collapse: collapse; background-color: #fff;">
                <tr style="background-color: #f2f2f2;">
                    <th style="text-align:left; padding: 8px; border-bottom: 2px solid #ddd;">Prüfung</th>
                    <th style="text-align:left; padding: 8px; border-bottom: 2px solid #ddd;">Datum</th>
                    <th style="text-align:left; padding: 8px; border-bottom: 2px solid #ddd;">Note</th>
                </tr>
                {rows_html}
            </table>
        </div>
    </div>
    """

    # 4. Variable Map (Added sender_name)
    variables = {
        "{firstname}": student['Vorname'],
        "{lastname}": student['Nachname'],
        "{subject}": subject_name,
        "{average}": f"{weighted_avg:.2f}" if weighted_avg else "-",
        "{date}": datetime.now().strftime("%d.%m.%Y"),
        "{sender_name}": sender_name  # <--- FIX IS HERE
    }

    subject_line = template['subject_line']
    body_raw = template['body']

    # Replace variables in Subject
    for key, val in variables.items():
        subject_line = subject_line.replace(key, str(val))

    # Replace variables in Body (Text)
    text_body = body_raw
    for key, val in variables.items():
        text_body = text_body.replace(key, str(val))
    text_body = text_body.replace("{grades_list}", grades_list_text)

    # Replace variables in Body (HTML)
    html_body = body_raw.replace('\n', '<br>') 
    for key, val in variables.items():
        html_body = html_body.replace(key, str(val))
    
    html_body = html_body.replace("{grades_list}", grades_table_html)

    full_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            {html_body}
        </body>
    </html>
    """

    return subject_line, text_body, full_html