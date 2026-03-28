"""
MuHive Configuration Module
───────────────────────────
This module handles loading and caching the 'config.yaml' settings.
It ensures that configuration is read once and reused across the pipeline.

Functions:
- load_config: Reads settings from YAML (cached)
- reload_config: Forces a fresh read from disk
"""

import os
from typing import Any
import yaml

# Internal cache to avoid redundant disk I/O
_config_cache: dict[str, Any] | None = None

def load_config(path: str | None = None) -> dict[str, Any]:
    """
    Load the central config.yaml file.
    Returns a dictionary of settings.
    """
    global _config_cache
    if _config_cache is not None:
        return _config_cache
        
    if path is None:
        # Default path is relative to this file
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
        
    with open(path, "r") as f:
        _config_cache = yaml.safe_load(f)
    return _config_cache

def reload_config(path: str | None = None) -> dict[str, Any]:
    """
    Clear the cache and reload the configuration.
    Useful for testing or dynamic profile switching.
    """
    global _config_cache
    _config_cache = None
    return load_config(path)
