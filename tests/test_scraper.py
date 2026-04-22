import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.scraping.scraper import scrape_rss, scrape_unstop, scrape_devfolio, run_scraper
from src.db.data_schemas import RawItem

@pytest.mark.asyncio
@patch("src.scraping.scraper.feedparser.parse")
@patch("src.scraping.scraper.extract_text")
async def test_scrape_rss_success(mock_extract, mock_parse):
    # Setup
    mock_entry = MagicMock()
    mock_entry.link = "https://test.com/news"
    mock_entry.get.side_effect = lambda key, default: {"title": "Test Title", "summary": "Test Summary"}.get(key, default)
    
    mock_feed = MagicMock()
    mock_feed.entries = [mock_entry]
    mock_parse.return_value = mock_feed
    
    mock_extract.return_value = {"text": "Extracted Text", "title_fallback": None}
    
    # Run
    items = await scrape_rss("https://test.com/rss", "AI")
    
    # Assert
    assert len(items) == 1
    assert items[0].title == "Test Title"
    assert items[0].source == "rss"
    assert items[0].ig == "AI"

@pytest.mark.asyncio
@patch("src.scraping.scraper.httpx.AsyncClient")
async def test_scrape_unstop_success(mock_client_class):
    # Setup
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": {
            "data": [
                {"title": "Unstop Hack", "seo_url": "hack-slug"}
            ]
        }
    }
    
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client_class.return_value.__aenter__.return_value = mock_client
    
    # Run
    items = await scrape_unstop("AI")
    
    # Assert
    assert len(items) == 1
    assert items[0].title == "Unstop Hack"
    assert "unstop.com" in items[0].url
    assert items[0].source == "unstop"

@pytest.mark.asyncio
@patch("src.scraping.scraper.httpx.AsyncClient")
async def test_scrape_devfolio_success(mock_client_class):
    # Setup
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "hits": {
            "hits": [
                {"_source": {"name": "Devfolio Hack", "slug": "slug1"}}
            ]
        }
    }
    
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp
    mock_client_class.return_value.__aenter__.return_value = mock_client
    
    # Run
    items = await scrape_devfolio("AI")
    
    # Assert
    assert len(items) == 1
    assert items[0].title == "Devfolio Hack"
    assert "slug1.devfolio.co" in items[0].url

@pytest.mark.asyncio
@patch("src.scraping.scraper.load_config")
@patch("src.scraping.scraper.scrape_unstop")
@patch("src.scraping.scraper.scrape_devfolio")
@patch("src.scraping.scraper.scrape_devpost")
@patch("src.scraping.scraper.scrape_hackerearth")
@patch("src.scraping.scraper.scrape_newsapi")
@patch("src.scraping.scraper.scrape_social")
async def test_run_scraper_coordinates_tasks(
    mock_social, mock_news, mock_he, mock_dp, mock_df, mock_un, mock_load_config
):
    # Setup: Return one item from each to verify aggregation
    mock_load_config.return_value = {
        "interest_groups": {"AI": {"active": True}},
        "sources": {"global": {"rss": [], "search": []}},
        "pipeline": {"max_concurrent_scrapers": 2}
    }
    
    item = RawItem(title="Test", url="url", text="text", ig="AI", source="test")
    mock_un.return_value = [item]
    mock_df.return_value = [item]
    mock_dp.return_value = []
    mock_he.return_value = []
    mock_news.return_value = []
    mock_social.return_value = []
    
    # Run
    all_items = await run_scraper(ig_filter="AI")
    
    # Assert
    assert len(all_items) == 2
    assert mock_un.called
    assert mock_df.called
