import asyncio
import feedparser
import httpx
import os
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

# RSS Scraper
async def scrape_rss(feed_url, ig):
    """Scrapes a single RSS feed and returns RawItems."""
    logger.info(f"Scraping RSS: {feed_url} for IG: {ig}")
    items = []
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:10]:
            try:
                if not hasattr(entry, 'link'): continue
                
                desc = entry.get('summary', '')
                if not desc and 'content' in entry:
                    desc = entry.content[0].value
                
                res = await extract_text(entry.link)
                title = entry.get('title', res.get('title_fallback', 'No Title'))
                extracted_text = res.get('text') or BeautifulSoup(desc, "lxml").get_text()
                
                items.append(RawItem(
                    title=title, 
                    url=entry.link, 
                    text=extracted_text, 
                    ig=ig, 
                    source="rss"
                ))
            except Exception as e:
                logger.debug(f"RSS item failed {entry.link}: {e}")
    except Exception as e:
        logger.error(f"RSS failure {feed_url}: {e}")
    return items

# Specialized Platform Scrapers
async def scrape_unstop(ig):
    logger.info(f"Hitting Unstop API for IG: {ig}")
    items = []
    try:
        url = f"{UNSTOP_API}?opportunity=hackathons&per_page=15"
        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": get_random_ua()}) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                for opp in data.get("data", {}).get("data", []):
                    title = opp.get("title")
                    seo = opp.get("seo_url")
                    link = seo if (seo and seo.startswith("http")) else f"https://unstop.com/hackathons/{seo}" if seo else ""
                    items.append(RawItem(title=title, url=link, text=f"Unstop Hackathon: {title}", ig=ig, source="unstop"))
    except Exception as e:
        logger.error(f"Unstop API failed: {e}")
    return items

async def scrape_devfolio(ig):
    logger.info(f"Hitting Devfolio API for IG: {ig}")
    items = []
    try:
        payload = {"from": 0, "size": 15, "query": {"match_all": {}}}
        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": get_random_ua()}) as client:
            resp = await client.post(DEVFOLIO_API, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                for hit in data.get("hits", {}).get("hits", []):
                    src = hit.get("_source", {})
                    name = src.get("name")
                    slug = src.get("slug")
                    link = f"https://{slug}.devfolio.co" if slug else ""
                    items.append(RawItem(title=name, url=link, text=f"Devfolio Hackathon: {name}", ig=ig, source="devfolio"))
    except Exception as e:
        logger.error(f"Devfolio API failed: {e}")
    return items

async def scrape_devpost(ig):
    logger.info(f"Hitting Devpost API for IG: {ig}")
    items = []
    try:
        url = f"{DEVPOST_API}?page=1"
        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": get_random_ua()}) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                for hack in data.get("hackathons", []):
                    name = hack.get("title")
                    link = hack.get("url")
                    items.append(RawItem(title=name, url=link, text=f"Devpost Hackathon: {name}", ig=ig, source="devpost"))
    except Exception as e:
        logger.error(f"Devpost API failed: {e}")
    return items

async def scrape_hackerearth(ig):
    logger.info(f"Hitting HackerEarth API for IG: {ig}")
    items = []
    try:
        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": get_random_ua()}) as client:
            resp = await client.get(HACKEREARTH_API)
            if resp.status_code == 200:
                data = resp.json()
                for ev in data.get("response", []):
                    name = ev.get("title")
                    link = ev.get("url")
                    items.append(RawItem(title=name, url=link, text=f"HackerEarth Event: {name}", ig=ig, source="hackerearth"))
    except Exception as e:
        logger.error(f"HackerEarth API failed: {e}")
    return items

async def scrape_newsapi(ig):
    key = os.environ.get("NEWSAPI_KEY")
    if not key: return []
    logger.info(f"Hitting NewsAPI for IG: {ig}")
    try:
        def _fetch():
            client = NewsApiClient(api_key=key)
            query = f"{ig} AND (hackathon OR opportunity OR internship OR research)"
            return client.get_everything(
                q=query,
                domains="techcrunch.com,theverge.com,wired.com,arstechnica.com,venturebeat.com",
                language="en",
                sort_by="publishedAt",
                page_size=10
            )
        data = await asyncio.to_thread(_fetch)
        items = []
        for art in data.get("articles", []):
            items.append(RawItem(
                title=art.get("title", ""),
                url=art.get("url", ""),
                text=art.get("description", ""),
                ig=ig,
                source="newsapi"
            ))
        return items
    except Exception as e:
        logger.error(f"NewsAPI failed: {e}")
        return []

async def scrape_social(ig):
    token = os.environ.get("APIFY_API_TOKEN")
    if not token: return []
    logger.info(f"Hitting Apify for Social Monitoring (IG: {ig})")
    try:
        client = ApifyClient(token)
        def _fetch():
            return [] # Placeholder as specific URLs were missing in logs
        return await asyncio.to_thread(_fetch)
    except Exception as e:
        logger.error(f"Apify Social failed: {e}")
        return []

async def scrape_site(url, ig):
    logger.info(f"Scraping site: {url} for IG: {ig}")
    try:
        res = await extract_text(url)
        title = res.get('title_fallback') or url
        return [RawItem(title=title, url=url, text=res.get('text', ''), ig=ig, source="site")]
    except Exception as e:
        logger.error(f"Site failure {url}: {e}")
        return []

async def run_scraper(ig_filter=None):
    """Main entry point to scrape all sources."""
    cfg = load_config()
    sources = cfg.get("sources", {})
    groups = cfg.get("interest_groups", {})
    settings = cfg.get("pipeline", {})
    
    sem = asyncio.Semaphore(settings.get("max_concurrent_scrapers", 3))
    
    async def _limited_scrape(coro):
        async with sem:
            return await coro
            
    tasks = []
    for ig_name, ig_cfg in groups.items():
        if ig_filter and ig_name != ig_filter: continue
        if not ig_cfg.get("active", True): continue
            
        # Specialized
        tasks.append(_limited_scrape(scrape_unstop(ig_name)))
        tasks.append(_limited_scrape(scrape_devfolio(ig_name)))
        tasks.append(_limited_scrape(scrape_devpost(ig_name)))
        tasks.append(_limited_scrape(scrape_hackerearth(ig_name)))
        tasks.append(_limited_scrape(scrape_newsapi(ig_name)))
        tasks.append(_limited_scrape(scrape_social(ig_name)))
        
        # Sources from config.yaml
        ig_sources = sources.get("interest_groups", {}).get(ig_name, {})
        global_sources = sources.get("global", {})
        
        for rss in global_sources.get("rss", []) + ig_sources.get("rss", []):
            tasks.append(_limited_scrape(scrape_rss(rss["url"], ig_name)))
        for search in global_sources.get("search", []) + ig_sources.get("search", []):
            tasks.append(_limited_scrape(scrape_search(search["query"], ig_name)))
        for site in ig_sources.get("sites", []):
            tasks.append(_limited_scrape(scrape_site(site["url"], ig_name)))
            
    results = await asyncio.gather(*tasks)
    all_items = [item for sublist in results for item in sublist]
    logger.info(f"Scraper Root: Found {len(all_items)} raw items")
    return all_items
