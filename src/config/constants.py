"""
src/config/constants.py
=======================
Central configuration for the Mu-Hive hackathon aggregation pipeline.
All constants, keyword mappings, and scoring weights live here.
Import from this module — never hardcode values elsewhere.
"""

# ---------------------------------------------------------------------------
# HTTP / Network
# ---------------------------------------------------------------------------

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

CONCURRENCY_LIMIT: int = 50   # asyncio.Semaphore size
SESSION_TIMEOUT: int = 45     # aiohttp ClientTimeout (seconds)

# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

DEVFOLIO_API = "https://api.devfolio.co/api/search/hackathons"
UNSTOP_API = "https://unstop.com/api/public/opportunity/search-result"
DEVPOST_API = "https://devpost.com/api/hackathons?status[]=upcoming&status[]=open"
HACKEREARTH_API = "https://www.hackerearth.com/api/events/upcoming/"

# ---------------------------------------------------------------------------
# Pipeline Quality Rules
# ---------------------------------------------------------------------------

TOP_N: int = 5           # Maximum events selected per IG
MAX_TBA_PER_IG: int = 1  # Max events with TBA date allowed per IG slot
MAX_NON_HACK_PER_IG: int = 2  # Max non-Hackathon events per IG

# ---------------------------------------------------------------------------
# Location Keywords (for scoring & filtering)
# ---------------------------------------------------------------------------

ONLINE_KEYWORDS = ["online", "virtual", "remote", "anywhere", "web"]
KERALA_KEYWORDS = [
    "kerala", "kochi", "trivandrum", "palai", "ernakulam", "calicut", "kollam",
    "thrissur", "kozhikode", "malappuram", "kannur", "kasargod", "alappuzha",
    "idukki", "pathanamthitta", "wayanad"
]
INDIA_KEYWORDS = [
    "india", "bangalore", "mumbai", "delhi", "chennai", "hyderabad", "pune",
    "bengaluru", "noida", "gurgaon", "kolkata", "ahmedabad", "surat",
    "jaipur", "lucknow", "nagpur", "indore", "bhopal", "visakhapatnam"
]
FOREIGN_KEYWORDS = [
    "usa", "uk ", "united states", "london", "san francisco", "new york",
    "canada", "europe", "germany", "australia", "china", "japan",
    "singapore", "dubai", "sf", "boston", "france", "netherlands",
    "sweden", "switzerland", "hong kong", "taiwan", "korea"
]

# ---------------------------------------------------------------------------
# Controlled Master IG List (~30 IGs) + Keyword Mappings
# ---------------------------------------------------------------------------
# Every event MUST map to one or more of these IGs.
# If no match → "General Tech".
# NO random/noisy categories allowed.

IG_KEYWORDS: dict[str, list[str]] = {
    "Web Development": ["react", "node", "django", "flask", "frontend", "backend", "REST", "API", "web", "html", "css", "javascript", "php"],
    "AI": ["artificial intelligence", "AI hackathon", "neural network", "deep learning", "NLP", "computer vision", "AI agent"],
    "Generative AI": ["LLM", "GPT", "diffusion", "generative", "text-to-image", "stable diffusion", "prompt engineering", "GenAI"],
    "Machine Learning": ["ML", "machine learning", "model training", "classification", "regression", "sklearn", "pytorch", "tensorflow"],
    "Data Science": ["data science", "EDA", "pandas", "statistics", "dataset", "jupyter", "notebook", "kaggle", "datathon"],
    "Data Analytics": ["analytics", "data visualization", "business intelligence", "dashboard", "tableau", "power BI", "data challenge"],
    "Cyber Security": ["CTF", "cybersecurity", "security", "vulnerability", "pentest", "bug bounty", "capture the flag", "ethical hacking"],
    "Blockchain": ["web3", "smart contract", "NFT", "DeFi", "solidity", "crypto", "blockchain", "ethereum", "polygon"],
    "Cloud Computing": ["AWS", "GCP", "Azure", "cloud", "kubernetes", "serverless", "cloud native", "infrastructure", "devops cloud"],
    "Game Development": ["game jam", "unity", "unreal", "pygame", "game dev", "game design", "2D", "3D game"],
    "UI/UX": ["UI", "UX", "figma", "wireframe", "prototype", "design thinking", "user experience", "interface design", "designathon"],
    "AR/VR": ["augmented reality", "virtual reality", "AR", "VR", "XR", "metaverse", "mixed reality", "spatial computing"],
    "IoT & Robotics": ["IoT", "hardware", "raspberry pi", "arduino", "robotics", "embedded", "sensors", "microcontroller"],
    "Competitive Programming": ["competitive programming", "CP", "algorithm", "data structures", "codeforces", "leetcode", "coding contest", "lockout"],
    "Software Engineering": ["software engineering", "system design", "architecture", "backend", "full stack", "open source", "software development"],
    "Product Management": ["product management", "PM", "roadmap", "product strategy", "product thinking", "product teardown"],
    "Entrepreneurship": ["startup", "ideathon", "pitch", "venture", "business plan", "entrepreneurship", "innovation challenge"],
    "Digital Marketing": ["marketing", "SEO", "campaigns", "social media", "content", "growth hacking", "brand", "digital marketing"],
    "General Tech": ["anything that does not match above categories"],
    "Open Innovation": ["social good", "community", "inclusion", "diversity", "women in tech", "sustainability", "NGO", "impact"],
    "HealthTech": ["health", "medical", "hospital", "clinical", "MedTech", "healthcare", "patient", "biotech", "pharma"],
    "FinTech": ["finance", "payment", "banking", "fintech", "insurtech", "lending", "investment", "neobank", "paygentic"],
    "EdTech": ["education", "learning", "school", "university", "e-learning", "tutoring", "edtech", "curriculum", "teaching"],
    "Smart Cities": ["urban", "smart city", "infrastructure", "sustainability", "civic tech", "environment", "green", "climate", "energy"],
    "Mobile Development": ["android", "iOS", "flutter", "react native", "mobile app", "swift", "kotlin", "mobile development"],
    "DevOps": ["CI/CD", "docker", "deployment", "pipeline", "jenkins", "GitOps", "monitoring", "SRE", "devops", "infra"],
    "Quantum Computing": ["quantum", "qubit", "qiskit", "quantum circuit", "quantum ML", "quantum hackathon"],
    "Space Tech": ["space", "satellite", "NASA", "aerospace", "orbital", "rocketry", "astrophysics", "SpaceTech"],
    "Creative Design": ["creative", "art", "illustration", "visual design", "branding", "graphic design", "motion", "photography"],
    "Beckn": ["beckn protocol", "ONDC", "open network", "interoperability", "decentralized commerce"],
}

MASTER_IGS: list[str] = [
  "Web Development", "AI", "Generative AI", "Machine Learning",
  "Data Science", "Data Analytics", "Cyber Security", "Blockchain",
  "Cloud Computing", "Game Development", "UI/UX", "AR/VR",
  "IoT & Robotics", "Competitive Programming", "Software Engineering",
  "Product Management", "Entrepreneurship", "Digital Marketing",
  "General Tech", "Open Innovation", "HealthTech", "FinTech",
  "EdTech", "Smart Cities", "Mobile Development", "DevOps",
  "Quantum Computing", "Space Tech", "Creative Design", "Beckn"
]

RELATED_IGS: dict[str, list[str]] = {
    "AI": ["Machine Learning", "Data Science", "Generative AI"],
    "Machine Learning": ["AI", "Data Science"],
    "Generative AI": ["AI", "Machine Learning"],
    "Data Science": ["Data Analytics", "Machine Learning"],
    "Data Analytics": ["Data Science"],
    "Web Development": ["Software Engineering", "Mobile Development"],
    "UI/UX": ["Creative Design", "Web Development"],
    "IoT & Robotics": ["AR/VR"],
    "Cloud Computing": ["DevOps", "Software Engineering"],
    "DevOps": ["Cloud Computing"],
    "FinTech": ["Blockchain"],
    "Blockchain": ["FinTech"],
    "Smart Cities": ["IoT & Robotics", "Open Innovation"],
    "Product Management": ["Entrepreneurship"],
    "Entrepreneurship": ["Product Management"],
    "Digital Marketing": ["Creative Design"],
}

# ---------------------------------------------------------------------------
# Scoring Weights (Finalized)
# ---------------------------------------------------------------------------

SCORE_FREE_ONLINE_KERALA: int = 250  # Free + (Online or Kerala)
SCORE_FREE_INDIA: int = 150          # Free + rest of India
SCORE_PAID_INDIA: int = 100          # Paid but still India
SCORE_UNKNOWN_FEE: int = 50          # Fee unknown (TBA / None)
SCORE_FREE_BASE: int = 80            # Free anywhere
SCORE_PRIZE: int = 60                # Has a prize pool
SCORE_UPCOMING_30D: int = 100        # Starts within 30 days
SCORE_HACKATHON_TYPE: int = 100      # Hackathon
SCORE_BOOTCAMP_TYPE: int = 70        # Bootcamp
SCORE_WORKSHOP_TYPE: int = 50        # Workshop
SCORE_CONTEST_TYPE: int = 30         # Contest
SCORE_INTERNSHIP_TYPE: int = 10      # Internship
SCORE_TBA_DATE: int = 10             # Date is TBA

