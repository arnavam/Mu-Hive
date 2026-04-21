"""Quick test to verify Tavily API is working."""
from pathlib import Path

from dotenv import load_dotenv
from src.scraping.search_engine import get_tavily_results
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).resolve().parent / ".env")

logger.info("Testing Tavily Search API...")
logger.info("-" * 40)

results = get_tavily_results("Artificial intelligence internships", max_results=3)

if results:
    logger.info(f"Tavily is working! Got {len(results)} results:")
    for i, r in enumerate(results, 1):
        logger.info(f"  {i}. {r['title']}\n     {r['url']}")
else:
    logger.error("No results returned. Check your TAVILY_API_KEY in .env")
