import pytest
import json
import csv
from unittest.mock import patch, mock_open, MagicMock
from src.db.database import run_outputs
from src.db.data_schemas import CleanItem

@pytest.fixture
def sample_clean_item():
    return CleanItem(
        hash="hash1",
        title="Test Clean",
        url="https://test.com",
        summary="A summary.",
        ig="AI",
        source="rss",
        category="hackathon",
        deadline="2026-06-01",
        score=0.9,
        status="ready",
        created_at="2026-04-22T12:00:00"
    )

@patch("src.db.database.load_config")
@patch("src.db.database.os.makedirs")
@patch("builtins.open", new_callable=mock_open)
def test_run_outputs_json(mock_file, mock_makedirs, mock_load_config, sample_clean_item):
    # Setup
    mock_load_config.return_value = {
        "json_file": {
            "active": True,
            "type": "json_file",
            "path": "data/results.json",
            "pretty": True
        }
    }
    
    # Run
    run_outputs([sample_clean_item])
    
    # Assert
    mock_file.assert_called_with("data/results.json", "w")
    # Verify json.dump was called (it uses the file handle)
    # The actual content check is tricky with mock_open and json.dump, 
    # but we verify the call to open with correct path.
    handle = mock_file()
    # Check if any write happened
    assert handle.write.called

@patch("src.db.database.load_config")
@patch("src.db.database.os.makedirs")
@patch("builtins.open", new_callable=mock_open)
def test_run_outputs_csv(mock_file, mock_makedirs, mock_load_config, sample_clean_item):
    # Setup
    mock_load_config.return_value = {
        "csv_file": {
            "active": True,
            "type": "csv_file",
            "path": "data/results.csv"
        }
    }
    
    # Run
    run_outputs([sample_clean_item])
    
    # Assert
    mock_file.assert_called_with("data/results.csv", "w", newline="")

@patch("src.db.database.load_config")
@patch("builtins.print")
def test_run_outputs_console(mock_print, mock_load_config, sample_clean_item):
    # Setup
    mock_load_config.return_value = {
        "console": {
            "active": True,
            "type": "console",
            "show_fields": ["title", "ig"]
        }
    }
    
    # Run
    run_outputs([sample_clean_item])
    
    # Assert
    # Check if any print occurred
    assert mock_print.called
    # Check if title was printed
    found = False
    for call in mock_print.call_args_list:
        if "Test Clean" in str(call):
            found = True
            break
    assert found
