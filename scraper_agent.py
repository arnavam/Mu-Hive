import asyncio, base64, os, time
import httpx, trafilatura
from bs4 import BeautifulSoup
from readability import Document
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from database import Database
from dotenv import load_dotenv

load_dotenv()
 
try:
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, module='newspaper')
    from newspaper import Article as NArticle
    HAS_NEWSPAPER = True
except ImportError:
    HAS_NEWSPAPER = False
 
# ── Config ────────────────────────────────────────────────────────────────────
MIN_WORDS    = 120
SCRAPE_LIMIT = 50
TIMEOUT      = 30   # seconds
PW_WAIT_MS   = 4000    # ms to wait after page load for JS
MAX_IMAGES   = 5       # max images extracted (URLs only)
USER_AGENT   = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36")
 
 
# ── Text extraction ───────────────────────────────────────────────────────────
def extract(html: str) -> str:
    """Run all extractors on HTML, return the longest result."""
    candidates = []
 
    t = trafilatura.extract(html, include_tables=True, favor_recall=True)
    candidates.append(t or "")
 
    try:
        soup = BeautifulSoup(Document(html).summary(), "lxml")
        candidates.append(soup.get_text(" ", strip=True))
    except Exception:
        pass
 
    if HAS_NEWSPAPER:
        try:
            art = NArticle(""); art.set_html(html); art.parse()
            candidates.append(art.text or "")
        except Exception:
            pass
 
    return max(candidates, key=lambda t: len(t.split()), default="")
 
 
# ── Layer 1: plain HTTP ───────────────────────────────────────────────────────
async def l1_httpx(url: str) -> tuple | None:
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=TIMEOUT,
                                     headers={"User-Agent": USER_AGENT}) as c:
            r = await c.get(url)
            r.raise_for_status()
 
        soup     = BeautifulSoup(r.text, "lxml")
        img_urls = [i["src"] for i in soup.find_all("img", src=True)
                    if i["src"].startswith("http")][:MAX_IMAGES]
        text     = extract(r.text)
 
        return (text, "", "", img_urls) if len(text.split()) >= MIN_WORDS else None
    except Exception as e:
        print(f"    [L1] {e}"); return None
 
 
# ── Layer 2: Playwright (JS-rendered pages) ───────────────────────────────────
async def l2_playwright(url: str) -> tuple | None:
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page    = await (await browser.new_context(user_agent=USER_AGENT)).new_page()
            await Stealth().apply_stealth_async(page)
            await page.goto(url, timeout=TIMEOUT * 1000, wait_until="domcontentloaded")
            await page.wait_for_timeout(PW_WAIT_MS)
            try:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)
            except:
                pass
 
            html  = await page.content()
            
            try:
                title = await page.title()
            except:
                title = ""
                
            try:
                meta  = await page.evaluate(
                    'document.querySelector("meta[name=\'description\']")?.content || ""')
            except:
                meta = ""
                
            try:
                imgs  = await page.evaluate(
                    "Array.from(document.images).map(i=>i.src).filter(s=>s.startsWith('http'))")
            except:
                imgs = []
                
            await browser.close()
 
        text = extract(html)
        return (text, title, meta, imgs[:MAX_IMAGES]) if len(text.split()) >= MIN_WORDS else None
    except Exception as e:
        print(f"    [L2] {e}"); return None
 
 
# ── Core scrape (reusable) ────────────────────────────────────────────────────
async def scrape_url(url: str) -> dict | None:
    """
    Scrape a URL, returning full text.
    Returns dict with keys: text, page_title, meta_description, layer
    or None if both layers fail.
 
    Usage from another agent:
        from scraper_agent import scrape_url
        result = await scrape_url("https://example.com")
    """
    for label, fn in [("L1", l1_httpx), ("L2", l2_playwright)]:
        print(f"  [{label}] trying...")
        result = await fn(url)
        if not result:
            continue
 
        text, title, meta, imgs = result
        print(f"  [{label}] ✓ {len(text.split())} words")
 
        return {"text": text, "page_title": title, "meta_description": meta, "layer": label}
 
    print("  [FAIL] both layers failed")
    return None
 
 
# ── Agent entry point ─────────────────────────────────────────────────────────
async def run_scraper_agent(limit: int = SCRAPE_LIMIT):
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] scraper starting...")
    db      = Database()
    pending = db.find_pending_scrape(limit=limit)
 
    if not pending:
        print("nothing to scrape."); db.close(); return
 
    print(f"{len(pending)} doc(s) queued.")
 
    for doc in pending:
        doc_id, link = doc["_id"], doc.get("link")
        print(f"\n── {link}")
 
        if not (isinstance(link, str) and link.startswith(("http://", "https://"))):
            db.update_event_scrape(doc_id, status="scrape_failed",
                                   scrape_error="invalid URL")
            continue
            
        SPAM_DOMAINS = ["bloguerosa.com", "qodsblog.com", "blogdeazar.com", "blazingblog.com"]
        if any(spam in link for spam in SPAM_DOMAINS):
            print("  [Skip] Spam domain filtered.")
            db.update_event_scrape(doc_id, status="scrape_failed", scrape_error="spam domain")
            continue
 
        result = await scrape_url(link)
 
        if not result:
            db.update_event_scrape(doc_id, status="scrape_failed",
                                   scrape_error="all layers failed")
            continue
 
        ok = db.update_event_scrape(
            doc_id,
            status="scraped",
            scraped_page_title=result["page_title"],
            scraped_meta_description=result["meta_description"],
            scraped_full_text=result["text"],
            scrape_layer=result["layer"],
        )
        print(f"  [{'saved' if ok else 'warn: no match'}] "
              f"layer={result['layer']} words={len(result['text'].split())}")
 
    db.close()
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] scraper done.")
 
 
if __name__ == "__main__":
    asyncio.run(run_scraper_agent())