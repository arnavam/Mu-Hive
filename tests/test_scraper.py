"""
tests/test_scraper.py
=====================
Test file to independently run and verify the scraper pipeline.
Run with: python -m tests.test_scraper
"""

import asyncio
from src.scraping.scraper import run_scraper_pipeline

def _print_results(grouped):
    print("\n" + "═" * 70)
    print("  🚀  Scraper Pipeline Data")
    print("═" * 70)

    active_count = 0
    total_events = 0

    for ig, events in grouped.items():
        if not events:
            continue
            
        active_count += 1
        total_events += len(events)
        
        print(f"\n{'─'*70}")
        print(f"  📌  {ig}  ({len(events)} events)")
        print(f"{'─'*70}")
        
        for i, event in enumerate(events, 1):
            title = event.eventName
            days  = event.days_remaining or 0
            plat  = event.platform or "Unknown"
            link  = event.registrationLink
            loc   = event.location or "Online"
            
            print(f"\n  {i}. {title}")
            print(f"     {days}d left │ {plat} │ {loc}")
            print(f"     🔗 {link}")

    print(f"\n{'═'*70}")
    print(f"  ✅  {active_count} IGs active  │  {total_events} Pydantic event objects")
    print(f"{'═'*70}\n")

async def main():
    print("[Test Scraper] Launching pipeline...")
    grouped = await run_scraper_pipeline()
    _print_results(grouped)

if __name__ == "__main__":
    asyncio.run(main())
