"""
MuLearn Stage 2 — Utility Functions (Zero LLM)

- load_config(): reads config.yaml
- get_domain(): extract domain from URL/source string
- get_hash(): MD5 hash for deduplication
- pre_filter(): sequential reject/pass checks
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from models import ScoutItem

# ── Global in-memory hash set (dedup within a single batch run) ──
MEMORY_HASH_SET: set[str] = set()

# ── Config cache ──
_config_cache: dict[str, Any] | None = None


def load_config(path: str | None = None) -> dict[str, Any]:
    """Load config.yaml. Caches after first read."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
    with open(path, "r") as f:
        _config_cache = yaml.safe_load(f)
    return _config_cache


def reload_config(path: str | None = None) -> dict[str, Any]:
    """Force reload config.yaml (useful for tests)."""
    global _config_cache
    _config_cache = None
    return load_config(path)


def get_domain(source: str) -> str:
    """
    Extract domain from a URL or source string.
    Examples:
        'https://devpost.com/hackathon/xyz' → 'devpost.com'
        'devpost.com' → 'devpost.com'
        'reddit.com/r/MachineLearning' → 'reddit.com'
    """
    s = source.strip().lower()
    if "://" not in s:
        s = "https://" + s
    parsed = urlparse(s)
    domain = parsed.netloc or parsed.path.split("/")[0]
    # Strip www. prefix
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def get_hash(item: ScoutItem) -> str:
    """MD5 hash of url + title for dedup."""
    return hashlib.md5((item.url + item.title).encode("utf-8")).hexdigest()


def pre_filter(item: ScoutItem) -> dict[str, Any]:
    """
    Non-LLM pre-filter. Sequential checks (first failure = reject):
      1. Hash duplicate check
      2. Empty fields check
      3. Blocklist check
      4. Source tier injection

    Returns:
        {"status": "pass", "item_hash": ..., "source_tier": ...}  on pass
        {"status": "fail", "item_hash": ..., "fail_reason": ...}  on fail
    """
    cfg = load_config()
    s2 = cfg["stage2"]

    # 1. HASH CHECK
    item_hash = get_hash(item)
    if item_hash in MEMORY_HASH_SET:
        return {"status": "fail", "fail_reason": "duplicate", "item_hash": item_hash}
    # Register hash (will be committed only if item passes full pipeline)
    MEMORY_HASH_SET.add(item_hash)

    # 2. EMPTY CHECK
    if not item.title or not item.title.strip():
        return {"status": "fail", "fail_reason": "empty_title", "item_hash": item_hash}
    if not item.description or not item.description.strip():
        return {"status": "fail", "fail_reason": "empty_description", "item_hash": item_hash}

    # 3. BLOCKLIST CHECK
    text = (item.title + " " + item.description).lower()
    for blocked_word in s2["blocklist"]:
        if blocked_word.lower() in text:
            return {
                "status": "fail",
                "fail_reason": f"blocked:{blocked_word}",
                "item_hash": item_hash,
            }

    # 4. SOURCE TIER INJECTION
    domain = get_domain(item.source)
    source_tier = s2["source_tiers"].get(domain, s2["default_source_tier"])

    return {"status": "pass", "item_hash": item_hash, "source_tier": source_tier}


def clear_hash_set() -> None:
    """Clear the in-memory dedup set (useful between batch runs)."""
    MEMORY_HASH_SET.clear()
