"""
Run search first (collect links into MongoDB), then scrape pending links.
"""
from search_engine import run_search_agent
from scraper_agent import run_scraper_agent
import asyncio

def main():
    keywords = ["Artificial intelligence", "web development"]
    categories = ["internships", "Current news", "workshops", "events", "hackathons"]

    run_search_agent(keywords, categories)
    asyncio.run(run_scraper_agent())


if __name__ == "__main__":
    main()
