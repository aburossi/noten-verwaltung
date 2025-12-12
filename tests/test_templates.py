import pytest
from utils.template_manager import render_template

# Mock data
MOCK_STUDENT = {
    "id": "student_1",
    "Vorname": "Hans",
    "Nachname": "Muster",
}

MOCK_ASSIGNMENTS = [
    {
        "name": "Math Test",
        "type": "Test",
        "weight": 1.0,
        "date": "2025-01-01T12:00:00",
        "url": "http://moodle",
        "grades": {"student_1": 5.0}
    },
    {
        "name": "Homework",
        "type": "Task",
        "weight": 0.5,
        "date": "2025-01-02T12:00:00",
        "grades": {"student_1": 4.0}
    }
]

def test_render_variables():
    template = {
        "subject_line": "Hello {firstname}",
        "body": "Dear {firstname} {lastname}, your average in {subject} is {average}."
    }
    
    subject, body_text, body_html = render_template(
        template, 
        MOCK_STUDENT, 
        "MATH", 
        4.5, 
        MOCK_ASSIGNMENTS,
        sender_name="Mr. Teacher"
    )
    
    # Check Subject Line
    assert "Hello Hans" in subject
    
    # Check Body Text
    assert "Dear Hans Muster" in body_text
    assert "MATH" in body_text
    assert "4.50" in body_text

def test_html_generation():
    template = {
        "subject_line": "Grades",
        "body": "Here are your grades: {grades_list}"
    }
    
    _, _, body_html = render_template(
        template, 
        MOCK_STUDENT, 
        "MATH", 
        4.5, 
        MOCK_ASSIGNMENTS
    )
    
    # Check if HTML contains the table structure
    assert "<table" in body_html
    assert "Math Test" in body_html
    assert "<strong>5.0</strong>" in body_html  # The grade should be bold