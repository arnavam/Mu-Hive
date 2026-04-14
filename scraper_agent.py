import re
import time
import scrapy
from scrapy.crawler import CrawlerProcess
import trafilatura

from database import Database

import logging
import warnings

# Suppress Scrapy deprecation and other internal warnings
warnings.filterwarnings("ignore")
logging.getLogger('scrapy').propagate = False

SUMMARY_MAX_SENTENCES = 5

class ScraperSpider(scrapy.Spider):
    name = 'scraper_spider'

    def __init__(self, limit=50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = Database()
        self.limit = limit
        self.pending = self.db.find_pending_scrape(limit=self.limit)
        
    def start_requests(self):
        if not self.pending:
            print("No pending events (status 'not processed').")
            return
            
        print(f"Found {len(self.pending)} event(s) to scrape.")
        
        for doc in self.pending:
            doc_id = doc.get("_id")
            link = doc.get("link")
            
            if doc_id is None:
                continue

            if not link or not isinstance(link, str) or not (link.strip().lower().startswith("http://") or link.strip().lower().startswith("https://")):
                print(f"  [Skip] Invalid URL: {link!r}")
                self.db.update_event_scrape(
                    doc_id,
                    status="scrape_failed",
                    scrape_error="Invalid or missing HTTP(S) URL",
                )
                continue
            
            print(f"Scraping: {link}")
            yield scrapy.Request(
                url=link, 
                callback=self.parse, 
                errback=self.errback, 
                cb_kwargs={'doc_id': doc_id}
            )

    def parse(self, response, doc_id):
        try:
            # Extract basic metadata via Scrapy CSS/XPath selectors
            scraped_page_title = response.css('title::text').get()
            if not scraped_page_title:
                scraped_page_title = response.xpath('//meta[@property="og:title"]/@content').get()
                
            scraped_meta_description = response.xpath('//meta[@name="description"]/@content').get()
            if not scraped_meta_description:
                scraped_meta_description = response.xpath('//meta[@property="og:description"]/@content').get()

            # Extract main text block using Trafilatura
            html = response.text
            text = trafilatura.extract(html, include_links=False, include_images=False, include_tables=False)
            
            summary = ""
            if text:
                # Basic summarization: take the first 4-5 sentences
                sentences = re.split(r'(?<=[.!?])\s+', text)
                summary_sentences = [s.strip() for s in sentences if s.strip()]
                # Keep up to SUMMARY_MAX_SENTENCES
                summary_sentences = summary_sentences[:SUMMARY_MAX_SENTENCES]
                summary = " ".join(summary_sentences)
            
            # Persist to database
            ok = self.db.update_event_scrape(
                doc_id,
                status="scraped",
                scraped_page_title=scraped_page_title,
                scraped_meta_description=scraped_meta_description,
                scraped_text_summary=summary or None,
            )
            if ok:
                print(f"  [Success] Scraped cleanly: {response.url}")
            else:
                print(f"  [Warning] MongoDB update matched no document for {response.url}")
                
        except Exception as e:
            print(f"  [Error] Failed to parse {response.url}: {e}")
            self.db.update_event_scrape(
                doc_id,
                status="scrape_failed",
                scrape_error=str(e)[:500],
            )
            
    def errback(self, failure):
        request = failure.request
        doc_id = request.cb_kwargs.get('doc_id')
        print(f"  [Error] Failed to fetch {request.url}: {failure.value.__class__.__name__}")
        if doc_id:
            self.db.update_event_scrape(
                doc_id,
                status="scrape_failed",
                scrape_error=str(failure.value)[:500],
            )
            
    def closed(self, reason):
        self.db.close()

def run_scraper_agent(limit=50, delay_seconds=1.0):
    """
    Process events with status 'not processed': scrape each link and persist
    structured fields using Scrapy and Trafilatura.
    """
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting scraper agent...")
    
    # Configure Scrapy process
    process = CrawlerProcess(settings={
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "LOG_LEVEL": "ERROR", # Silence all the verbose info and stats
        "DOWNLOAD_DELAY": delay_seconds,
        "DOWNLOAD_TIMEOUT": 20,
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 4, # Adjust based on preference
    })
    
    process.crawl(ScraperSpider, limit=limit)
    process.start() # This blocks until scraping is finished
    
    print("Scraper agent finished.")

def main():
    run_scraper_agent()

if __name__ == "__main__":
    main()
