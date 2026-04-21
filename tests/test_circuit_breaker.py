import pytest
import time
import json
from unittest.mock import patch, MagicMock, mock_open
from src.circuit_breaker import mark_failure, is_cooled_down

@patch("src.circuit_breaker.load_config")
@patch("src.circuit_breaker.get_circuit_state")
@patch("builtins.open", new_callable=mock_open)
@patch("time.time")
def test_mark_failure_sets_expiry_correctly(mock_time, mock_file, mock_get_state, mock_load_config):
    # Setup
    mock_time.return_value = 1000.0
    mock_load_config.return_value = {"pipeline": {"circuit_cooldown_seconds": 300}}
    mock_get_state.return_value = {}
    
    # Run
    mark_failure("groq")
    
    # Assert
    # Extract the data passed to json.dump
    # get the string written to the file
    written_data = "".join(call.args[0] for call in mock_file().write.call_args_list)
    state = json.loads(written_data)
    
    assert state["groq"]["expiry"] == 1300.0

@patch("src.circuit_breaker.get_circuit_state")
@patch("time.time")
def test_is_cooled_down_returns_false_during_window(mock_time, mock_get_state):
    # Setup
    mock_time.return_value = 1000.0
    mock_get_state.return_value = {"groq": {"expiry": 1500.0}}
    
    # Run & Assert
    assert is_cooled_down("groq") is False

@patch("src.circuit_breaker.get_circuit_state")
@patch("time.time")
def test_is_cooled_down_returns_true_after_expiry(mock_time, mock_get_state):
    # Setup
    mock_time.return_value = 2000.0
    mock_get_state.return_value = {"groq": {"expiry": 1500.0}}
    
    # Run & Assert
    assert is_cooled_down("groq") is True
