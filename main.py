"""
main.py
=======
Entry point. Run with: python main.py

Pipeline:
    fetch_all_events()  →  raw list from all platforms
    clean_events()      →  strict URL/location/date/university filtering
    process_events()    →  curated IG → events mapping (30 IGs)
    save_events()       →  written to MongoDB
"""

import sys
import asyncio

from src.scraping.scraper       import fetch_all_events
from src.scraping.data_cleaner  import clean_events
from src.scraping.curate        import curate, MASTER_IGS, IG_KEYWORDS
from src.db.database            import save_events, get_collection


def _render(grouped: dict) -> None:
    print("\n" + "═" * 70)
    print("  🚀  Mu-Hive Hackathon Radar  |  Weekly Top Picks")
    print("═" * 70)

    active_count = 0
    total_events = 0

    for ig in MASTER_IGS:
        events_to_show = grouped.get(ig, [])

        # MuV: hide if empty — never show garbage
        if ig == "MuV" and len(events_to_show) == 0:
            continue

        # Skip any IG with 0 events
        if len(events_to_show) == 0:
            continue

        active_count += 1
        total_events += len(events_to_show)

        # print IG header + events (keep existing format)
        print(f"\n{'─'*70}")
        print(f"  📌  {ig}  ({len(events_to_show)} events)")
        print(f"{'─'*70}")
        for i, event in enumerate(events_to_show, 1):
            title = event.get('eventName', 'Unknown')
            etype = event.get('_event_type', 'Hackathon')
            days  = event.get('days_remaining', 0)
            plat  = event.get('platform', 'Unknown')
            link  = event.get('registrationLink', '')
            loc   = event.get('location', 'Online')
            if any(k in loc.lower() for k in ["online", "virtual", "remote", "anywhere", "web"]):
                loc = "Virtual/Online"
            
            print(f"\n  {i}. {title}")
            print(f"     {etype} │ {days}d left")
            print(f"     {plat}  │  {loc}")
            print(f"     🔗 {link}")

    # summary
    print(f"\n{'═'*70}")
    print(f"  ✅  {active_count}/30 IGs active  │  "
          f"{total_events} events total  │  DB updated")
    print(f"{'═'*70}")

    # warnings for IGs with < 3 events
    for ig in MASTER_IGS:
        if ig == "MuV":
            continue
        count = len(grouped.get(ig, []))
        if 0 < count < 3:
            print(f"  ⚠️  {ig}: only {count} events — expand scrape sources")
        elif count == 0:
            print(f"  ❌  {ig}: 0 events — check keywords or scrape sources")


async def main() -> None:
    # ── Warm up DB connection (DNS + SSL handshake) ──────────────────────
    print("[DB] Connecting to MongoDB...")
    try:
        collection = get_collection()
        collection.database.client.admin.command("ping")
        print("[DB] ✅ Connected!")
    except Exception as e:
        print(f"[DB] ❌ Connection failed: {e}")
        print("[DB] Skipping DB save — events will still be displayed.")
        collection = None

    # ── Scrape ──────────────────────────────────────────────────────────────
    print("\n[Scraper] Fetching events from all platforms...")
    raw_events = await fetch_all_events()
    print(f"[Scraper] {len(raw_events)} raw events fetched")

    # ── Clean (5-rule strict filter) ────────────────────────────────────────
    primary_events, extended_events = clean_events(raw_events, use_ai=False)

    # ── Process (dedup → filter → classify → score → IG map → top-5) ──────
    grouped = curate(primary_events, extended_events, IG_KEYWORDS)

    # ── Store ───────────────────────────────────────────────────────────────
    if collection is not None:
        inserted, _ = save_events(grouped)
        print(f"\n[DB] {inserted} documents upserted/modified")
    else:
        print("\n[DB] Skipped (no connection)")

    # ── Display ─────────────────────────────────────────────────────────────
    _render(grouped)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
