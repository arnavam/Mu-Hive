"""
MuHive Infrastructure Utilities

Config loading, item hashing, domain extraction, and circuit breaker.
"""

import hashlib
import logging
import os
import time
import yaml
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger("muhive.utils")

# ==============================================================================
# SECTION 1: CONFIGURATION
# ==============================================================================

_config_cache: dict[str, Any] | None = None

def load_config(path: str | None = None) -> dict[str, Any]:
    """Loads and caches the central config.yaml file."""
    global _config_cache
    if _config_cache is None:
        path = path or os.path.join(os.path.dirname(__file__), "config.yaml")
        with open(path, "r") as f:
            _config_cache = yaml.safe_load(f)
    return _config_cache



# ==============================================================================
# SECTION 2: HASHING & DOMAINS
# ==============================================================================

def get_hash(item) -> str:
    """Creates a unique MD5 hash based on URL and Title."""
    content = (item.url + item.title).encode("utf-8")
    return hashlib.md5(content).hexdigest()

def get_domain(source: str) -> str:
    """Extracts a clean domain from a URL or source string."""
    s = source.strip().lower()
    if "://" not in s: s = f"https://{s}"
    domain = urlparse(s).netloc or s.split("/")[0]
    return domain.removeprefix("www.")

# ==============================================================================
# SECTION 3: CIRCUIT BREAKER
# ==============================================================================

_circuit_breaker: dict[str, float] = {}

def is_circuit_open(provider: str, cooldown_minutes: int) -> bool:
    """Checks if a provider is currently in a failure cooldown period."""
    return (time.time() - _circuit_breaker.get(provider, 0)) < (cooldown_minutes * 60)

def trip_circuit(provider: str) -> None:
    """Disables a provider temporarily after a failure."""
    _circuit_breaker[provider] = time.time()
    logger.warning(f"Circuit TRIPPED: {provider}")
