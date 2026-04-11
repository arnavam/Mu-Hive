import feedparser
import logging
import sqlite3
from bs4 import BeautifulSoup
from src.db.database import get_connection
from src.config.sources import AI_RSS_FEEDS

logger = logging.getLogger(__name__)

def clean_html(html_content):
    """Strip HTML tags from RSS summaries"""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator=' ', strip=True)

def run_scout():
    logger.info("Initializing Scout Agent...")
    conn = get_connection()
    cursor = conn.cursor()
    new_articles_count = 0

    for feed_url in AI_RSS_FEEDS:
        logger.info(f"Parsing feed: {feed_url}")
        try:
            feed = feedparser.parse(feed_url)
            
            # If feed fails to fetch or parse properly, feed.entries might be empty
            if not feed.entries:
                logger.warning(f"No entries found or failed to parse: {feed_url}")
                continue

            # Limit to recent 10 entries per feed to avoid blasting the DB in one go
            for entry in feed.entries[:10]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                
                # Extraction logic for summary, which varies by feed
                summary_raw = entry.get("summary", "")
                if not summary_raw and "content" in entry:
                    summary_raw = entry.content[0].value
                
                summary = clean_html(summary_raw)
                
                if not title or not link:
                    continue
                    
                # Insert heavily relying on UNIQUE constraint to avoid duplicates
                try:
                    cursor.execute('''
                        INSERT INTO opportunities (title, summary, link, ig_tags)
                        VALUES (?, ?, ?, ?)
                    ''', (title, summary, link, '["AI"]'))
                    new_articles_count += 1
                except sqlite3.IntegrityError:
                    # Link already exists, duplicate tracking prevented
                    pass
        except Exception as e:
            logger.error(f"Error connecting to or parsing {feed_url}: {e}")

    conn.commit()
    conn.close()
    logger.info(f"Scout Agent finished. Inserted {new_articles_count} new distinct AI opportunities.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_scout()
