import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
from utils.email_manager import get_students_with_changes

# Helper timestamps
NOW = datetime.now().isoformat()
YESTERDAY = (datetime.now() - timedelta(days=1)).isoformat()
TWO_DAYS_AGO = (datetime.now() - timedelta(days=2)).isoformat()

@patch('utils.email_manager.st')
@patch('utils.email_manager.get_last_email_status') # <--- Mock this function
def test_smart_email_detection(mock_get_status, mock_st):
    
    # 1. Setup Data
    mock_st.session_state.students = [
        {"id": "student_A", "Vorname": "Alice"},
        {"id": "student_B", "Vorname": "Bob"}
    ]
    
    mock_st.session_state.assignments = [
        # New assignment for Alice (Date > Last Email)
        {
            "subject": "MATH",
            "date": NOW, 
            "grades": {"student_A": 5.0} 
        },
        # Old assignment for Bob (Date < Last Email)
        {
            "subject": "MATH",
            "date": TWO_DAYS_AGO, 
            "grades": {"student_B": 4.0} 
        }
    ]
    
    # 2. Define how the mocked status function behaves
    def side_effect(student_id, subject):
        # We simulate that both students got an email YESTERDAY
        return {"timestamp": YESTERDAY, "status": "sent"}
    
    mock_get_status.side_effect = side_effect
    
    # 3. Run Logic
    changed_students = get_students_with_changes("MATH")
    
    # 4. Assertions
    changed_ids = [s['id'] for s in changed_students]
    
    assert "student_A" in changed_ids  # Should be detected (New Data)
    assert "student_B" not in changed_ids # Should be ignored (Old Data)