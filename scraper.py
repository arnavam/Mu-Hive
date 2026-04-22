import asyncio
import aiohttp
import json
import sqlite3
import os
import sys
import re
from datetime import datetime, timezone

try:
    from dateutil import parser as date_parser
except ImportError:
    date_parser = None

OUTPUT_FILE = "hackathons.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# API Endpoints
DEVFOLIO_API = "https://api.devfolio.co/api/search/hackathons"
UNSTOP_API = "https://unstop.com/api/public/opportunity/search-result"
DEVPOST_API = "https://devpost.com/api/hackathons?status[]=upcoming&status[]=open"
HACKEREARTH_API = "https://www.hackerearth.com/api/events/upcoming/"

IG_KEYWORDS = {
    "Web Development": ["web", "frontend", "backend", "react", "node", "django", "html", "javascript", "fullstack", "css", "vue", "angular", "php"],
    "Cyber Security": ["security", "cyber", "hack", "ctf", "forensics", "infosec", "cryptography", "malware", "penetration", "bug bounty"],
    "Generative AI": ["llm", "gpt", "generative", "prompt", "genai", "stable diffusion", "diffusion", "midjourney", "openai", "claude"],
    "AI": ["ai", "ml", "machine learning", "artificial intelligence", "nlp", "computer vision", "tensorflow", "pytorch"],
    "Mobile Development": ["app", "android", "ios", "flutter", "react native", "kotlin", "swift"],
    "Blockchain": ["web3", "crypto", "blockchain", "smart contract", "eth", "solana", "nft", "bitcoin", "ethereum", "defi"],
    "Devops": ["devops", "cloud", "aws", "docker", "kubernetes", "azure", "gcp", "ci/cd", "infrastructure"],
    "Game Dev": ["game", "unity", "unreal", "godot", "gaming", "esports"],
    "UI UX": ["ui", "ux", "design", "figma", "interface", "user experience", "user interface", "product design"],
    "Data Analytics": ["data analysis", "sql", "tableau", "powerbi", "dashboard", "analytics", "business intelligence"],
    "Data Science": ["data science", "pandas", "deep learning", "neural network", "datathon", "kaggle", "scikit"],
    "Internet Of Things (IOT) And Robotics": ["iot", "hardware", "arduino", "raspberry", "robotics", "embedded", "sensors", "electronics"],
    "AR VR MR": ["ar", "vr", "xr", "augmented", "virtual reality", "metaverse", "mixed reality", "spatial"],
    "No Or Low Code": ["nocode", "lowcode", "bubble", "webflow", "zapier", "framer"],
    "Data Structures and Algorithm": ["dsa", "algorithm", "competitive programming", "leetcode", "data structures", "cp", "codeforces"],
    "Quality Assurance": ["qa", "testing", "automation", "selenium", "jest", "cypress", "quality"],
    "Entrepreneurship": ["startup", "pitch", "business", "founder", "ideathon", "pitching", "b-plan", "venture"],
    "Space": ["space", "astronomy", "nasa", "satellite", "rocket", "astro", "aerospace", "cosmos"],
    "Comics": ["comic", "manga", "anime", "webtoon", "fandom", "illustration"],
    "Digital Marketing": ["seo", "marketing", "social media", "content", "brand", "advertising", "growth"],
    "MuV": ["muv"],
    "Human Resources": ["hr", "human resources", "talent", "recruitment", "management", "workforce"],
    "Project Management": ["pm", "project management", "agile", "scrum", "product manager", "jira", "roadmap"],
    "Quantum Computing": ["quantum", "qubit", "qiskit", "ibm q"],
    "Strategic Leadership": ["strategy", "leadership", "executive", "vision", "management"],
    "Civil": ["civil", "architecture", "construction", "smart city", "infrastructure", "urban"],
    "Creative Design": ["creative", "art", "graphic design", "animation", "3d", "blender", "photoshop"],
    "Beckn": ["beckn", "ondc", "protocol", "commerce network", "dsep"],
    "Product Management": ["product", "product management", "roadmapping", "product strategy"]
}

MASTER_IGS = list(IG_KEYWORDS.keys())

def parse_and_check_expired(date_str):
    if not date_str or date_str.lower() in ["tba", "live", "none", "", "n/a", "ongoing"]:
        return "TBA"
        
    date_str = str(date_str)
    now = datetime.now()
    
    # 1. ISO format
    iso_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", date_str)
    if iso_match:
        try:
            parsed = datetime(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
            if parsed < now: return False
            delta = (parsed - now).days
            if delta > 60: return False
            return delta
        except:
            pass

    # 2. String ranges
    months = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, 
              "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
              "january": 1, "february": 2, "march": 3, "april": 4, "june": 6,
              "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12}
              
    target_str = date_str.split("-")[-1].lower()
    year_match = re.search(r"(\d{4})", date_str)
    year = int(year_match.group(1)) if year_match else now.year
    day_match = re.search(r"(\d{1,2})", target_str)
    
    if day_match:
        day = int(day_match.group(1))
        month = next((m_val for m_key, m_val in months.items() if m_key in target_str), None)
        if not month:
            month = next((m_val for m_key, m_val in months.items() if m_key in date_str.lower()), None)
            
        if month:
            try:
                parsed = datetime(year, month, day)
                if parsed < now: return False
                delta = (parsed - now).days
                if delta > 60: return False
                return delta
            except:
                pass
                
    return "TBA"

def get_event_delta(event):
    end = str(event.get("endDate", "TBA")).strip()
    start = str(event.get("startDate", "TBA")).strip()
    
    res = parse_and_check_expired(end)
    if res is False: return False
    if res != "TBA": return res
    
    return parse_and_check_expired(start)

def calculate_score(event):
    score = 0
    loc = event.get("location", "").lower()
    
    online_keywords = ["online", "virtual", "remote"]
    india_keywords = ["india", "bangalore", "mumbai", "delhi", "chennai", "hyderabad", "pune"]
    kerala_keywords = ["kerala", "kochi", "trivandrum", "palai", "ernakulam", "calicut"]
    foreign_keywords = ["usa", "us ", "uk ", "united states", "london", "san francisco", "new york", "canada", "europe", "germany", "australia"]
    
    if any(k in loc for k in foreign_keywords) and not any(k in loc for k in online_keywords):
        score -= 200
        
    if any(k in loc for k in kerala_keywords):
        score += 150
    elif any(k in loc for k in india_keywords):
        score += 80
    if any(k in loc for k in online_keywords):
        score += 100
        
    cost = event.get("cost", "").lower()
    if "free" in cost:
        score += 50
    elif cost and cost not in ["free", "tba", "0", "none"]:
        score -= 150
        
    prize = event.get("prizePool", "")
    if prize and str(prize).strip() and str(prize).strip().lower() not in ["tba", "none"]:
        score += 60
        
    delta = event.get("_days_away", "TBA")
    if delta == "TBA":
        score += 20
    else:
        if delta < 30: score += 100
        score += (60 - delta)
        
    return score

def map_to_ig(tags_list):
    mapped = set()
    combined_str = ""
    
    if isinstance(tags_list, list):
        combined_str += " ".join([str(t) for t in tags_list])
        
    combined_str = combined_str.lower()
    
    for ig_name, keywords in IG_KEYWORDS.items():
        if any(kw in combined_str for kw in keywords):
            mapped.add(ig_name)
            
    return list(mapped)

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
        except Exception:
            pass
    return events

async def get_all_devfolio(session, semaphore):
    offset = 0
    all_events = []
    seen_urls = set()
    while True:
        tasks = [fetch_devfolio_page(session, semaphore, o) for o in range(offset, offset + 500, 50)]
        results = await asyncio.gather(*tasks)
        
        empty_page_found = False
        new_events_found = False
        for res in results:
            if not res:
                empty_page_found = True
            for event in res:
                if event['registrationLink'] and event['registrationLink'] not in seen_urls:
                    seen_urls.add(event['registrationLink'])
                    all_events.append(event)
                    new_events_found = True
            
        if empty_page_found or not new_events_found:
            break
        offset += 500
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
    page = 1
    all_events = []
    seen_urls = set()
    while True:
        tasks = [fetch_unstop_page(session, semaphore, p) for p in range(page, page + 10)]
        results = await asyncio.gather(*tasks)
        
        empty_page_found = False
        new_events_found = False
        for res in results:
            if not res:
                empty_page_found = True
            for event in res:
                if event['registrationLink'] and event['registrationLink'] not in seen_urls:
                    seen_urls.add(event['registrationLink'])
                    all_events.append(event)
                    new_events_found = True
            
        if empty_page_found or not new_events_found:
            break
        page += 10
    return all_events

async def fetch_devpost_page(session, semaphore, page):
    events = []
    url = f"{DEVPOST_API}&page={page}"
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
    page = 1
    all_events = []
    seen_urls = set()
    while True:
        tasks = [fetch_devpost_page(session, semaphore, p) for p in range(page, page + 10)]
        results = await asyncio.gather(*tasks)
        
        empty_page_found = False
        new_events_found = False
        for res in results:
            if not res:
                empty_page_found = True
            for event in res:
                if event['registrationLink'] and event['registrationLink'] not in seen_urls:
                    seen_urls.add(event['registrationLink'])
                    all_events.append(event)
                    new_events_found = True
            
        if empty_page_found or not new_events_found:
            break
        page += 10
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
    page = 1
    all_events = []
    seen_urls = set()
    while True:
        tasks = [fetch_hackerearth_page(session, semaphore, p) for p in range(page, page + 10)]
        results = await asyncio.gather(*tasks)
        
        empty_page_found = False
        new_events_found = False
        for res in results:
            if not res:
                empty_page_found = True
            for event in res:
                if event['registrationLink'] and event['registrationLink'] not in seen_urls:
                    seen_urls.add(event['registrationLink'])
                    all_events.append(event)
                    new_events_found = True
            
        if empty_page_found or not new_events_found:
            break
        page += 10
    return all_events

async def main():
    raw_events = []
    semaphore = asyncio.Semaphore(50)
    
    timeout = aiohttp.ClientTimeout(total=45)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = [
            get_all_devfolio(session, semaphore),
            get_all_unstop(session, semaphore),
            get_all_devpost(session, semaphore),
            get_all_hackerearth(session, semaphore)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for res in results:
            if isinstance(res, list):
                raw_events.extend(res)

    # 1. Output RAW backup to JSON (optional)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(raw_events, f, indent=4, ensure_ascii=False)
        
    # 2. Deduplicate Events & strict validity
    unique_events = {}
    for e in raw_events:
        delta = get_event_delta(e)
        if delta is False:
            continue
        if not e.get("eventName") or not e.get("registrationLink"):
            continue
        link = e["registrationLink"]
        e["_days_away"] = delta
        if link not in unique_events:
            unique_events[link] = e
            
    valid_events = list(unique_events.values())
    
    # 3. Score and Assign hits
    for event in valid_events:
        event["_score"] = calculate_score(event)
        combined_str = " ".join([str(t) for t in event.get("tags", [])]) + " " + str(event.get("eventName", ""))
        combined_str = combined_str.lower()
        
        event["_ig_hits"] = {}
        best_ig = None
        best_hits = 0
        
        for ig_name, keywords in IG_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in combined_str)
            event["_ig_hits"][ig_name] = hits
            if hits > best_hits:
                best_hits = hits
                best_ig = ig_name
                
        event["_primary_ig"] = best_ig
        
    valid_events.sort(key=lambda x: x["_score"], reverse=True)
        
    # 4. Strict Grouping with Global Used tracking
    grouped = {ig: [] for ig in MASTER_IGS}
    used_links = set()
    tba_counts = {ig: 0 for ig in MASTER_IGS}
    
    def can_add_event(ig, e):
        if e["_days_away"] == "TBA":
            if tba_counts[ig] >= 1:
                return False
        return True
        
    def add_event(ig, e):
        grouped[ig].append(e)
        used_links.add(e["registrationLink"])
        if e["_days_away"] == "TBA":
            tba_counts[ig] += 1
    
    # Pass 1: Perfect Primary Matches
    for e in valid_events:
        pig = e["_primary_ig"]
        link = e["registrationLink"]
        if pig and len(grouped[pig]) < 5 and link not in used_links:
            if can_add_event(pig, e):
                add_event(pig, e)
            
    # Pass 2: Smart Fallback (1+ hits)
    # The requirement strictly allows fallback ONLY if native events are < 3.
    for ig in MASTER_IGS:
        if len(grouped[ig]) < 3:
            candidates = [e for e in valid_events if e["registrationLink"] not in used_links and e["_ig_hits"][ig] > 0]
            # Prioritize closer semantic domain matches over generic score
            candidates.sort(key=lambda x: (x["_ig_hits"][ig], x["_score"]), reverse=True)
            for c in candidates:
                if can_add_event(ig, c):
                    add_event(ig, c)
                if len(grouped[ig]) == 5:
                    break
                    
    # Pass 3 (Generic 0-hit Fallback) is completely eradicated to prevent random noisy data in niche IGs.

    # 6. Console Output Clean UI
    final_curated_events_dict = {}
    
    for ig in MASTER_IGS:
        print(f"\n## {ig}\n")
        for e in grouped[ig]:
            print(f"Event: {e['eventName']}")
            print(f"Date: {e['startDate']}")
            print(f"Link: {e['registrationLink']}\n")
            
            # Format assigned IGs for SQLite DB
            link = e['registrationLink']
            if link not in final_curated_events_dict:
                curated_copy = e.copy()
                curated_copy['assigned_igs'] = set([ig])
                final_curated_events_dict[link] = curated_copy
            else:
                final_curated_events_dict[link]['assigned_igs'].add(ig)

    final_curated_events = list(final_curated_events_dict.values())

    # 4. Output ONLY Top Selected to SQLite DB
    db_file = "hackathons.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eventName TEXT,
            platform TEXT,
            registrationLink TEXT UNIQUE,
            startDate TEXT,
            endDate TEXT,
            tags TEXT,
            location TEXT,
            prizePool TEXT,
            cost TEXT,
            eligibility TEXT,
            interest_groups TEXT,
            score INTEGER
        )
    ''')
    
    try:
        cursor.execute("ALTER TABLE events ADD COLUMN interest_groups TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE events ADD COLUMN score INTEGER")
    except sqlite3.OperationalError:
        pass
    
    inserted = 0
    updated = 0
    for event in final_curated_events:
        ig_str = ", ".join(sorted(list(event['assigned_igs'])))
        try:
            cursor.execute('''
                INSERT INTO events (eventName, platform, registrationLink, startDate, endDate, tags, location, prizePool, cost, eligibility, interest_groups, score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event["eventName"], event["platform"], event["registrationLink"],
                event["startDate"], event["endDate"], ", ".join(event["tags"]),
                event["location"], event["prizePool"], event["cost"], event["eligibility"],
                ig_str, event["_score"]
            ))
            inserted += 1
        except sqlite3.IntegrityError:
            cursor.execute('''
                UPDATE events SET
                    eventName=?, platform=?, startDate=?, endDate=?, tags=?, location=?, prizePool=?, cost=?, eligibility=?, interest_groups=?, score=?
                WHERE registrationLink=?
            ''', (
                event["eventName"], event["platform"], event["startDate"], event["endDate"], 
                ", ".join(event["tags"]), event["location"], event["prizePool"], event["cost"], event["eligibility"],
                ig_str, event["_score"],
                event["registrationLink"]
            ))
            updated += 1
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
