import pytest
import os
from unittest.mock import patch, MagicMock, ANY
from utils.data_manager import load_json, save_all_data

# 1. Test Loading JSON (File I/O)
def test_load_json_valid(tmp_path):
    p = tmp_path / "test.json"
    p.write_text('{"key": "value"}', encoding="utf-8")
    data = load_json(str(p))
    assert data == {"key": "value"}

def test_load_json_missing():
    data = load_json("non_existent_file.json", default=[])
    assert data == []

def test_load_json_corrupt(tmp_path):
    p = tmp_path / "corrupt.json"
    p.write_text("{broken json", encoding="utf-8")
    data = load_json(str(p), default="safe")
    assert data == "safe"

# 2. Test Logic (Mocking I/O)
@patch('utils.data_manager.st')
@patch('utils.data_manager.create_backup')
@patch('utils.data_manager.save_json') 
@patch('os.makedirs') 
def test_save_all_data(mock_makedirs, mock_save_json, mock_backup, mock_st):
    """
    Test that save_all_data constructs correct paths and calls save_json.
    """
    # --- THE FIX IS HERE ---
    # We define a real dictionary to act as our session state
    fake_state_data = {
        'current_class_id': "class_test_123"
    }
    
    # We tell the mock: "When .get() is called, use the real dictionary's .get method"
    mock_st.session_state.get.side_effect = fake_state_data.get

    # We also set attributes directly because some code might use st.session_state.students (dot notation)
    mock_st.session_state.current_class_id = "class_test_123"
    mock_st.session_state.students = [{"id": 1}]
    mock_st.session_state.assignments = []
    mock_st.session_state.config = {}
    mock_st.session_state.email_log = []
    mock_st.session_state.audit_log = []
    
    # Ensure save_json returns True so the function reports success
    mock_save_json.return_value = True

    # Run Function
    success = save_all_data(create_auto_backup=False)

    # Assert Success
    assert success is True
    
    # Assert Directory Creation
    # Now args[0] should be a real string path containing 'class_test_123'
    args, _ = mock_makedirs.call_args
    assert "class_test_123" in args[0]

    # Assert Save Calls
    # Verify save_json was called with the student list we defined above
    mock_save_json.assert_any_call(ANY, [{"id": 1}])