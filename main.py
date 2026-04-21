"""
Run search first (collect links into MongoDB), then scrape pending links.
"""
from src.scraping.search_engine import run_search_agent
from src.scraping.scraper_agent import run_scraper_agent
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    keywords = ["Artificial intelligence", "web development"]
    categories = ["internships", "Current news", "workshops", "events", "hackathons"]

    run_search_agent(keywords, categories)
    await run_scraper_agent()


if __name__ == "__main__":
    asyncio.run(main())