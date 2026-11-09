"""
src/config/constants.py
=======================
Central configuration for the Mu-Hive hackathon aggregation pipeline.
Network and pipeline constants live here.
Import from this module — never hardcode values elsewhere.
"""

from src.config.interest_groups import registry

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
# Master IG list
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# IG configuration (single source of truth: interest_groups.yaml)
# ---------------------------------------------------------------------------
# MASTER_IGS, hackathon keywords, and related-IG mappings are derived from the
# YAML registry so names, aliases, and keywords cannot drift apart.

MASTER_IGS: list[str] = registry.all_active_names()
IG_KEYWORDS: dict[str, list[str]] = registry.hackathon_keywords
RELATED_IGS: dict[str, list[str]] = registry.related_igs

# ---------------------------------------------------------------------------
# Reverse IG mapping for curated fallback
# ---------------------------------------------------------------------------

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

