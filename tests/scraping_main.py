from src.scraping.search_engine import run_search_agent
from src.scraping.scraper_agent import run_scraper_agent, run_rss_agent
from src.scraping.eventslink_parser import main as run_eventslink_parser
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Silence noisy third-party library loggers
for noisy in ["httpx", "trafilatura", "trafilatura.core", "readability", "readability.readability", "primp", "urllib3", "charset_normalizer"]:
    logging.getLogger(noisy).setLevel(logging.WARNING)

async def main():
    keywords = ["Artificial intelligence", "web development"]
    categories = ["internships", "Current news", "workshops", "events", "hackathons"]

    logger.info("=" * 55)
    logger.info("  Extracting from SearchEngine")
    logger.info("=" * 55)
    run_search_agent(keywords, categories)

    logger.info("=" * 55)
    logger.info("  Scraping SearchEngine Links")
    logger.info("=" * 55)
    await run_scraper_agent()

    logger.info("=" * 55)
    logger.info("  Extracting Eventslink")
    logger.info("=" * 55)
    await run_eventslink_parser()

    logger.info("=" * 55)
    logger.info("  Scraping Eventslink Links")
    logger.info("=" * 55)
    await run_scraper_agent()

    logger.info("=" * 55)
    logger.info("  Scraping RSS Feeds")
    logger.info("=" * 55)
    await run_rss_agent()

if __name__ == "__main__":
    asyncio.run(main())
