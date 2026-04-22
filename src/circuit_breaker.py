import os
import time
import json
from src.config import load_config

# Helpers for Circuit Breaker (LITE)
def get_circuit_state():
    pipeline_cfg = load_config("pipeline")
    path = pipeline_cfg.get("circuit_state_file", "data/circuit_state.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        # If corrupted or empty, reset
        return {}

def mark_failure(provider_or_model):
    pipeline_cfg = load_config("pipeline")
    state = get_circuit_state()
    state[provider_or_model] = {
        "last_429": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "expiry": time.time() + pipeline_cfg.get("circuit_cooldown_seconds", 300)
    }
    path = pipeline_cfg.get("circuit_state_file", "data/circuit_state.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f)

def is_cooled_down(provider_or_model):
    state = get_circuit_state()
    entry = state.get(provider_or_model, {})
    # If it's a simple timestamp (legacy), convert or handle
    if isinstance(entry, (int, float)):
        return time.time() > entry
    expiry = entry.get("expiry", 0)
    return time.time() > expiry
