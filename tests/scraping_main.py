from src.scraping.search_engine import run_search_agent
from src.scraping.scraper_agent import run_scraper_agent, run_rss_agent
from src.scraping.scraper import run_scraper_pipeline
from src.scraping.scraper import save_events, _print_results
from scripts.gmailsender import run_email_agent
import sys
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Silence noisy third-party library loggers
for noisy in ["httpx", "trafilatura", "trafilatura.core", "readability", "readability.readability", "primp", "urllib3", "charset_normalizer", "duckduckgo_search"]:
    logging.getLogger(noisy).setLevel(logging.WARNING)

async def main():
    
    ig_mappings = {
        "Artificial intelligence": "ai",
        "web development": "web development",
        "Data science": "data science",
    }
    categories = ["Current news"]

    logger.info("=" * 55)
    logger.info("  Extracting from SearchEngine")
    logger.info("=" * 55)
    run_search_agent(ig_mappings, categories)

    logger.info("=" * 55)
    logger.info("  Scraping SearchEngine Links")
    logger.info("=" * 55)
    await run_scraper_agent()

    logger.info("=" * 55)
    logger.info("  Extracting Eventslink")
    logger.info("=" * 55)
    grouped_events = await run_scraper_pipeline()
    _print_results(grouped_events)
    inserted, modified = save_events(grouped_events)
    logger.info(f"  Inserted {inserted} and skipped/modified {modified} events to DB.")

    logger.info("=" * 55)
    logger.info("  Scraping Eventslink Links")
    logger.info("=" * 55)
    await run_scraper_agent()

    logger.info("=" * 55)
    logger.info("  Scraping RSS Feeds")
    logger.info("=" * 55)
    await run_rss_agent()

    logger.info("=" * 55)
    logger.info("  Sending Email Digests")
    logger.info("=" * 55)
    # run_email_agent is synchronous, we can run it directly
    run_email_agent()

if __name__ == "__main__":
    asyncio.run(main())
