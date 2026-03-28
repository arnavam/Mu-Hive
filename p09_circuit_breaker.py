"""
MuHive Circuit Breaker
──────────────────────
Safety mechanism to prevent overloading AI providers or wasting credits
when a specific service (like Groq or Gemini) is failing.

Functions:
- is_circuit_open: Checks if a provider is currently in 'cooldown'
- trip_circuit: Temporarily disables a provider after a failure
"""

import time
import logging

logger = logging.getLogger("muhive.cb")

# Registry of failed providers: { provider_name: timestamp_of_failure }
_circuit_breaker: dict[str, float] = {}

def is_circuit_open(provider: str, cooldown_minutes: int) -> bool:
    """
    Returns True if the provider should be skipped due to recent failures.
    """
    last_fail = _circuit_breaker.get(provider, 0)
    elapsed = time.time() - last_fail
    return elapsed < (cooldown_minutes * 60)

def trip_circuit(provider: str) -> None:
    """
    Marks a provider as failed, triggering the cooldown period.
    """
    _circuit_breaker[provider] = time.time()
    logger.warning("Circuit breaker TRIPPED for: %s", provider)
