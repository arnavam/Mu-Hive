import random
import asyncio
import feedparser
import httpx
import trafilatura
import os
from bs4 import BeautifulSoup
from loguru import logger
from ddgs import DDGS
from newsapi import NewsApiClient
from apify_client import ApifyClient
from ..schemas import RawItem
from ..config import load_config
from ..http_utils import get_random_ua
from ..retry import with_retry
from aiolimiter import AsyncLimiter
import warnings
from bs4 import XMLParsedAsHTMLWarning

# Hide the annoying BS4 warning about XML being parsed as HTML
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Shared URLs for specialized scrapers (from Joshna's branch)
UNSTOP_API = "https://unstop.com/api/public/opportunity/search-result"
DEVFOLIO_API = "https://api.devfolio.co/api/hackathons/explore"
DEVPOST_API = "https://devpost.com/api/hackathons"
HACKEREARTH_API = "https://www.hackerearth.com/chrome-extension/events/"

# Shared search limiter to ensure rate limits are respected across all Interest Groups
# We initialize it lazily to avoid loading config at import time
_SEARCH_LIMITER = None

def get_search_limiter():
    global _SEARCH_LIMITER
    if _SEARCH_LIMITER is None:
        settings = load_config("settings")["pipeline"]
        _SEARCH_LIMITER = AsyncLimiter(settings["search_rpm"], 60)
    return _SEARCH_LIMITER

# Extracts clean text and metadata from a URL
@with_retry
async def _extract_text(url):
    headers = {
        "User-Agent": get_random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }
    
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers=headers) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            
            # Technique from Sruthi: Explicit Meta-tag extraction
            soup = BeautifulSoup(resp.content, "lxml")
            
            # Cleanup non-content tags before trafilatura (Sruthi's technique)
            for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
                tag.decompose()
            
            cleaned_html = str(soup)
            text = trafilatura.extract(cleaned_html)
            
            # Fallback metadata if trafilatura missed it
            # Explicitly using attrs dict to avoid 'multiple values for argument name' errors
            page_title = soup.find("meta", attrs={"property": "og:title"}) or \
                         soup.find("meta", attrs={"name": "twitter:title"}) or \
                         soup.find("meta", attrs={"name": "title"})
            title_text = page_title["content"] if page_title else (soup.title.string if soup.title else "")
            
            return {
                "text": text or "",
                "title_fallback": title_text.strip() if title_text else None
            }
            
    except Exception as e:
        if "brotli" in str(e).lower() or "decode" in str(e).lower():
            logger.debug(f"Retrying {url} with plain encoding...")
            headers["Accept-Encoding"] = "identity"
            async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers=headers) as client:
                resp = await client.get(url)
                text = trafilatura.extract(resp.text)
                return {"text": text or "", "title_fallback": None}
        raise e

# Scrapes a single RSS feed and returns RawItems
async def _scrape_rss(feed_url, ig):
    logger.info(f"Scraping RSS: {feed_url} for IG: {ig}")
    items = []
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:10]:
            try:
                if not hasattr(entry, 'link'): continue
                
                # Technique from Zaim: Robust content extraction
                desc = entry.get('summary', '')
                if not desc and 'content' in entry:
                    desc = entry.content[0].value
                
                res = await _extract_text(entry.link)
                title = entry.get('title', res.get('title_fallback', 'No Title'))
                
                # If trafilatura failed, use the RSS summary as text
                final_text = res.get('text') or BeautifulSoup(desc, "lxml").get_text()
                
                items.append(RawItem(title=title, url=entry.link, text=final_text, ig=ig, source="rss"))
            except Exception as e:
                logger.debug(f"RSS item failed {entry.link}: {e}")
    except Exception as e:
        logger.error(f"RSS failure {feed_url}: {e}")
    return items

# Technique from Sruthi/Johan: Tavily Search
async def _scrape_tavily(query, max_results=5):
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

# Scrapes a single search query and returns RawItems
async def _scrape_search(query, ig):
    logger.info(f"Searching query: {query} for IG: {ig}")
    items = []
    
    search_limiter = get_search_limiter()
    
    try:
        results = []
        async with search_limiter:
            # Try DuckDuckGo first (Primary)
            try:
                results = await asyncio.to_thread(lambda: list(DDGS().text(query, max_results=5)))
            except Exception as e:
                logger.warning(f"DuckDuckGo failed: {e}. Falling back to Tavily.")
            
            # Fallback to Tavily only if DDG failed or returned nothing
            if not results:
                tav_results = await _scrape_tavily(query)
                for r in tav_results:
                    results.append({'title': r.get('title'), 'href': r.get('url'), 'body': r.get('content')})

        if not results:
            logger.debug(f"No results for search '{query}'")

        for res in results:
            try:
                url = res.get('href')
                if not url: continue
                res_data = await _extract_text(url)
                title = res.get('title', res_data.get('title_fallback', 'No Title'))
                items.append(RawItem(title=title, url=url, text=res_data.get('text', ''), ig=ig, source="search"))
                
                # Small jitter to mimic human behavior (Stealth technique)
                await asyncio.sleep(random.uniform(0.5, 1.5))
            except Exception as e:
                logger.debug(f"Search item failed {url}: {e}")
                
    except Exception as e:
        logger.error(f"Search failure for '{query}': {e}")
    return items

# Specialized Scrapers (Technique from Joshna)

async def _scrape_unstop(ig):
    """Hits Unstop private API for hackathons"""
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
                    
                    # Fix: SEO URL might already be a full link or just a slug
                    if seo:
                        if seo.startswith("http"):
                            link = seo
                        else:
                            link = f"https://unstop.com/hackathons/{seo}"
                    else:
                        link = ""
                    # Direct API hits are rich, we could extract more, but sticking to RawItem schema
                    items.append(RawItem(title=title, url=link, text=f"Unstop Hackathon: {title}", ig=ig, source="unstop"))
    except Exception as e:
        logger.error(f"Unstop API failed: {e}")
    return items

async def _scrape_devfolio(ig):
    """Hits Devfolio Elasticsearch endpoint"""
    logger.info(f"Hitting Devfolio API for IG: {ig}")
    items = []
    try:
        # Simplified query for Devfolio
        payload = {"from": 0, "size": 15, "query": {"match_all": {}}}
        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": get_random_ua()}) as client:
            resp = await client.post("https://api.devfolio.co/api/hackathons/explore", json=payload)
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

async def _scrape_devpost(ig):
    """Hits Devpost API"""
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

async def _scrape_hackerearth(ig):
    """Hits HackerEarth API"""
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

# Scrapes high-quality tech news via NewsAPI (Adhi-Narayan's technique)
async def _scrape_newsapi(ig):
    key = os.environ.get("NEWSAPI_KEY")
    if not key:
        return []
        
    logger.info(f"Hitting NewsAPI for IG: {ig}")
    try:
        # We run this in a thread because the newsapi client is synchronous
        def _fetch():
            client = NewsApiClient(api_key=key)
            # Map IG to common tech domains
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

# Scrapes social media profiles via Apify (Conversations 5/6 technique)
async def _scrape_social(ig):
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        return []
        
    logger.info(f"Hitting Apify for Social Monitoring (IG: {ig})")
    try:
        client = ApifyClient(token)
        # For v1, we use a generic LinkedIn profile detail actor
        # Example actor: 'apimaestro/linkedin-profile-detail'
        def _fetch():
            # This is a template logic - actual URLs would come from config
            # Here we simulate the logic discussed in history
            return [] # Placeholder as specific URLs were missing in logs
            
        return await asyncio.to_thread(_fetch)
    except Exception as e:
        logger.error(f"Apify Social failed: {e}")
        return []

# Scrapes a single site and returns RawItem
async def _scrape_site(url, ig):
    logger.info(f"Scraping site: {url} for IG: {ig}")
    try:
        res = await _extract_text(url)
        title = res.get('title_fallback') or url
        return [RawItem(title=title, url=url, text=res.get('text', ''), ig=ig, source="site")]
    except Exception as e:
        logger.error(f"Site failure {url}: {e}")
        return []

# Combines all sources for an IG and scrapes concurrently
async def run_scraper(ig_filter=None):
    sources = load_config("sources")
    groups = load_config("groups")["interest_groups"]
    settings = load_config("settings")["pipeline"]
    
    sem = asyncio.Semaphore(settings["max_concurrent_scrapers"])
    
    async def _limited_scrape(coro):
        async with sem:
            return await coro
            
    tasks = []
    
    for ig_name, ig_cfg in groups.items():
        if ig_filter and ig_name != ig_filter:
            continue
        if not ig_cfg.get("active", True):
            continue
            
        # Technique from Joshna: Always hit specialized platforms for active groups
        # (Alternatively, these could be added to sources.yaml, but auto-hitting them is powerful)
        tasks.append(_limited_scrape(_scrape_unstop(ig_name)))
        tasks.append(_limited_scrape(_scrape_devfolio(ig_name)))
        tasks.append(_limited_scrape(_scrape_devpost(ig_name)))
        tasks.append(_limited_scrape(_scrape_hackerearth(ig_name)))
        
        # New: Holistic NewsAPI and Social monitoring
        tasks.append(_limited_scrape(_scrape_newsapi(ig_name)))
        tasks.append(_limited_scrape(_scrape_social(ig_name)))
        
        # Global sources
        global_rss = sources.get("global", {}).get("rss", [])
        global_search = sources.get("global", {}).get("search", [])
        
        # Local sources
        local_rss = sources["interest_groups"].get(ig_name, {}).get("rss", [])
        local_search = sources["interest_groups"].get(ig_name, {}).get("search", [])
        local_sites = sources["interest_groups"].get(ig_name, {}).get("sites", [])
        
        for rss in global_rss + local_rss:
            tasks.append(_limited_scrape(_scrape_rss(rss["url"], ig_name)))
        for search in global_search + local_search:
            tasks.append(_limited_scrape(_scrape_search(search["query"], ig_name)))
        for site in local_sites:
            tasks.append(_limited_scrape(_scrape_site(site["url"], ig_name)))
            
    results = await asyncio.gather(*tasks)
    all_items = [item for sublist in results for item in sublist]
    
    logger.info(f"Scraper: Found {len(all_items)} raw items")
    return all_items
