from src.scraping.firecrawl_tool import firecrawl_scraper

class ScoutAgent:
    """Agent wrapper for the scraper (retains backward compatibility)"""
    def run(self, mode, url, options):
        return firecrawl_scraper(url, mode, options)

scout = ScoutAgent()
