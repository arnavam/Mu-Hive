import sys
import json
import re
from datetime import datetime, timezone

try:
    from dateutil import parser as date_parser
except ImportError:
    date_parser = None

DATA_FILE = "hackathons.json"

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

def is_fresh(event):
    """
    Returns True if the event is fresh, upcoming, 'Live', 'TBA', or unparseable.
    Returns False only if the date is strictly in the past (expired).
    """
    date_str = event.get("endDate")
    if not date_str or str(date_str).strip().lower() in ["tba", "live", "none", ""]:
        date_str = event.get("startDate", "")
        
    date_str = str(date_str).strip()
    if not date_str or date_str.lower() in ["tba", "live", "none"]:
        return True
        
    # Handle ranges like "Mar 28 - Apr 11, 2026"
    # We take the second part to check expiration
    if " - " in date_str and "T" not in date_str:
        parts = date_str.split(" - ")
        target_date_str = parts[-1].strip()
        # If the second part has no year but the first part does, add it
        if not re.search(r'\d{4}', target_date_str) and re.search(r'\d{4}', parts[0]):
            year_match = re.search(r'\d{4}', parts[0])
            if year_match:
                target_date_str = f"{target_date_str} {year_match.group()}"
        date_str = target_date_str

    try:
        if date_parser:
            parsed_date = date_parser.parse(date_str, fuzzy=True)
        else:
            # Fallback regex parsing if dateutil is not installed
            iso_match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', date_str)
            if iso_match:
                parsed_date = datetime.strptime(iso_match.group(1), "%Y-%m-%dT%H:%M:%S")
            else:
                date_str_clean = re.sub(r'(st|nd|rd|th),?', '', date_str)
                parsed_date = None
                for fmt in ("%b %d %Y", "%d %b %Y", "%B %d %Y", "%d %B %Y", "%Y-%m-%d"):
                    try:
                        parsed_date = datetime.strptime(date_str_clean.strip(), fmt)
                        break
                    except ValueError:
                        pass
                
                if not parsed_date:
                    match = re.search(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', date_str)
                    if match:
                        month, day, year = match.groups()
                        parsed_date = datetime.strptime(f"{str(month)[:3]} {day} {year}", "%b %d %Y")
                    else:
                        match2 = re.search(r'(\d{1,2})\s+([A-Za-z]+),?\s+(\d{4})', date_str)
                        if match2:
                            day, month, year = match2.groups()
                            parsed_date = datetime.strptime(f"{day} {str(month)[:3]} {year}", "%d %b %Y")
                        else:
                            return True # Unparseable without dateutil, keep to be safe

        if parsed_date and parsed_date.tzinfo is not None:
            parsed_date = parsed_date.astimezone(timezone.utc).replace(tzinfo=None)
            
        now = datetime.utcnow()
        if parsed_date and parsed_date.date() < now.date():
            return False # Strictly in the past
    except Exception:
        pass # Unparseable, keep to be safe

    return True

def calculate_score(event):
    score = 0
    loc = event.get("location", "").lower()
    proximity_keywords = ["kerala", "kochi", "trivandrum", "palai", "online", "virtual"]
    if any(k in loc for k in proximity_keywords):
        score += 50
        
    cost = event.get("cost", "").lower()
    if "free" in cost:
        score += 30
    elif cost and cost not in ["free", "tba", "0", "none"]:
        score -= 50
        
    elig = event.get("eligibility", "").lower()
    elig_keywords = ["students", "college", "b.tech", "student", "university"]
    if any(k in elig for k in elig_keywords):
        score += 30
        
    prize = event.get("prizePool", "")
    if prize and str(prize).strip() and str(prize).strip().lower() not in ["tba", "none"]:
        score += 30
        
    return score

def map_to_ig(tags_list):
    """Maps tags to our structured IG_KEYWORDS dict.
    Converts list array to a single string then checks against subsets.
    """
    mapped = set()
    combined_str = ""
    
    if isinstance(tags_list, list):
        combined_str += " ".join([str(t) for t in tags_list])
        
    combined_str = combined_str.lower()
    
    # Keyword Matching Logic loop
    for ig_name, keywords in IG_KEYWORDS.items():
        if any(kw in combined_str for kw in keywords):
            mapped.add(ig_name)
            
    # The Fallback Rules
    if not mapped:
        if combined_str.strip() == "":
            mapped.add("Web Development")
        elif "hackathon" in combined_str or "hack" in combined_str or "code" in combined_str:
            mapped.add("Web Development")
        elif "data" in combined_str:
            mapped.add("Data Science")
        else:
            mapped.add("AI")
            
    return list(mapped)

def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
        
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            events = json.load(f)
    except FileNotFoundError:
        print("hackathons.json not found. Run advanced_scraper.py first.")
        return
        
    grouped = {ig: [] for ig in MASTER_IGS}
    
    for event in events:
        if not is_fresh(event):
            continue
            
        event["_score"] = calculate_score(event)
        
        tags = event.get("tags", [])
        
        # We append event name string to mapping if tags are completely empty
        if not tags and event.get("eventName"):
            mapped = map_to_ig([event.get("eventName")])
        else:
            mapped = map_to_ig(tags)
            
        for ig in mapped:
            grouped[ig].append(event)
            
    print("============================================================")
    print("🚀 Weekly Hackathon Radar - Top 5 Relevant Picks")
    print("============================================================\n")
    
    for ig in MASTER_IGS:
        ig_events = grouped[ig]
        if not ig_events:
            continue
            
        ig_events.sort(key=lambda x: x.get("_score", 0), reverse=True)
        ig_events = ig_events[:5]
        
        print("-" * 60)
        print(f"## {ig}\n")
        
        for e in ig_events:
            print(f"Event: {e['eventName']}")
            print(f"Date: {e['startDate']}")
            print(f"Source: {e['platform']}")
            print(f"Link: {e['registrationLink']}\n")

if __name__ == "__main__":
    main()
