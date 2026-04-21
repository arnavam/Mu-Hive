import asyncio
import sys
import os
from loguru import logger
import src.stage_01_scraper as scraper
import src.stage_02_filter as filter
import src.stage_03_verifier as verifier
import src.stage_04_structurer as structurer
import src.stage_05_writer as output_writer
from src.utils import load_config

async def main():
    # 1. Setup
    logger.remove()
    logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
    
    # Check env vars
    if "TOGETHER_API_KEY" not in os.environ and "GROQ_API_KEY" not in os.environ:
         logger.warning("No primary LLM keys (TOGETHER or GROQ) found in environment!")
    
    if "TAVILY_API_KEY" not in os.environ or not os.environ["TAVILY_API_KEY"]:
         logger.warning("TAVILY_API_KEY missing! Search fallback will be disabled.")

    # Parse args
    ig_filter = None
    if "--ig" in sys.argv:
        idx = sys.argv.index("--ig")
        if idx + 1 < len(sys.argv):
             ig_filter = sys.argv[idx + 1]
             logger.info(f"Filtering for IG: {ig_filter}")

    logger.info("Starting MuHive v1 Pipeline...")

    # 2. Pipeline Execution
    try:
        # Step 1: Scrape
        raw_items = await scraper.run_scraper(ig_filter=ig_filter)
        
        # Step 2: Filter
        filtered_items = filter.run_filter(raw_items)
        
        # Step 3: Verify
        verified_entries = await verifier.run_verifier(filtered_items)
        
        # Step 4: Structure
        clean_items = await structurer.run_structurer(verified_entries)
        
        # Step 5: Output
        output_writer.run_outputs(clean_items)
        
        # 3. Summary
        print("\n" + "#" * 50)
        print("  MUHIVE v1 PIPELINE SUMMARY")
        print("#" * 50)
        print(f"  Raw Scraped:     {len(raw_items)}")
        print(f"  Filtered:        {len(filtered_items)}")
        print(f"  Verified:        {len(verified_entries)}")
        print(f"  Structured:      {len(clean_items)}")
        print("#" * 50 + "\n")
        
    except Exception as e:
        logger.exception(f"Pipeline crashed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
