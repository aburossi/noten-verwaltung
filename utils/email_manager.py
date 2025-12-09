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
    event = {
        'timestamp': datetime.now().isoformat(),
        'student_id': student_id,
        'student_name': student_name,
        'subject': subject,
        'status': status,
        'error': error_msg
    }
    st.session_state.email_log.insert(0, event)
    if 'current_class_id' in st.session_state:
        class_id = st.session_state.current_class_id
        log_file_path = os.path.join(CLASSES_DIR, class_id, "email_log.json")
        save_json(log_file_path, st.session_state.email_log)

def get_last_email_status(student_id, subject):
    if 'email_log' not in st.session_state:
        return None
    for log in st.session_state.email_log:
        if log['student_id'] == student_id and log['subject'] == subject:
            return log
    return None

def get_students_with_changes(subject):
    """
    Identify students who have assignments with a modification date NEWER 
    than their last sent email.
    """
    changed_students = []
    
    # Filter assignments by subject
    subj_assignments = [a for a in st.session_state.assignments if a['subject'] == subject]
    
    for student in st.session_state.students:
        last_email_log = get_last_email_status(student['id'], subject)
        
        # If never emailed, but has grades -> Needs email
        has_grades = any(student['id'] in a['grades'] for a in subj_assignments)
        if not last_email_log:
            if has_grades: changed_students.append(student)
            continue
            
        last_email_date = datetime.fromisoformat(last_email_log['timestamp'])
        
        # Check if any assignment has a grade that is logically 'newer'
        # Since we don't track timestamp per grade, we check assignment date 
        # (Assuming assignment date ~ grading date for new assignments)
        # For updates to old assignments, this is a limitation, but sufficient for "New Weekly Assignments"
        
        has_new_data = False
        for a in subj_assignments:
            if student['id'] in a['grades']:
                try:
                    assign_date = datetime.fromisoformat(a['date'])
                    if assign_date > last_email_date:
                        has_new_data = True
                        break
                except: pass
        
        if has_new_data:
            changed_students.append(student)
            
    return changed_students

def send_email(recipient, subject_line, text_body, sender_email, sender_password, html_body=None):
    try:
        config = st.session_state.config['email']
        
        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = subject_line
        
        text_part = MIMEText(text_body, 'plain', 'utf-8')
        msg.attach(text_part)
        
        if html_body:
            final_html = html_body
        else:
            clean_body = text_body.replace('\n', '<br>')
            final_html = f'<html><body style="font-family: Arial, sans-serif;">{clean_body}</body></html>'

        html_part = MIMEText(final_html, 'html', 'utf-8')
        msg.attach(html_part)
        
        with smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port']) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)