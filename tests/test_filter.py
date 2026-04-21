import pytest
from unittest.mock import patch, MagicMock
from src.pipeline.stage_02_filter import run_filter
from src.schemas import RawItem

@pytest.fixture
def sample_item():
    return RawItem(
        title="Test Opportunity",
        url="https://example.com/jobs",
        text="Looking for someone with tech skills.",
        ig="AI",
        source="test"
    )

@patch("src.pipeline.stage_02_filter.load_config")
@patch("src.pipeline.stage_02_filter.get_hash")
@patch("os.path.exists")
@patch("builtins.open")
def test_duplicate_hash_is_dropped(mock_open, mock_exists, mock_get_hash, mock_load_config, sample_item):
    # Setup
    mock_load_config.side_effect = lambda name: {
        "settings": {"pipeline": {"seen_hashes_file": "state/seen_hashes.json"}},
        "blocklist": {"words": [], "domains": []}
    }[name]
    mock_exists.return_value = True
    mock_get_hash.return_value = "fake_hash"
    
    # Mock reading seen_hashes.json where the item is already "structured"
    mock_open.return_value.__enter__.return_value.read.return_value = '{"fake_hash": {"status": "structured"}}'
    
    # Run
    result = run_filter([sample_item])
    
    # Assert
    assert len(result) == 0

@patch("src.pipeline.stage_02_filter.load_config")
@patch("src.pipeline.stage_02_filter.get_hash")
@patch("os.path.exists")
@patch("builtins.open")
def test_blocklist_word_drops_item(mock_open, mock_exists, mock_get_hash, mock_load_config, sample_item):
    # Setup
    mock_load_config.side_effect = lambda name: {
        "settings": {"pipeline": {"seen_hashes_file": "state/seen_hashes.json"}},
        "blocklist": {"words": ["crypto"], "domains": []}
    }[name]
    mock_exists.return_value = False # No seen hashes yet
    mock_get_hash.return_value = "fake_hash"
    
    sample_item.title = "A Crypto Job"
    
    # Run
    result = run_filter([sample_item])
    
    # Assert
    assert len(result) == 0

@patch("src.pipeline.stage_02_filter.load_config")
@patch("src.pipeline.stage_02_filter.get_hash")
@patch("os.path.exists")
@patch("builtins.open")
def test_blocklist_domain_drops_item(mock_open, mock_exists, mock_get_hash, mock_load_config, sample_item):
    # Setup
    mock_load_config.side_effect = lambda name: {
        "settings": {"pipeline": {"seen_hashes_file": "state/seen_hashes.json"}},
        "blocklist": {"words": [], "domains": ["spam.com"]}
    }[name]
    mock_exists.return_value = False
    mock_get_hash.return_value = "fake_hash"
    
    sample_item.url = "https://spam.com/article"
    
    # Run
    result = run_filter([sample_item])
    
    # Assert
    assert len(result) == 0

@patch("src.pipeline.stage_02_filter.load_config")
@patch("src.pipeline.stage_02_filter.get_hash")
@patch("os.path.exists")
@patch("builtins.open")
def test_verified_item_passes_through_with_status(mock_open, mock_exists, mock_get_hash, mock_load_config, sample_item):
    # Setup
    mock_load_config.side_effect = lambda name: {
        "settings": {"pipeline": {"seen_hashes_file": "state/seen_hashes.json"}},
        "blocklist": {"words": [], "domains": []}
    }[name]
    mock_exists.return_value = True
    mock_get_hash.return_value = "fake_hash"
    
    # Mock reading seen_hashes.json where the item is "verified"
    mock_open.return_value.__enter__.return_value.read.return_value = '{"fake_hash": {"status": "verified"}}'
    
    # Run
    result = run_filter([sample_item])
    
    # Assert
    assert len(result) == 1
    assert result[0].status == "verified"
