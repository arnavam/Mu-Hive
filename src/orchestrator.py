import asyncio
from src.agents.scout import scout
from src.agents.intelligence import intelligence
from src.db.database import db

class Orchestrator:
    """
    The main coordinator for the Mu-Hive pipeline.
    It manages the flow of data between different agents and the database.
    """
    
    def _sanitize_url(self, url):
        """Cleans up common URL input errors"""
        if not url:
            return url
        url = url.strip()
        # Fix double protocols like https://https://
        if url.startswith("https://https://"):
            url = url.replace("https://https://", "https://", 1)
        elif url.startswith("http://http://"):
            url = url.replace("http://http://", "http://", 1)
        return url

    async def process_url(self, url, mode='scrape', options=None):
        """Coordinates the end-to-end processing of a single URL"""
        url = self._sanitize_url(url)
        print(f"[*] [Orchestrator] Starting pipeline for: {url}")
        
        try:
            # 1. Scraping (via Scout Agent)
            print(f"[1/4] [Scout] Scraping content using {mode} mode...")
            scraped_data = await asyncio.to_thread(scout.run, mode, url, options)
            
            if not scraped_data:
                print(f"[!] [Scout] No data extracted from {url}")
                return None

            # 2. Database Storage (Initial Raw Save)
            print(f"[2/4] [DB] Storing raw scraped data...")
            record_id = await asyncio.to_thread(db.save_scrape_result, url, scraped_data)

            # 3. Fetch from DB and Analyze Event Structure
            print(f"[3/4] [Intelligence] Fetching data and analyzing event structure...")
            fetched_record = await asyncio.to_thread(db.get_scrape_result, record_id)
            
            # Perform structured analysis
            event_data = await asyncio.to_thread(intelligence.analyze_event, fetched_record['data'])
            
            if event_data:
                # 4. Final Database Storage (Upsert into events table)
                print(f"[4/4] [DB] Upserting structured event into 'events' table...")
                event_data['link'] = url  # Ensure the unique key is present
                await asyncio.to_thread(db.upsert_event, event_data)
            
            # Generate a text summary for the UI (not stored in scraped_data anymore)
            summary = await asyncio.to_thread(intelligence.summarize, fetched_record['data'])

            print(f"[+] [Orchestrator] Successfully processed: {url}")
            return {
                "url": url,
                "summary": summary,
                "event_data": event_data,
                "record_id": record_id
            }

        except Exception as e:
            print(f"[!] [Orchestrator] Error in pipeline for {url}: {str(e)}")
            return {"url": url, "error": str(e)}

    async def run_batch(self, urls, mode='scrape', options=None):
        """Processes multiple URLs concurrently"""
        tasks = [self.process_url(url, mode, options) for url in urls]
        return await asyncio.gather(*tasks)

orchestrator = Orchestrator()
