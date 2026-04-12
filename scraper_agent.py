import re
import time

import requests
from bs4 import BeautifulSoup

from database import Database

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

SUMMARY_MAX_CHARS = 4000
REQUEST_TIMEOUT = 20


def _meta_content(soup, *keys):
    for key in keys:
        tag = soup.find("meta", attrs={"property": key}) or soup.find(
            "meta", attrs={"name": key}
        )
        if tag and tag.get("content"):
            return tag["content"].strip()
    return None


def _visible_text_summary(soup):
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    for sel in ("nav", "footer", "header", "[role='navigation']"):
        for t in soup.select(sel):
            t.decompose()
    main = soup.find("main") or soup.find("article") or soup.body or soup
    text = main.get_text(separator=" ", strip=True) if main else ""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > SUMMARY_MAX_CHARS:
        text = text[: SUMMARY_MAX_CHARS - 3] + "..."
    return text or None


def scrape_url(url):
    """
    Fetch URL and return dict with page_title, meta_description, text_summary.
    Raises on HTTP/network errors.
    """
    resp = requests.get(
        url,
        headers=DEFAULT_HEADERS,
        timeout=REQUEST_TIMEOUT,
        allow_redirects=True,
    )
    resp.raise_for_status()
    ctype = (resp.headers.get("Content-Type") or "").lower()
    if "text/html" not in ctype and "application/xhtml" not in ctype:
        raise ValueError(f"Not HTML: {ctype!r}")

    soup = BeautifulSoup(resp.content, "lxml")
    page_title = _meta_content(soup, "og:title") or (
        soup.title.get_text(strip=True) if soup.title else None
    )
    meta_description = _meta_content(
        soup, "og:description", "description", "twitter:description"
    )
    text_summary = _visible_text_summary(soup)
    return {
        "scraped_page_title": page_title,
        "scraped_meta_description": meta_description,
        "scraped_text_summary": text_summary,
    }


def _is_scrapable_link(link):
    if not link or not isinstance(link, str):
        return False
    u = link.strip().lower()
    return u.startswith("http://") or u.startswith("https://")


def run_scraper_agent(limit=50, delay_seconds=1.0):
    """
    Process events with status 'not processed': scrape each link and persist
    structured fields on the same MongoDB document.
    """
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting scraper agent...")
    db = Database()
    pending = db.find_pending_scrape(limit=limit)
    if not pending:
        print("No pending events (status 'not processed').")
        db.close()
        return

    print(f"Found {len(pending)} event(s) to scrape.")
    for doc in pending:
        doc_id = doc.get("_id")
        link = doc.get("link")
        if doc_id is None:
            print(f"  Skip (missing _id): {link!r}")
            continue

        if not _is_scrapable_link(link):
            print(f"  Skip (invalid URL): {link!r}")
            db.update_event_scrape(
                doc_id,
                status="scrape_failed",
                scrape_error="Invalid or missing HTTP(S) URL",
            )
            continue

        print(f"  Scraping: {link}")
        try:
            data = scrape_url(link)
            ok = db.update_event_scrape(
                doc_id,
                status="scraped",
                scraped_page_title=data["scraped_page_title"],
                scraped_meta_description=data["scraped_meta_description"],
                scraped_text_summary=data["scraped_text_summary"],
            )
            if ok:
                print("    -> stored: scraped")
            else:
                print("    [!] MongoDB update matched no document")
        except Exception as e:
            print(f"    [!] Failed: {e}")
            db.update_event_scrape(
                doc_id,
                status="scrape_failed",
                scrape_error=str(e)[:500],
            )

        if delay_seconds:
            time.sleep(delay_seconds)

    db.close()
    print("Scraper agent finished.")


def main():
    run_scraper_agent()


if __name__ == "__main__":
    main()
