"""
MuHive Text & Hashing Utilities
──────────────────────────────
Core string manipulation and fingerprinting logic.
Used for deduplication and source domain extraction.

Functions:
- get_hash: Generates a unique MD5 fingerprint for an item
- get_domain: Extracts the base domain from URLs or source strings
"""

import hashlib
from urllib.parse import urlparse
from models import ScoutItem

def get_hash(item: ScoutItem) -> str:
    """
    Creates a unique MD5 hash based on URL and Title.
    Used to prevent processing the same item twice.
    """
    content = (item.url + item.title).encode("utf-8")
    return hashlib.md5(content).hexdigest()

def get_domain(source: str) -> str:
    """
    Normalizes a source string into a clean domain.
    Example: 'https://devpost.com/hackathons' -> 'devpost.com'
    """
    s = source.strip().lower()
    if "://" not in s:
        s = "https://" + s
        
    parsed = urlparse(s)
    domain = parsed.netloc or parsed.path.split("/")[0]
    
    # Remove 'www.' prefix if present
    if domain.startswith("www."):
        domain = domain[4:]
        
    return domain
