# src/utils/ig_normalizer.py
"""Canonical IG normalization.

The registry (``src/config/interest_groups.yaml``) is the single source of
truth for IG names and aliases. No duplicate alias table is kept here.
"""

from __future__ import annotations


def normalize_ig(raw: str | None) -> str | None:
    """Resolve any alias or raw casing to its canonical IG name."""
    if not raw:
        return None
    from src.config.interest_groups import registry

    return registry.normalize(raw)
