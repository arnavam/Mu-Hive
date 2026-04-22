import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.orchestrator import run_pipeline

@pytest.mark.asyncio
@patch("src.orchestrator.run_scraper")
@patch("src.orchestrator.run_classifier")
@patch("src.orchestrator.run_validater")
@patch("src.orchestrator.run_summarizer")
@patch("src.orchestrator.run_outputs")
@patch("src.orchestrator.load_config")
async def test_run_pipeline_full_flow(
    mock_load_config, mock_outputs, mock_summarizer, mock_validater, mock_classifier, mock_scraper
):
    # Setup
    raw_item = MagicMock()
    mock_scraper.return_value = [raw_item]
    mock_classifier.return_value = [raw_item]
    
    verified_entry = {"item": raw_item, "score": 0.9, "status": "ready"}
    mock_validater.return_value = [verified_entry]
    
    clean_item = MagicMock()
    mock_summarizer.return_value = [clean_item]
    
    # Run
    await run_pipeline(ig_filter="AI")
    
    # Assert
    mock_scraper.assert_called_once_with(ig_filter="AI")
    mock_classifier.assert_called_once_with([raw_item])
    mock_validater.assert_called_once_with([raw_item])
    mock_summarizer.assert_called_once_with([verified_entry])
    mock_outputs.assert_called_once_with([clean_item])

@pytest.mark.asyncio
@patch("src.orchestrator.run_scraper")
@patch("src.orchestrator.logger")
async def test_run_pipeline_no_items(mock_logger, mock_scraper):
    # Setup
    mock_scraper.return_value = []
    
    # Run
    await run_pipeline()
    
    # Assert
    mock_logger.warning.assert_called_with("No items found during scraping.")
