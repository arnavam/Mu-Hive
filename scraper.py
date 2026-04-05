import asyncio
import aiohttp
import json

OUTPUT_FILE = "hackathons.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# API Endpoints
DEVFOLIO_API = "https://api.devfolio.co/api/search/hackathons"
UNSTOP_API = "https://unstop.com/api/public/opportunity/search-result"
DEVPOST_API = "https://devpost.com/api/hackathons" 
HACKEREARTH_API = "https://www.hackerearth.com/api/events/upcoming/"

def normalize_event(name, platform, link, start, end, tags, location="", prize="", cost="", elig=""):
    return {
        "eventName": str(name).strip() if name else "Unknown",
        "platform": platform,
        "registrationLink": link if link else "",
        "startDate": str(start).strip() if start else "TBA",
        "endDate": str(end).strip() if end else "TBA",
        "tags": [str(t).strip() for t in tags if t] if isinstance(tags, list) else [],
        "location": str(location).strip() if location else "Online",
        "prizePool": str(prize).strip() if prize else "",
        "cost": str(cost).strip() if cost else "Free",
        "eligibility": str(elig).strip() if elig else "Students"
    }

async def fetch_devfolio_page(session, semaphore, offset):
    events = []
    payload = {"from": offset, "size": 50, "query": {"match_all": {}}}
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    
    async with semaphore:
        try:
            async with session.post(DEVFOLIO_API, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    hits = data.get("hits", {}).get("hits", [])
                    for item in hits:
                        try:
                            src = item.get("_source", {})
                            name = src.get("name", "Unknown")
                            slug = src.get("slug", "")
                            link = f"https://{slug}.devfolio.co" if slug else ""
                            start = src.get("starts_at", "TBA")
                            end = src.get("ends_at", "TBA")
                            tags = src.get("themes", [])
                            loc = "Online" if src.get("is_online") else "In-Person"
                            events.append(normalize_event(name, "Devfolio", link, start, end, tags, loc, "TBA", "Free", "Students"))
                        except Exception:
                            continue
        except Exception as e:
            pass
    return events

async def get_all_devfolio(session, semaphore):
    print("[*] Starting Devfolio API concurrent extraction...")
    offset = 0
    all_events = []
    while True:
        # Fetch in concurrent chunks of 5 pages (250 items)
        tasks = [fetch_devfolio_page(session, semaphore, o) for o in range(offset, offset + 250, 50)]
        results = await asyncio.gather(*tasks)
        
        empty_page_found = False
        for res in results:
            if not res:
                empty_page_found = True
            all_events.extend(res)
            
        if empty_page_found:
            break
        offset += 250
    print(f"[+] Devfolio complete. Found {len(all_events)} events.")
    return all_events

async def fetch_unstop_page(session, semaphore, page):
    events = []
    url = f"{UNSTOP_API}?opportunity=hackathons&page={page}&per_page=20"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    async with semaphore:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    arr = data.get("data", {}).get("data", [])
                    for item in arr:
                        try:
                            name = item.get("title", "")
                            seo = item.get("seo_url", "")
                            link = f"https://unstop.com/hackathons/{seo}" if seo else ""
                            start = item.get("start_date", "TBA")
                            end = item.get("end_date", "TBA")
                            filters = item.get("filters", {})
                            tags = [t.get("name") for t in filters] if isinstance(filters, list) else []
                            cost = "Paid" if item.get("payment_type") == "paid" else "Free"
                            events.append(normalize_event(name, "Unstop", link, start, end, tags, "Virtual/Online", "TBA", cost, "Students/College"))
                        except Exception:
                            continue
        except Exception:
            pass
    return events

async def get_all_unstop(session, semaphore):
    print("[*] Starting Unstop API concurrent extraction...")
    page = 1
    all_events = []
    while True:
        # Fetch chunk of 5 pages concurrently
        tasks = [fetch_unstop_page(session, semaphore, p) for p in range(page, page + 5)]
        results = await asyncio.gather(*tasks)
        
        empty_page_found = False
        for res in results:
            if not res:
                empty_page_found = True
            all_events.extend(res)
            
        if empty_page_found:
            break
        page += 5
    print(f"[+] Unstop complete. Found {len(all_events)} events.")
    return all_events

async def fetch_devpost_page(session, semaphore, page):
    events = []
    url = f"{DEVPOST_API}?page={page}"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    async with semaphore:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    arr = data.get("hackathons", [])
                    for item in arr:
                        try:
                            name = item.get("title", "")
                            link = item.get("url", "")
                            start = item.get("submission_period_dates", "TBA")
                            end = item.get("submission_period_dates", "TBA")
                            tags = item.get("themes", [])
                            loc = item.get("location", "Online")
                            prize = item.get("prize_amount", "")
                            events.append(normalize_event(name, "Devpost", link, start, end, tags, loc, prize, "Free", "Students/Global"))
                        except Exception:
                            continue
        except Exception:
            pass
    return events

async def get_all_devpost(session, semaphore):
    print("[*] Starting Devpost API concurrent extraction...")
    page = 1
    all_events = []
    while True:
        tasks = [fetch_devpost_page(session, semaphore, p) for p in range(page, page + 5)]
        results = await asyncio.gather(*tasks)
        
        empty_page_found = False
        for res in results:
            if not res:
                empty_page_found = True
            all_events.extend(res)
            
        if empty_page_found:
            break
        page += 5
    print(f"[+] Devpost complete. Found {len(all_events)} events.")
    return all_events

async def fetch_hackerearth_page(session, semaphore, page):
    events = []
    url = f"{HACKEREARTH_API}?page={page}"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    async with semaphore:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    arr = data.get("response", [])
                    for item in arr:
                        try:
                            name = item.get("title", "")
                            link = item.get("url", "")
                            start = item.get("start_utc_tz", "TBA")
                            end = item.get("end_utc_tz", "TBA")
                            tags = item.get("tags", [])
                            loc = item.get("location", "Online")
                            events.append(normalize_event(name, "HackerEarth", link, start, end, tags, loc, "TBA", "Free", "Open"))
                        except Exception:
                            continue
        except Exception:
            pass
    return events

async def get_all_hackerearth(session, semaphore):
    print("[*] Starting HackerEarth API concurrent extraction...")
    page = 1
    all_events = []
    while True:
        tasks = [fetch_hackerearth_page(session, semaphore, p) for p in range(page, page + 5)]
        results = await asyncio.gather(*tasks)
        
        empty_page_found = False
        for res in results:
            if not res:
                empty_page_found = True
            all_events.extend(res)
            
        if empty_page_found:
            break
        page += 5
    print(f"[+] HackerEarth complete. Found {len(all_events)} events.")
    return all_events

async def main():
    print("==================================================")
    print(" MAX SPEED Production Hackathon Aggregator Started")
    print("==================================================\n")
    
    events = []
    semaphore = asyncio.Semaphore(15)
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Run all 4 dynamic extraction loops concurrently
        tasks = [
            get_all_devfolio(session, semaphore),
            get_all_unstop(session, semaphore),
            get_all_devpost(session, semaphore),
            get_all_hackerearth(session, semaphore)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for res in results:
            if isinstance(res, list):
                events.extend(res)
            elif isinstance(res, Exception):
                print(f"[!] Top-level error: {res}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=4, ensure_ascii=False)
        
    print(f"[+] Ultra-fast scraper complete. Found {len(events)} events.")
    print(f"[+] Wrote to {OUTPUT_FILE}")

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
