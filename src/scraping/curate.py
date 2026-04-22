import httpx
import trafilatura
from bs4 import BeautifulSoup
from loguru import logger
import warnings
from bs4 import XMLParsedAsHTMLWarning
from src.http_utils import get_random_ua
from src.retry import with_retry

# Hide the annoying BS4 warning about XML being parsed as HTML
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

@with_retry
async def extract_text(url):
    """Extracts clean text and metadata from a URL."""
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
            
            soup = BeautifulSoup(resp.content, "lxml")
            
            # Cleanup non-content tags before trafilatura
            for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
                tag.decompose()
            
            cleaned_html = str(soup)
            text = trafilatura.extract(cleaned_html)
            
            # Fallback metadata if trafilatura missed it
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
