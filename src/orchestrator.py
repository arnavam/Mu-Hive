import asyncio
import sys
import os
from loguru import logger

from src.scraping.scraper import run_scraper
from src.agents.classifier import run_classifier
from src.agents.validater import run_validater
from src.agents.summarizer import run_summarizer
from src.db.database import run_outputs
from src.config import load_config

async def run_pipeline(ig_filter=None):
    """
    Coordinates the multi-agent pipeline flow.
    """
    logger.info("Starting MuHive Agentic Pipeline...")

    try:
        # Step 1: Scrape Raw Data
        raw_items = await run_scraper(ig_filter=ig_filter)
        if not raw_items:
            logger.warning("No items found during scraping.")
            return

        # Step 2: Classify and Filter
        filtered_items = run_classifier(raw_items)
        if not filtered_items:
            logger.info("All items filtered out by classifier.")
            return

        # Step 3: Validate (Verify relevance and authenticity)
        verified_entries = await run_validater(filtered_items)
        if not verified_entries:
            logger.info("No items passed validation.")
            return

        # Step 4: Summarize and Structure
        clean_items = await run_summarizer(verified_entries)
        if not clean_items:
            logger.info("No items were successfully structured.")
            return

        # Step 5: Output to configured channels
        run_outputs(clean_items)

        # Print Summary
        print("\n" + "#" * 50)
        print("  MUHIVE PIPELINE SUMMARY")
        print("#" * 50)
        print(f"  Raw Scraped:     {len(raw_items)}")
        print(f"  Filtered:        {len(filtered_items)}")
        print(f"  Verified:        {len(verified_entries)}")
        print(f"  Structured:      {len(clean_items)}")
        print("#" * 50 + "\n")

    except Exception as e:
        logger.exception(f"Pipeline crashed in orchestrator: {e}")
        raise e
