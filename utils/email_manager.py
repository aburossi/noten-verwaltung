import streamlit as st
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from .data_manager import save_json
from .constants import CLASSES_DIR
from .grading import calculate_weighted_average

def log_email_event(student_id, student_name, subject, status, error_msg=""):
    """Log an email event to the session state and save to class specific file"""
    event = {
        'timestamp': datetime.now().isoformat(),
        'student_id': student_id,
        'student_name': student_name,
        'subject': subject,
        'status': status,
        'error': error_msg
    }
    
    # Update Session State
    st.session_state.email_log.insert(0, event)
    
    # Save to the specific class folder
    # We construct the path dynamically using the current class ID
    if 'current_class_id' in st.session_state:
        class_id = st.session_state.current_class_id
        log_file_path = os.path.join(CLASSES_DIR, class_id, "email_log.json")
        save_json(log_file_path, st.session_state.email_log)

def get_last_email_status(student_id, subject):
    """Get the last email status for a student/subject combo"""
    # Ensure email_log exists in session state
    if 'email_log' not in st.session_state:
        return None
        
    for log in st.session_state.email_log:
        if log['student_id'] == student_id and log['subject'] == subject:
            return log
    return None

def generate_email_content(student, subject, include_average=True):
    """Generate email content for a student"""
    student_assignments = [
        a for a in st.session_state.assignments 
        if a['subject'] == subject and student['id'] in a.get('grades', {})
    ]
    
    weighted_avg = calculate_weighted_average(student['id'], subject)
    
    # Build email body
    body = f"Hallo {student['Vorname']},\n\n"
    body += f"Hier ist eine Übersicht deiner Noten im Fach {subject}:\n\n"
    
    for assignment in student_assignments:
        grade = assignment['grades'].get(student['id'])
        if grade:
            body += f"• {assignment['name']} ({assignment['type']}, Gewicht: {assignment['weight']}): Note {grade}\n"
    
    if include_average and weighted_avg:
        body += f"\n📊 Gewichteter Durchschnitt: {weighted_avg}\n"
    
    body += "\nLiebe Grüsse,\nPietro Rossi"
    
    return {
        'to': f"{student['Anmeldename']}@lernende.bbw.ch",
        'subject': f"Notenbericht {subject}",
        'body': body
    }

def send_email(recipient, subject_line, body, sender_email, sender_password):
    """Send email via SMTP"""
    try:
        config = st.session_state.config['email']
        
        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = subject_line
        
        # Plain text version
        text_part = MIMEText(body, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # HTML version
        html_body = body.replace('\n', '<br>')
        html_part = MIMEText(f'<html><body style="font-family: Arial, sans-serif;">{html_body}</body></html>', 'html', 'utf-8')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port']) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)