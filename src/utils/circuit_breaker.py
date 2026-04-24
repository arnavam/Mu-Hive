import time
from typing import Dict

# Simple in-memory circuit breaker
# Tracks failures per provider and enforces a cooldown period
_failures: Dict[str, float] = {}
COOLDOWN_SECONDS = 300  # 5 minutes

def mark_failure(provider: str):
    """Marks a provider as failed and starts the cooldown."""
    _failures[provider] = time.time()

def is_cooled_down(provider: str) -> bool:
    """Returns True if the provider is NOT in a cooldown period."""
    if provider not in _failures:
        return True
    
    last_failure = _failures[provider]
    if time.time() - last_failure > COOLDOWN_SECONDS:
        del _failures[provider]
        return True
        
    return False
