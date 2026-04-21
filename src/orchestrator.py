import asyncio
from src.agents.scout import scout
from src.agents.intelligence import intelligence
from src.db.database import db

class Orchestrator:
    """
    The main coordinator for the Mu-Hive pipeline.
    It manages the flow of data between different agents and the database.
    """
    
    async def process_url(self, url, mode='scrape', options=None):
        """Coordinates the end-to-end processing of a single URL"""
        print(f"[*] [Orchestrator] Starting pipeline for: {url}")
        
        try:
            # 1. Scraping (via Scout Agent)
            print(f"[1/3] [Scout] Scraping content using {mode} mode...")
            scraped_data = await asyncio.to_thread(scout.run, mode, url, options)
            
            if not scraped_data:
                print(f"[!] [Scout] No data extracted from {url}")
                return None

            # 2. Intelligence / Summarization (via Intelligence Agent)
            print(f"[2/3] [Intelligence] Analyzing content with AI...")
            summary = await asyncio.to_thread(intelligence.summarize, scraped_data)

            # 3. Database Storage
            print(f"[3/3] [DB] Saving result to database...")
            # We use a thread since pymongo is blocking
            await asyncio.to_thread(db.save_scrape_result, url, scraped_data, summary)

            print(f"[+] [Orchestrator] Successfully processed: {url}")
            return {
                "url": url,
                "summary": summary,
                "data": scraped_data
            }

        except Exception as e:
            print(f"[!] [Orchestrator] Error in pipeline for {url}: {str(e)}")
            return {"url": url, "error": str(e)}

    async def run_batch(self, urls, mode='scrape', options=None):
        """Processes multiple URLs concurrently"""
        tasks = [self.process_url(url, mode, options) for url in urls]
        return await asyncio.gather(*tasks)

orchestrator = Orchestrator()
