from src.scraping.search_engine import run_search_agent
from src.scraping.scraper_agent import run_scraper_agent, run_rss_agent
from src.scraping.scraper import run_scraper_pipeline
from src.db.postgres_database import save_events
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

#print eventslink results
def _print_results(grouped):
    print("\n" + "═" * 55)
    print("  🚀  Scraper Pipeline Data")
    print("═" * 55)

    active_count = 0
    total_events = 0

    for ig, events in grouped.items():
        if not events:
            continue
            
        active_count += 1
        total_events += len(events)
        
        print(f"\n{'─'*55}")
        print(f"  📌  {ig}  ({len(events)} events)")
        print(f"{'─'*55}")
        
        for i, event in enumerate(events, 1):
            title = event.eventName
            days  = event.days_remaining or 0
            plat  = event.platform or "Unknown"
            link  = event.registrationLink
            loc   = event.location or "Online"
            
            print(f"\n  {i}. {title}")
            print(f"     {days}d left │ {plat} │ {loc}")
            print(f"     🔗 {link}")

    print(f"\n{'═'*55}")
    print(f"  ✅  {active_count} IGs active  │  {total_events} events")
    print(f"{'═'*55}\n")

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

if __name__ == "__main__":
    asyncio.run(main())
