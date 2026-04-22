import re
import os

with open(r'c:\Users\Zaim\Desktop\Antigravity Workspace\Mu-Hive\src\agents\scout.py', 'r', encoding='utf-8') as f:
    scout_code = f.read()

with open(r'c:\Users\Zaim\Desktop\Antigravity Workspace\Mu-Hive-joshna\scraper.py', 'r', encoding='utf-8') as f:
    joshna_code = f.read()

# 1. Add imports
scout_code = scout_code.replace('import asyncio\n', 'import asyncio\nimport aiohttp\nfrom src.agents.planner import MVP_IGS\n')

# 2. Update RSS category
scout_code = scout_code.replace(
    'if db.insert_opportunity(title, link, summary, source_engine="RSS", ig_tags=[ig]):',
    'if db.insert_opportunity(title, link, summary, source_engine="RSS", ig_tags=[ig], category="News"):'
)

# 3. Update search category
scout_code = scout_code.replace(
    'if db.insert_opportunity(title, link, source_engine=source, ig_tags=[keyword]):',
    'if db.insert_opportunity(title, link, source_engine=source, ig_tags=[keyword], category=category.capitalize()):'
)

# Extract Joshna's functions starting from 'OUTPUT_FILE' down to 'async def main():'
start_idx = joshna_code.find('USER_AGENT = "Mozilla/5.0')
end_idx = joshna_code.find('async def main():')

if start_idx != -1 and end_idx != -1:
    joshna_funcs = joshna_code[start_idx:end_idx].strip()
    
    # Remove USER_AGENT duplicate (already in scout.py)
    joshna_funcs = joshna_funcs.replace('USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"\n', '')

    hackathon_insert_logic = """
def map_hackathon_tags(tags):
    tag_map = {
        "ai": "AI", "machine learning": "AI", "genai": "AI", "llm": "AI",
        "data science": "Data Science", "data": "Data Science", "analytics": "Data Science",
        "web": "Web Development", "frontend": "Web Development", "backend": "Web Development", "devops": "Web Development",
        "cyber": "Cyber Security", "security": "Cyber Security", "crypto": "Cyber Security", "blockchain": "Cyber Security",
        "ui": "UI/UX", "ux": "UI/UX", "design": "UI/UX"
    }
    mapped_igs = set()
    for tag in tags:
        t = str(tag).lower()
        for k, v in tag_map.items():
            if k in t:
                mapped_igs.add(v)
    return list(mapped_igs)

async def run_hackathon_apis(db: Database):
    logger.info("Running Hackathon API Scrapers...")
    events = []
    semaphore = asyncio.Semaphore(15)
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
                events.extend(res)
            elif isinstance(res, Exception):
                logger.warning(f"Hackathon extraction error: {res}")
                
    new_count = 0
    for ev in events:
        summary = f"Platform: {ev['platform']}\\nStart: {ev['startDate']}\\nEnd: {ev['endDate']}\\nLocation: {ev['location']}\\nPrize Pool: {ev['prizePool']}\\nCost: {ev['cost']}\\nEligibility: {ev['eligibility']}\\nTags: {', '.join(ev['tags'])}"
        ig_tags = map_hackathon_tags(ev['tags'])
        
        # Only insert if there is at least one mapped IG (will skip unmatched ones)
        if ig_tags:
            if db.insert_opportunity(ev['eventName'], ev['registrationLink'], summary, source_engine=ev['platform'], ig_tags=ig_tags, category="Hackathons", is_processed=True, quality_score=8):
                new_count += 1
                
    logger.info(f"Hackathon APIs inserted {new_count} new targeted opportunities.")
"""

    injection = f"\n\n# --- JOSHNA HACKATHON APIs ---\n{joshna_funcs}\n{hackathon_insert_logic}\n# -----------------------------\n"
    
    # Inject right before l1_httpx function
    insert_pos = scout_code.find('async def l1_httpx')
    scout_code = scout_code[:insert_pos] + injection + scout_code[insert_pos:]
    
    # Also add the execution call inside run_scout_async
    scout_code = scout_code.replace(
        'run_search_agent(db)\n    await run_scraper_agent(db)',
        'run_search_agent(db)\n    await run_hackathon_apis(db)\n    await run_scraper_agent(db)'
    )

    with open(r'c:\Users\Zaim\Desktop\Antigravity Workspace\Mu-Hive\src\agents\scout.py', 'w', encoding='utf-8') as f:
        f.write(scout_code)
    print("scout.py patched successfully.")
else:
    print("Could not find start/end bounds for patching.")
