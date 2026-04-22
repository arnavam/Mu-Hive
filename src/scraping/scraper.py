import asyncio
import feedparser
import httpx
import os
from typing import List, Optional, Coroutine
from bs4 import BeautifulSoup
from loguru import logger
from newsapi import NewsApiClient
from apify_client import ApifyClient
from src.db.data_schemas import RawItem
from src.config import load_config
from src.config.sources import UNSTOP_API, DEVFOLIO_API, DEVPOST_API, HACKEREARTH_API
from src.http_utils import get_random_ua
from src.scraping.curate import extract_text
from src.scraping.search_engine import scrape_search

# --- RSS Scraper --- #
async def scrape_rss(feed_url: str, ig_name: str) -> List[RawItem]:
    """Scrapes a single RSS feed and converts entries to RawItems."""
    logger.info(f"Scraping RSS: {feed_url} ({ig_name})")
    scraped_items: List[RawItem] = []
    try:
        # feedparser is a robust library for RSS/Atom parsing
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:10]:
            try:
                if not hasattr(entry, 'link'): continue
                
                # Try to find a description or content
                description = entry.get('summary', '')
                if not description and 'content' in entry:
                    description = entry.content[0].value
                
                # Fetch full article text using trafilatura
                curation = await extract_text(entry.link)
                title = entry.get('title', curation.get('title_fallback', 'Untitled'))
                final_text = curation.get('text') or BeautifulSoup(description, "lxml").get_text()
                
                scraped_items.append(RawItem(
                    title=title, 
                    url=entry.link, 
                    text=final_text, 
                    ig=ig_name, 
                    source="rss"
                ))
            except Exception as e:
                logger.debug(f"Failed to parse RSS item {entry.link}: {e}")
    except Exception as e:
        logger.error(f"RSS Feed error {feed_url}: {e}")
    return scraped_items

# --- Specialized Platform Scrapers --- #
async def scrape_unstop(ig_name: str) -> List[RawItem]:
    """Fetches upcoming hackathons directly from the Unstop API."""
    logger.info(f"Scraping Unstop for {ig_name}")
    items: List[RawItem] = []
    try:
        url = f"{UNSTOP_API}?opportunity=hackathons&per_page=15"
        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": get_random_ua()}) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                for opp in data.get("data", {}).get("data", []):
                    title = opp.get("title")
                    seo_slug = opp.get("seo_url")
                    link = seo_slug if (seo_slug and seo_slug.startswith("http")) else f"https://unstop.com/hackathons/{seo_slug}" if seo_slug else ""
                    items.append(RawItem(title=title, url=link, text=f"Unstop Opportunity: {title}", ig=ig_name, source="unstop"))
    except Exception as e:
        logger.error(f"Unstop API error: {e}")
    return items

async def scrape_devfolio(ig_name: str) -> List[RawItem]:
    """Fetches hackathons from the Devfolio Search API."""
    logger.info(f"Scraping Devfolio for {ig_name}")
    items: List[RawItem] = []
    try:
        payload = {"from": 0, "size": 15, "query": {"match_all": {}}}
        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": get_random_ua()}) as client:
            response = await client.post(DEVFOLIO_API, json=payload)
            if response.status_code == 200:
                data = response.json()
                for hit in data.get("hits", {}).get("hits", []):
                    source_data = hit.get("_source", {})
                    name = source_data.get("name")
                    slug = source_data.get("slug")
                    link = f"https://{slug}.devfolio.co" if slug else ""
                    items.append(RawItem(title=name, url=link, text=f"Devfolio Event: {name}", ig=ig_name, source="devfolio"))
    except Exception as e:
        logger.error(f"Devfolio API error: {e}")
    return items

async def scrape_devpost(ig_name: str) -> List[RawItem]:
    """Fetches hackathons from Devpost."""
    logger.info(f"Scraping Devpost for {ig_name}")
    items: List[RawItem] = []
    try:
        url = f"{DEVPOST_API}?page=1"
        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": get_random_ua()}) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                for hackathon in data.get("hackathons", []):
                    title = hackathon.get("title")
                    link = hackathon.get("url")
                    items.append(RawItem(title=title, url=link, text=f"Devpost Competition: {title}", ig=ig_name, source="devpost"))
    except Exception as e:
        logger.error(f"Devpost API error: {e}")
    return items

async def scrape_hackerearth(ig_name: str) -> List[RawItem]:
    """Fetches challenges from the HackerEarth Public API."""
    logger.info(f"Scraping HackerEarth for {ig_name}")
    items: List[RawItem] = []
    try:
        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": get_random_ua()}) as client:
            response = await client.get(HACKEREARTH_API)
            if response.status_code == 200:
                data = response.json()
                for event in data.get("response", []):
                    title = event.get("title")
                    link = event.get("url")
                    items.append(RawItem(title=title, url=link, text=f"HackerEarth Challenge: {title}", ig=ig_name, source="hackerearth"))
    except Exception as e:
        logger.error(f"HackerEarth API error: {e}")
    return items

async def scrape_newsapi(ig_name: str) -> List[RawItem]:
    """Fetches technical news articles using the NewsAPI search endpoint."""
    api_key = os.environ.get("NEWSAPI_KEY")
    if not api_key: return []
    logger.info(f"Scraping NewsAPI for {ig_name}")
    try:
        def _fetch_blocking():
            client = NewsApiClient(api_key=api_key)
            query_string = f"{ig_name} AND (hackathon OR opportunity OR internship OR research)"
            return client.get_everything(
                q=query_string,
                domains="techcrunch.com,theverge.com,wired.com,arstechnica.com,venturebeat.com",
                language="en",
                sort_by="publishedAt",
                page_size=10
            )
        # NewsAPI library is synchronous, we run it in a thread to keep the pipeline async
        raw_data = await asyncio.to_thread(_fetch_blocking)
        items: List[RawItem] = []
        for article in raw_data.get("articles", []):
            items.append(RawItem(
                title=article.get("title", ""),
                url=article.get("url", ""),
                text=article.get("description", ""),
                ig=ig_name,
                source="newsapi"
            ))
        return items
    except Exception as e:
        logger.error(f"NewsAPI error: {e}")
        return []

async def scrape_social(ig_name: str) -> List[RawItem]:
    """Placeholder for social monitoring via Apify."""
    token = os.environ.get("APIFY_API_TOKEN")
    if not token: return []
    logger.info(f"Scraping Social Monitoring (Apify) for {ig_name}")
    try:
        client = ApifyClient(token)
        def _run_actor():
            return [] # Future expansion point
        return await asyncio.to_thread(_run_actor)
    except Exception as e:
        logger.error(f"Apify Social error: {e}")
        return []

async def scrape_direct_site(url: str, ig_name: str) -> List[RawItem]:
    """Scrapes a specific URL defined in config.yaml."""
    logger.info(f"Scraping Direct Site: {url} ({ig_name})")
    try:
        content = await extract_text(url)
        title = content.get('title_fallback') or url
        return [RawItem(title=title, url=url, text=content.get('text', ''), ig=ig_name, source="direct_site")]
    except Exception as e:
        logger.error(f"Direct Site error {url}: {e}")
        return []

# --- Main Entry Point --- #
async def run_scraper(ig_filter: Optional[str] = None) -> List[RawItem]:
    """ Coordinates all scraping tasks in parallel with concurrency control. """
    full_config = load_config()
    sources_cfg = full_config.get("sources", {})
    all_groups = full_config.get("interest_groups", {})
    pipeline_settings = full_config.get("pipeline", {})
    
    # Use a semaphore to prevent overloading network/system
    concurrency_limit = pipeline_settings.get("max_concurrent_scrapers", 3)
    parallel_gate = asyncio.Semaphore(concurrency_limit)
    
    async def _throttled_task(coroutine: Coroutine):
        async with parallel_gate:
            return await coroutine
            
    scraping_tasks = []
    for ig_name, ig_cfg in all_groups.items():
        # Filtering logic
        if ig_filter and ig_name != ig_filter: continue
        if not ig_cfg.get("active", True): continue
            
        # 1. Add Platform Scrapers
        scraping_tasks.append(_throttled_task(scrape_unstop(ig_name)))
        scraping_tasks.append(_throttled_task(scrape_devfolio(ig_name)))
        scraping_tasks.append(_throttled_task(scrape_devpost(ig_name)))
        scraping_tasks.append(_throttled_task(scrape_hackerearth(ig_name)))
        scraping_tasks.append(_throttled_task(scrape_newsapi(ig_name)))
        scraping_tasks.append(_throttled_task(scrape_social(ig_name)))
        
        # 2. Add Sources from config.yaml
        ig_specific_sources = sources_cfg.get("interest_groups", {}).get(ig_name, {})
        glob_sources = sources_cfg.get("global", {})
        
        # Combined RSS feeds
        for rss in glob_sources.get("rss", []) + ig_specific_sources.get("rss", []):
            scraping_tasks.append(_throttled_task(scrape_rss(rss["url"], ig_name)))
            
        # Search Engine queries
        for search in glob_sources.get("search", []) + ig_specific_sources.get("search", []):
            scraping_tasks.append(_throttled_task(scrape_search(search["query"], ig_name)))
            
        # Direct URL scraping
        for site in ig_specific_sources.get("sites", []):
            scraping_tasks.append(_throttled_task(scrape_direct_site(site["url"], ig_name)))
            
    # Execute all tasks concurrently
    aggregated_results = await asyncio.gather(*scraping_tasks)
    
    # Flatten results from list of lists to a single list of RawItems
    all_items = [item for sublist in aggregated_results for item in sublist]
    
    logger.info(f"Scraper Final: Harvested {len(all_items)} raw items across all sources.")
    return all_items
