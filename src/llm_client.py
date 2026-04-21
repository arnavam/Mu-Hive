import os
import json
from loguru import logger
from openai import OpenAI
from aiolimiter import AsyncLimiter
from .config import load_config
from .circuit_breaker import mark_failure, is_cooled_down

_limiter_cache = {}

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

# Reads models.yaml, returns a client for that role and tier
def make_llm_client(role, tier="cheap"):
    models = load_config("models")
    role_cfg = models["roles"][role]
    
    # Try specified tier, fallback to first available
    tier_cfg = role_cfg.get(tier) or list(role_cfg.values())[0]
    provider_name = tier_cfg["provider"]
    provider_cfg = models["providers"][provider_name]
    
    # BUG FIX: Only check if the PROVIDER is in cooldown.
    # Previously this also checked the model, which caused unnecessary
    # fallback triggers when only the model name was stale in circuit state.
    if not is_cooled_down(provider_name):
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
        tier_cfg["max_tokens"],
        provider_name
    )
