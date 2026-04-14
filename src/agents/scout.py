from firecrawl import FirecrawlApp
from src.config.settings import FIRECRAWL_API_KEY

def firecrawl_scraper(url: str, mode: str = 'scrape', options: dict = None):
    """
    Standalone function to scrape or crawl a URL using Firecrawl.
    Handles serialization of the result automatically.
    """
    if options is None:
        options = {}

    if not FIRECRAWL_API_KEY:
        raise ValueError("Firecrawl API key not found.")

    app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
    
    # Execute scrape/crawl
    if mode == 'crawl':
        result = app.crawl(url, scrape_options=options)
    else:
        # Handle both old and new firecrawl-py versions
        if hasattr(app, 'scrape_url'):
            result = app.scrape_url(url, params=options)
        else:
            result = app.scrape(url, **options)

    # Handle object serialization (converting Firecrawl response objects to dicts)
    if hasattr(result, 'model_dump'):
        serializable_result = result.model_dump()
    elif hasattr(result, 'dict'):
        serializable_result = result.dict()
    elif hasattr(result, '__dict__'):
        serializable_result = result.__dict__
    else:
        serializable_result = result

    return serializable_result

class ScoutAgent:
    """Agent wrapper for the scraper (retains backward compatibility)"""
    def run(self, mode, url, options):
        return firecrawl_scraper(url, mode, options)

scout = ScoutAgent()
