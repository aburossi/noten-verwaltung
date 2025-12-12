import pytest
from unittest.mock import patch, MagicMock
from utils.grading import calculate_grade

# We create a fake configuration to simulate st.session_state.config
MOCK_CONFIG = {
    'scales': {
        '60% Scale': {'threshold': 0.6, 'label': 'Note 4 mit 60%'},
        '66% Scale': {'threshold': 0.66, 'label': 'Note 4 mit 66%'},
        '50% Scale': {'threshold': 0.5, 'label': 'Note 4 mit 50%'}
    }
}

# The @patch decorator replaces 'streamlit' inside utils.grading with a fake object
@patch('utils.grading.st')
def test_calculate_grade_standard(mock_st):
    # Setup the fake session state
    mock_st.session_state.config = MOCK_CONFIG

    # Test
    result = calculate_grade(60, 100, '60% Scale')
    
    assert result['note'] == 4.0
    assert result['label'] == 'Note 4 mit 60%'

@patch('utils.grading.st')
def test_calculate_grade_max(mock_st):
    mock_st.session_state.config = MOCK_CONFIG
    
    result = calculate_grade(100, 100, '60% Scale')
    assert result['note'] == 6.0

@patch('utils.grading.st')
def test_calculate_grade_zero(mock_st):
    mock_st.session_state.config = MOCK_CONFIG
    
    # This previously failed because of the "if not points" bug
    result = calculate_grade(0, 100, '60% Scale')
    
    # 0 points should be a 1.0 (or whatever your min grade is)
    assert result is not None  # Ensure we actually got a result
    assert result['note'] == 1.0

@patch('utils.grading.st')
def test_calculate_grade_invalid(mock_st):
    mock_st.session_state.config = MOCK_CONFIG
    
    assert calculate_grade(None, 100) is None
    assert calculate_grade(50, 0) is None