import asyncio
import feedparser
import logging
import time
import os
from bs4 import BeautifulSoup
from readability import Document
import httpx
import trafilatura
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import requests
from duckduckgo_search import DDGS

from src.db.database import Database
from src.config.sources import ALL_RSS_FEEDS

logger = logging.getLogger(__name__)

# --- Config for Scraper ---
MIN_WORDS    = 120
SCRAPE_LIMIT = 50
TIMEOUT      = 30
PW_WAIT_MS   = 4000
USER_AGENT   = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"

try:
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, module='newspaper')
    from newspaper import Article as NArticle
    HAS_NEWSPAPER = True
except ImportError:
    HAS_NEWSPAPER = False

def clean_html(html_content):
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator=' ', strip=True)

def run_rss_scout(db: Database):
    logger.info("Running RSS Scout...")
    new_count = 0
    for ig, feeds in ALL_RSS_FEEDS.items():
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                if not feed.entries:
                    continue
                for entry in feed.entries[:5]:
                    title = entry.get("title", "").strip()
                    link = entry.get("link", "").strip()
                    summary_raw = entry.get("summary", "")
                    if not summary_raw and "content" in entry:
                        summary_raw = entry.content[0].value
                    summary = clean_html(summary_raw)
                    
                    if title and link:
                        if db.insert_opportunity(title, link, summary, source_engine="RSS", ig_tags=[ig]):
                            new_count += 1
            except Exception as e:
                logger.error(f"RSS error on {feed_url}: {e}")
    logger.info(f"RSS Scout inserted {new_count} new opportunities.")

def get_tavily_results(query, max_results=3):
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key: return []
    try:
        response = requests.post("https://api.tavily.com/search", json={
            "query": query, "search_depth": "advanced", "max_results": max_results
        }, headers={"Authorization": f"Bearer {api_key}"}, timeout=15)
        return response.json().get('results', [])[:max_results]
    except:
        return []

def run_search_agent(db: Database):
    logger.info("Running Search Engine Agent...")
    keywords = list(ALL_RSS_FEEDS.keys())
    categories = ["news", "events", "hackathons", "internships", "workshops"]
    
    ddgs = DDGS()
    SPAM_DOMAINS = ["bloguerosa.com", "qodsblog.com", "blogdeazar.com", "youtube.com", "facebook.com", "instagram.com", "tiktok.com"]
    new_count = 0

    for keyword in keywords:
        for category in categories:
            query = f"{keyword} {category}"
            try:
                try:
                    results = list(ddgs.text(query, max_results=3, safesearch='moderate', timelimit='y'))
                    source = 'DuckDuckGo'
                except Exception:
                    results = get_tavily_results(query, 3)
                    source = 'Tavily'
                    
                if not results: continue

                for result in results:
                    title = result.get('title', 'No Title')
                    link = result.get('href', result.get('url', ''))
                    if not link: continue
                    if any(spam in link for spam in SPAM_DOMAINS) or link.endswith(('.xyz', '.info')):
                        continue
                    if db.insert_opportunity(title, link, source_engine=source, ig_tags=[keyword]):
                        new_count += 1
            except Exception as e:
                logger.warning(f"Error searching '{query}': {e}")
            time.sleep(1)
    logger.info(f"Search Engine inserted {new_count} new opportunities.")

def extract(html: str) -> str:
    candidates = []
    t = trafilatura.extract(html, include_tables=True, favor_recall=True)
    candidates.append(t or "")
    try:
        soup = BeautifulSoup(Document(html).summary(), "lxml")
        candidates.append(soup.get_text(" ", strip=True))
    except Exception: pass
    if HAS_NEWSPAPER:
        try:
            art = NArticle(""); art.set_html(html); art.parse()
            candidates.append(art.text or "")
        except Exception: pass
    return max(candidates, key=lambda t: len(t.split()), default="")

async def l1_httpx(url: str):
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT}) as c:
            r = await c.get(url)
            r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        title = soup.title.string if soup.title else ""
        meta = soup.find("meta", attrs={"name": "description"})
        meta = meta["content"] if meta else ""
        text = extract(r.text)
        return (text, title, meta) if len(text.split()) >= MIN_WORDS else None
    except Exception as e:
        return None

async def l2_playwright(url: str, browser):
    try:
        page = await (await browser.new_context(user_agent=USER_AGENT)).new_page()
        await Stealth().apply_stealth_async(page)
        await page.goto(url, timeout=TIMEOUT * 1000, wait_until="domcontentloaded")
        await page.wait_for_timeout(PW_WAIT_MS)
        html = await page.content()
        title = await page.title()
        try:
            meta = await page.evaluate('document.querySelector("meta[name=\'description\']")?.content || ""')
        except:
            meta = ""
        await page.close()
        text = extract(html)
        return (text, title, meta) if len(text.split()) >= MIN_WORDS else None
    except Exception as e:
        return None

async def run_scraper_agent(db: Database):
    logger.info("Running Scraper Layer...")
    pending = db.find_pending_scrape(limit=SCRAPE_LIMIT)
    if not pending:
        logger.info("No items pending scrape.")
        return

    logger.info(f"{len(pending)} items pending scrape.")
    semaphore = asyncio.Semaphore(5)
    
    async def scrape_one(doc, browser):
        async with semaphore:
            doc_id, link = doc["_id"], doc.get("link")
            result = await l1_httpx(link)
            label = "L1"
            if not result:
                result = await l2_playwright(link, browser)
                label = "L2"
                
            if result:
                text, title, meta = result
                db.update_event_scrape(doc_id, status="scraped", scraped_page_title=title, scraped_meta_description=meta, scraped_full_text=text, scrape_layer=label)
            else:
                db.update_event_scrape(doc_id, status="scrape_failed", scrape_error="all layers failed")
                
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        await asyncio.gather(*[scrape_one(doc, browser) for doc in pending])
        await browser.close()
    logger.info("Scraper Layer finished.")

async def run_scout_async():
    db = Database()
    run_rss_scout(db)
    run_search_agent(db)
    await run_scraper_agent(db)
    db.close()

def run_scout():
    asyncio.run(run_scout_async())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_scout()
