import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.agents.summarizer import run_summarizer, Extraction
from src.db.data_schemas import RawItem, CleanItem

@pytest.fixture
def sample_verified_entry():
    item = RawItem(
        title="Test Tech Opportunity",
        url="https://test.com/opp",
        text="This is a great tech opportunity for AI enthusiasts. Deadline is June 1st.",
        ig="AI",
        source="test"
    )
    return {"item": item, "score": 0.9, "status": "ready"}

@pytest.mark.asyncio
@patch("src.agents.summarizer.load_config")
@patch("src.agents.summarizer.make_llm_client")
@patch("src.agents.summarizer.get_limiter")
@patch("src.agents.summarizer.update_hashes_status")
@patch("src.agents.summarizer.get_hash")
async def test_summarizer_creates_clean_item(mock_get_hash, mock_update_hashes, mock_limiter, mock_make_client, mock_load_config, sample_verified_entry):
    # Setup
    mock_load_config.return_value = {
        "ig_routing": {"default": {"structurer": "cheap"}},
        "structurer_concurrency": 1
    }
    mock_get_hash.return_value = "fake_hash"
    
    mock_client = MagicMock()
    mock_extraction = Extraction(summary="A great opportunity.", category="hackathon", deadline="2026-06-01")
    mock_client.create.return_value = mock_extraction
    mock_make_client.return_value = mock_client
    
    mock_limiter_obj = AsyncMock()
    mock_limiter.return_value = mock_limiter_obj
    
    # Run
    results = await run_summarizer([sample_verified_entry])
    
    # Assert
    assert len(results) == 1
    item = results[0]
    assert isinstance(item, CleanItem)
    assert item.hash == "fake_hash"
    assert item.summary == "A great opportunity."
    assert item.category == "hackathon"
    assert item.deadline == "2026-06-01"
    mock_update_hashes.assert_called_once()

@pytest.mark.asyncio
@patch("src.agents.summarizer.load_config")
@patch("src.agents.summarizer.make_llm_client")
@patch("src.agents.summarizer.get_limiter")
@patch("src.agents.summarizer.update_hashes_status")
@patch("src.agents.summarizer.get_hash")
async def test_summarizer_fallback_on_error(mock_get_hash, mock_update_hashes, mock_limiter, mock_make_client, mock_load_config, sample_verified_entry):
    # Setup: LLM error should result in a fallback CleanItem with 'flagged' status
    mock_load_config.return_value = {
        "ig_routing": {"default": {"structurer": "cheap"}},
        "structurer_concurrency": 1
    }
    mock_get_hash.return_value = "fake_hash"
    
    mock_client = MagicMock()
    mock_client.create.side_effect = Exception("LLM Down")
    mock_make_client.return_value = mock_client
    
    # Run
    results = await run_summarizer([sample_verified_entry])
    
    # Assert
    assert len(results) == 1
    item = results[0]
    assert item.summary == "[Failed to extract summary]"
    assert item.status == "flagged"
