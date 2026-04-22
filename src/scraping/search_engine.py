import os
import asyncio
import random
import httpx
from loguru import logger
from ddgs import DDGS
from aiolimiter import AsyncLimiter
from src.config import load_config
from src.scraping.curate import extract_text
from src.db.data_schemas import RawItem

_SEARCH_LIMITER = None

def get_search_limiter():
    """Returns the search rate limiter based on config."""
    global _SEARCH_LIMITER
    if _SEARCH_LIMITER is None:
        settings = load_config("pipeline")
        rpm = settings.get("search_rpm", 5)
        _SEARCH_LIMITER = AsyncLimiter(rpm, 60)
    return _SEARCH_LIMITER

async def scrape_tavily(query, max_results=5):
    """Hits Tavily API for search results."""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return []
    
    logger.info(f"Tavily searching: {query}")
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": max_results
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("results", [])
    except Exception as e:
        logger.warning(f"Tavily failed: {e}")
        return []

async def scrape_search(query, ig):
    """Scrapes search results from DDG with Tavily fallback."""
    logger.info(f"Searching query: {query} for IG: {ig}")
    items = []
    search_limiter = get_search_limiter()
    
    try:
        results = []
        async with search_limiter:
            # Primary: DuckDuckGo
            try:
                results = await asyncio.to_thread(lambda: list(DDGS().text(query, max_results=5)))
            except Exception as e:
                logger.warning(f"DuckDuckGo failed: {e}. Falling back to Tavily.")
            
            # Fallback: Tavily
            if not results:
                tav_results = await scrape_tavily(query)
                for r in tav_results:
                    results.append({
                        'title': r.get('title'), 
                        'href': r.get('url'), 
                        'body': r.get('content')
                    })

        for res in results:
            try:
                url = res.get('href')
                if not url: continue
                res_data = await extract_text(url)
                title = res.get('title', res_data.get('title_fallback', 'No Title'))
                items.append(RawItem(
                    title=title, 
                    url=url, 
                    text=res_data.get('text', ''), 
                    ig=ig, 
                    source="search"
                ))
                await asyncio.sleep(random.uniform(0.5, 1.5))
            except Exception as e:
                logger.debug(f"Search item failed {url}: {e}")
                
    except Exception as e:
        logger.error(f"Search failure for '{query}': {e}")
    return items
