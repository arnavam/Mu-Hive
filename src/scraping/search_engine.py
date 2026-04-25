import logging
logger = logging.getLogger(__name__)

from pathlib import Path

from ddgs import DDGS
import requests
import time
import os 
from dotenv import load_dotenv
from src.db.database import Database

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

def run_search_agent(ig_mappings, categories, max_result=5):
    logger.info(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting scheduled search agent...")
    db = Database()

    logger.info("--------- Keyword Expansion -------------")
    search_queries = []
    for keyword, ig_key in ig_mappings.items():
        for category in categories:
            query = f"{keyword} {category}"
            search_queries.append({"query": query, "ig": ig_key})
            logger.info(f"- {query}")

    logger.info("\n--- Searching DuckDuckGo ---")
     
    ddgs = DDGS()
    for search_item in search_queries:
        query = search_item["query"]
        ig_key = search_item["ig"]
        logger.info(f"\nResults for '{query}':")
        try:
            results = []
            source_engine = 'DuckDuckGo'
            
            try:
                # Get top results for each expanded query via DuckDuckGo
                # Setting safesearch='moderate' and timelimit='y' helps filter out obscure/spam domains.
                results = list(ddgs.text(query, max_results=max_result, safesearch='moderate', timelimit='y'))
            except Exception as ddg_error:
                logger.info(f"   [!] DuckDuckGo failed ({ddg_error}). Falling back to Tavily...")
                source_engine = 'Tavily'
                time.sleep(2)  # Avoid fast consecutive requests
                try:
                    results = get_tavily_results(query, max_result)
                except Exception as t_error:
                    logger.info(f"   [!] Tavily Search also failed: {t_error}")

            if not results:
                logger.info("   No results found.")
            else:
                SPAM_DOMAINS = ["bloguerosa.com", "qodsblog.com", "blogdeazar.com", "blazingblog.com", "youtube.com", "facebook.com", "instagram.com",
    "tiktok.com"]
                for i, result in enumerate(results, start=1):
                    title = result.get('title', 'No Title')
                    link = result.get('href', result.get('url', 'No Link'))
                    
                    # Ensure high quality by filtering spam domains and low-reputation TLDs
                    is_spam = any(spam in link for spam in SPAM_DOMAINS)
                    is_low_quality = any(link.endswith(tld) or (tld + "/") in link for tld in [".xyz", ".info", ".top", ".cc", ".biz"])
                    if is_spam or is_low_quality:
                        logger.info(f"{i}. [Skip] Filtered low-quality or spam domain: {link}")
                        continue

                    logger.info(f"{i}. [{source_engine}] {title}")
                    logger.info(f"   Link: {link}")
                    
                    if not db.link_exists(link, ig_key):
                        db.insert_event(title, link, ig_key, source_engine, 'not processed')
        except Exception as e:
            logger.info(f"   Error searching for '{query}': {e}")
        
        # Small delay to avoid hitting rate limits too quickly
        time.sleep(1)
             
    db.close()

# Searching using Tavily Search API
def get_tavily_results(query, max_results=5):
    """Fetch results from Tavily Search API (fallback when DuckDuckGo fails)."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key or api_key == "your_tavily_api_key_here":
        logger.info("   [!] Tavily API key not configured in .env")
        logger.info("   [!] Get your API key at https://app.tavily.com and add it to .env")
        return []
    
    url = "https://api.tavily.com/search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "query": query,
        "search_depth": "advanced",
        "include_answer": False,
        "max_results": max_results
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()
    
    results = []
    for item in data.get('results', [])[:max_results]:
        results.append({
            'title': item.get('title', 'No Title'),
            'url': item.get('url', 'No Link')
        })
    return results


def main():
    logger.info("Search agent started. Running search...")
    logger.info("Press Ctrl+C to exit.")
    
    # We map the search terms dynamically to the actual IG email groups
    ig_mappings = {
        "Artificial intelligence": "ai",
        "web development": "web development",
        "Data science": "data science"
    }
    categories = ["internships", "Current news", "workshops", "events", "hackathons"]
    
    # Run the search agent immediately
    run_search_agent(ig_mappings, categories)
 
if __name__ == "__main__":
    main()
 
