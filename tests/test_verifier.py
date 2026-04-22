import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.agents.validater import run_validater, Verification
from src.db.data_schemas import RawItem

@pytest.fixture
def sample_raw_item():
    return RawItem(
        title="Test Tech Opportunity",
        url="https://test.com/opp",
        text="This is a great tech opportunity for AI enthusiasts.",
        ig="AI",
        source="test"
    )

@pytest.mark.asyncio
@patch("src.agents.validater.load_config")
@patch("src.agents.validater.make_llm_client")
@patch("src.agents.validater.get_limiter")
@patch("src.agents.validater.update_hashes_status")
async def test_validater_passes_valid_item(mock_update_hashes, mock_limiter, mock_make_client, mock_load_config, sample_raw_item):
    # Setup
    mock_load_config.return_value = {
        "ig_routing": {"default": {"verifier": "cheap"}},
        "min_verified_score": 0.5,
        "verifier_concurrency": 1
    }
    
    mock_client = MagicMock()
    # Mock LLM response
    mock_verif = Verification(is_real=True, is_relevant=True, score=0.9, reason="Perfect match")
    mock_client.create.return_value = mock_verif
    mock_make_client.return_value = mock_client
    
    mock_limiter_obj = AsyncMock()
    mock_limiter.return_value = mock_limiter_obj
    
    # Run
    results = await run_validater([sample_raw_item])
    
    # Assert
    assert len(results) == 1
    assert results[0]["score"] == 0.9
    assert results[0]["status"] == "ready"
    mock_update_hashes.assert_called_once()

@pytest.mark.asyncio
@patch("src.agents.validater.load_config")
@patch("src.agents.validater.make_llm_client")
@patch("src.agents.validater.get_limiter")
@patch("src.agents.validater.update_hashes_status")
async def test_validater_drops_low_score_item(mock_update_hashes, mock_limiter, mock_make_client, mock_load_config, sample_raw_item):
    # Setup
    mock_load_config.return_value = {
        "ig_routing": {"default": {"verifier": "cheap"}},
        "min_verified_score": 0.5,
        "verifier_concurrency": 1
    }
    
    mock_client = MagicMock()
    mock_verif = Verification(is_real=True, is_relevant=True, score=0.2, reason="Not good enough")
    mock_client.create.return_value = mock_verif
    mock_make_client.return_value = mock_client
    
    # Run
    results = await run_validater([sample_raw_item])
    
    # Assert
    assert len(results) == 0

@pytest.mark.asyncio
@patch("src.agents.validater.load_config")
@patch("src.agents.validater.make_llm_client")
@patch("src.agents.validater.get_limiter")
@patch("src.agents.validater.update_hashes_status")
async def test_validater_escalation(mock_update_hashes, mock_limiter, mock_make_client, mock_load_config, sample_raw_item):
    # Setup: Gray zone score (0.7) should trigger escalation if tier is cheap
    mock_load_config.return_value = {
        "ig_routing": {"default": {"verifier": "cheap"}},
        "min_verified_score": 0.5,
        "verifier_concurrency": 1,
        "max_premium_items_per_run": 5
    }
    
    # First response: Cheap model gives 0.7
    mock_verif_cheap = Verification(is_real=True, is_relevant=True, score=0.7, reason="Maybe")
    # Second response: Premium model gives 0.9
    mock_verif_premium = Verification(is_real=True, is_relevant=True, score=0.9, reason="Definitely")
    
    mock_client_cheap = MagicMock()
    mock_client_cheap.create.return_value = mock_verif_cheap
    
    mock_client_premium = MagicMock()
    mock_client_premium.create.return_value = mock_verif_premium
    
    # make_llm_client will be called twice
    mock_make_client.side_effect = [mock_client_cheap, mock_client_premium]
    
    # Run
    results = await run_validater([sample_raw_item])
    
    # Assert
    assert len(results) == 1
    assert results[0]["score"] == 0.9 # Should have the premium score
    assert mock_make_client.call_count == 2
