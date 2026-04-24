#!/usr/bin/env python3
"""
scripts/zulip_notify.py
================-------
Final, Robust Mu-Hive Pipeline.
Includes improved AI instructions to prevent schema 'echoing' and 
increased delays for rate-limit safety.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fix path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# MODULE SHIM: Protect against missing Database module
mock_db = MagicMock()
mock_db.Database = MagicMock
sys.modules["src.db.database"] = mock_db

from src.scraping.scraper import fetch_all_events, fetch_all_news
from src.scraping.data_cleaner import clean_events
from src.scraping.curate import curate
from src.config.constants import IG_KEYWORDS
from src.agents.intelligence import OpportunityIntelligence
from src.agents.summarizer import SummaryOutput
from src.llm import make_llm_client
from zulip_writer import ZulipWriter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_zulip_credentials(ig_name: str) -> dict:
    """Retrieves Zulip credentials from environment variables."""
    slug = ig_name.lower().replace(" ", "_").upper()
    email = os.getenv(f"ZULIP_{slug}_EMAIL")
    key = os.getenv(f"ZULIP_{slug}_KEY")
    site = os.getenv(f"ZULIP_{slug}_SITE", "https://mulearn.zulipchat.com/")
    
    if email and key:
        return {"email": email, "api_key": key, "site": site}
    return None

CHANNEL_MAP = {
    "Ai": "AI IG",
    "Cyber Security": "Cyber Security IG",
    "Web Development": "Web Dev IG"
}


def is_hackathon(ev: dict) -> bool:
    etype = str(ev.get('_event_type', ev.get('eventType', ''))).lower()
    cat = str(ev.get('category', '')).lower()
    return 'hackathon' in etype or 'hackathon' in cat

def format_date(date_str: str) -> str:
    if not date_str or date_str.lower() == "tba":
        return "TBA"
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%B %d, %Y")
    except:
        return date_str

async def process_with_advanced_llm(item: dict, ig_name: str, client) -> tuple[bool, str]:
    title = item.get('eventName', 'Unknown')
    tags = item.get('tags', [])
    summary_text = item.get('summary', '')
    content = f"Tags: {tags}\nSummary: {summary_text}"
    
    try:
        # Step 1: Intelligence
        intel = client.create(OpportunityIntelligence, [
            {"role": "system", "content": "You are a Mu-Hive intelligence grader. Analyze the provided opportunity and return its quality and relevance."},
            {"role": "user", "content": f"Opportunity: {title}\nTags: {content}\nIG: {ig_name}\n\nTask: Evaluate this and fill in the JSON fields."}
        ])
        if not intel.is_relevant or intel.quality_score < 4:
            return False, ""
        
        # Step 2: Summarization
        res = client.create(SummaryOutput, [
            {"role": "system", "content": "You are a lead tech writer for Mu-Hive. Write a short, engaging description."},
            {"role": "user", "content": f"Write a 1-sentence summary of '{title}' for the {ig_name} group. Focus on value to students."}
        ])
        return True, res.summary
    except Exception as e:
        logger.debug(f"AI Eval failed for {title[:20]}: {e}")
        return False, ""

async def main():
    logger.info("🌊 Starting Unified Robust Mu-Hive Pipeline...")
    client = make_llm_client(role="intelligence", tier="cheap")
    if not client:
        return

    # 1. Fetch from all sources
    logger.info("📡 Fetching Hackathons and RSS News...")
    events_task = fetch_all_events()
    news_task = fetch_all_news()
    
    raw_events, raw_news = await asyncio.gather(events_task, news_task)
    
    all_raw = raw_events + raw_news
    logger.info(f"📥 Found {len(raw_events)} events and {len(raw_news)} news items.")

    primary, extended = clean_events(all_raw)
    grouped_events = curate(primary, extended, IG_KEYWORDS)
    
    for ig_name, zulip_channel in CHANNEL_MAP.items():
        creds = get_zulip_credentials(ig_name)
        if not creds:
            logger.warning(f"⚠️ No credentials found in .env for {ig_name}. Skipping...")
            continue
            
        logger.info(f"🤖 Initializing bot for {ig_name} using environment variables")
        writer = ZulipWriter(email=creds['email'], api_key=creds['api_key'], site=creds['site'])

        items = grouped_events.get(ig_name, [])
        if not items: continue
            
        logger.info(f"✨ Processing {len(items)} items for #{zulip_channel}...")
        hacks_body, news_body, total_found = "", "", 0
        
        for item in items:
            # Multi-threading safety delay
            await asyncio.sleep(2.0)
            
            is_relevant, summary = await process_with_advanced_llm(item, ig_name, client)
            if not is_relevant: continue
                
            is_hack = is_hackathon(item)
            mode = item.get('location', 'Online')
            fmt = f"* **{item.get('eventName')}**\n  *Summary*: {summary}\n  *Link*: [Read More]({item.get('registrationLink')})\n"
            if is_hack:
                fmt = fmt.replace("[Read More]", "[Register Here]")
                fmt += f"  *Mode*: {mode}\n"
                fmt += f"  *Deadline*: {format_date(item.get('endDate', 'TBA'))}\n"
            
            if is_hack: hacks_body += fmt + "\n"
            else: news_body += fmt + "\n"
            total_found += 1

        if not hacks_body and not news_body: continue
            
        logger.info(f"📧 Sending updates to #{zulip_channel}...")

        # 1. Send News Topic
        if news_body:
            news_header = f"## {ig_name} News Digest\n---\n"
            writer.client.send_message({
                "type": "stream",
                "to": zulip_channel,
                "topic": "📰 News & Insights",
                "content": news_header + news_body
            })
        
        # 2. Send Hackathons Topic
        if hacks_body:
            hacks_header = f"## {ig_name} Hackathon Digest\n---\n"
            writer.client.send_message({
                "type": "stream",
                "to": zulip_channel,
                "topic": "🚀 Hackathons",
                "content": hacks_header + hacks_body
            })

        logger.info(f"✅ Notified #{zulip_channel}")

    logger.info("🏁 Pipeline Run Complete.")

if __name__ == "__main__":
    asyncio.run(main())
