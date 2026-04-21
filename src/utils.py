import os
import time
import yaml
import json
import random
from loguru import logger
from openai import OpenAI
from aiolimiter import AsyncLimiter
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

# Shared browser headers to mimic real users
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

def get_random_ua():
    return random.choice(_USER_AGENTS)

# Load .env file at the start
load_dotenv()

_config_cache = {}
_limiter_cache = {}

# Reads any yaml from config/ folder, cached after first load
def load_config(name):
    if name not in _config_cache:
        path = os.path.join("config", f"{name}.yaml")
        with open(path, "r") as f:
            _config_cache[name] = yaml.safe_load(f)
    return _config_cache[name]

# Returns aiolimiter using rpm from models.yaml for that specific model
# Cached so that multiple tasks using the same model share the same limiter
def get_limiter(provider, model_name):
    models = load_config("models")
    key = f"{provider}:{model_name}"
    
    if key not in _limiter_cache:
        # Check provider specific RPM in models.yaml
        provider_cfg = models["providers"].get(provider, {})
        rpm = provider_cfg.get("rpm", 10) # default to 10 if missing
        _limiter_cache[key] = AsyncLimiter(rpm, 60)
        
    return _limiter_cache[key]

# Tenacity wrapper using backoff from settings.yaml
def with_retry(fn):
    settings = load_config("settings")["pipeline"]
    return retry(
        stop=stop_after_attempt(settings["max_retries"]),
        wait=wait_exponential(
            multiplier=2, # Increased multiplier for free tier
            min=settings["retry_backoff_seconds"][0], 
            max=settings["retry_backoff_seconds"][-1]
        ),
        reraise=True
    )(fn)

# Reads models.yaml, returns a simple wrapper for the configured model
class LLMClient:
    def __init__(self, client, model, temperature, max_tokens, provider):
        self.client = client
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.provider = provider

    def create(self, response_model, messages):
        schema = json.dumps(response_model.model_json_schema(), indent=2)
        # Append schema instructions
        sys_msg = messages[0]["content"] + f"\n\nReturn EXACTLY valid JSON matching this schema:\n{schema}"
        messages[0]["content"] = sys_msg
        
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Defensive check for OpenRouter/Provider inconsistencies
            if not resp or not resp.choices or not resp.choices[0].message.content:
                raise ValueError("LLM returned an empty or malformed response.")
                
            return response_model.model_validate_json(resp.choices[0].message.content)
        except Exception as e:
            if "429" in str(e):
                logger.warning(f"Rate limit hit for {self.model}. Cooling down {self.provider}...")
                mark_failure(self.provider)
            raise e

# Helpers for Circuit Breaker (LITE)
def get_circuit_state():
    path = "state/circuit_state.json"
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        # If corrupted or empty, reset
        return {}

def mark_failure(provider_or_model):
    state = get_circuit_state()
    # Cool down for 5 minutes
    state[provider_or_model] = {
        "last_429": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "expiry": time.time() + 300
    }
    with open("state/circuit_state.json", "w") as f:
        json.dump(state, f)

def is_cooled_down(provider_or_model):
    state = get_circuit_state()
    entry = state.get(provider_or_model, {})
    # If it's a simple timestamp (legacy), convert or handle
    if isinstance(entry, (int, float)):
        return time.time() > entry
    expiry = entry.get("expiry", 0)
    return time.time() > expiry

# Reads models.yaml, returns a client for that role and tier
def make_llm_client(role, tier="cheap"):
    models = load_config("models")
    role_cfg = models["roles"][role]
    
    # Try specified tier, fallback to first available
    tier_cfg = role_cfg.get(tier) or list(role_cfg.values())[0]
    provider_name = tier_cfg["provider"]
    provider_cfg = models["providers"][provider_name]
    
    # Check if provider OR model is in cooldown
    if not is_cooled_down(provider_name) or not is_cooled_down(tier_cfg["model"]):
        logger.warning(f"Provider {provider_name} is in COOLDOWN. Attempting fallback.")
        if tier != "fallback":
            return make_llm_client(role, tier="fallback")
    
    api_key = os.environ.get(provider_cfg["api_key_env"])
    if not api_key:
        logger.error(f"API Key {provider_cfg['api_key_env']} missing from environment!")
        
    client = OpenAI(
        base_url=provider_cfg["base_url"],
        api_key=api_key or "missing"
    )
    return LLMClient(
        client, 
        tier_cfg["model"], 
        tier_cfg.get("temperature", 0.0), 
        tier_cfg.get("max_tokens", 500),
        provider_name
    )

# Bulk status updater for seen_hashes.json
def update_hashes_status(items, status):
    settings = load_config("settings")["pipeline"]
    hash_file = settings["seen_hashes_file"]
    
    if not os.path.exists(hash_file):
        data = {}
    else:
        try:
            with open(hash_file, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
            
    import hashlib
    def get_h(url, title):
        return hashlib.md5(f"{url}{title}".encode()).hexdigest()
        
    for item_data in items:
        # entry can be a CleanItem or a dict from verifier
        if isinstance(item_data, dict):
            item = item_data["item"]
        else:
            item = item_data
            
        h = get_h(item.url, item.title)
        if h in data:
            data[h]["status"] = status
            data[h]["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            
    with open(hash_file, "w") as f:
        json.dump(data, f, indent=2)
