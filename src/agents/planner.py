import asyncio
from src.agents.scout import firecrawl_scraper
from src.agents.intelligence import intelligence
from src.db.database import db

class PlannerAgent:
    """
    Orchestrates the Mu-Hive pipeline:
    1. Scrape data from a URL
    2. Analyze and summarize the data
    3. Save the result to the database
    """
    
    async def process_url(self, url, mode='scrape', options=None):
        print(f"[*] Starting pipeline for: {url}")
        
        try:
            # 1. Scraping
            print(f"[1/3] Scraping content using {mode} mode...")
            scraped_data = await asyncio.to_thread(firecrawl_scraper, url, mode, options)
            
            if not scraped_data:
                print(f"[!] No data extracted from {url}")
                return None

            # 2. Intelligence / Summarization
            print(f"[2/3] Analyzing content with AI...")
            summary = await asyncio.to_thread(intelligence.summarize, scraped_data)

            # 3. Database Storage
            print(f"[3/3] Saving result to database...")
            # We use a thread since pymongo is blocking
            await asyncio.to_thread(db.save_scrape_result, url, mode, scraped_data, summary)

            print(f"[+] Successfully processed: {url}")
            return {
                "url": url,
                "summary": summary,
                "data": scraped_data
            }

        except Exception as e:
            print(f"[!] Error in pipeline for {url}: {str(e)}")
            return {"url": url, "error": str(e)}

    async def run_batch(self, urls, mode='scrape', options=None):
        """Processes multiple URLs concurrently"""
        tasks = [self.process_url(url, mode, options) for url in urls]
        return await asyncio.gather(*tasks)

planner = PlannerAgent()
