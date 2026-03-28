"""
MuHive Filtering Logic
──────────────────────
Handles 'Stage 2a' filtering: deduplication, blocklists, and source checks.
The first line of defense before items hit the expensive LLMs.

Functions:
- pre_filter: Main sequential check for a single ScoutItem
- clear_hash_set: Resets the in-memory deduplication tracker
"""

from typing import Any
from models import ScoutItem
from p01_configuration import load_config
from p02_text_processing import get_hash, get_domain

# Set to track processed items in the current batch
MEMORY_HASH_SET: set[str] = set()

def pre_filter(item: ScoutItem) -> dict[str, Any]:
    """
    Checks if an item should proceed to LLM stages.
    Returns: { status: 'pass'|'fail', ... }
    """
    cfg = load_config()
    s2 = cfg["stage2"]

    # 1. Deduplication
    h = get_hash(item)
    if h in MEMORY_HASH_SET:
        return {"status": "fail", "fail_reason": "duplicate", "item_hash": h}
    MEMORY_HASH_SET.add(h)

    # 2. Content validation
    if not item.title or not item.title.strip():
        return {"status": "fail", "fail_reason": "empty_title", "item_hash": h}
    
    # 3. Blocklist
    text = (item.title + " " + item.description).lower()
    for word in s2["blocklist"]:
        if word.lower() in text:
            return {"status": "fail", "fail_reason": f"blocked:{word}", "item_hash": h}

    # 4. Source Tier
    domain = get_domain(item.source)
    tier = s2["source_tiers"].get(domain, s2["default_source_tier"])

    return {"status": "pass", "item_hash": h, "source_tier": tier}

def clear_hash_set() -> None:
    """Reset for a new batch run."""
    MEMORY_HASH_SET.clear()
