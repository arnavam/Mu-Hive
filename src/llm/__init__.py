import os
import json
from typing import List, Dict, Any, Type, Optional
from loguru import logger
from openai import OpenAI
from aiolimiter import AsyncLimiter
from src.config import load_config
from src.circuit_breaker import mark_failure, is_cooled_down

"""
LLM Provider Module
-------------------
This module handles communication with AI Model providers (Groq, OpenRouter, etc.).
It manages:
1. Rate Limiting: Ensures we don't violate API RPM limits.
2. Circuit Breaking: Automatically stops using a failing provider and tries a fallback.
3. Response Structuring: Automatically formats prompt to force models to return valid JSON.
"""

_limiter_cache: Dict[str, AsyncLimiter] = {}

def get_limiter(provider: str, model_name: str) -> AsyncLimiter:
    """Returns a shared rate limiter for a specific provider/model combination."""
    models_cfg = load_config("models")
    limiter_key = f"{provider}:{model_name}"
    
    if limiter_key not in _limiter_cache:
        provider_cfg = models_cfg.get("providers", {}).get(provider, {})
        # Respect the RPM limit set in models.yaml, defaulting to 10 if not found
        rpm_limit = provider_cfg.get("rpm", 10)
        _limiter_cache[limiter_key] = AsyncLimiter(rpm_limit, 60)
        
    return _limiter_cache[limiter_key]

class LLMClient:
    """Wrapper around the OpenAI client to support Pydantic schema validation."""
    
    def __init__(self, client: OpenAI, model: str, temperature: float, max_tokens: int, provider: str):
        self.client = client
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.provider = provider

    def create(self, response_model: Type[Any], messages: List[Dict[str, str]]) -> Any:
        """
        Executes a completion request and returns a validated Pydantic model.
        Injects the response schema into the system prompt to ensure JSON compliance.
        """
        json_schema = json.dumps(response_model.model_json_schema(), indent=2)
        system_instruction = messages[0]["content"] + f"\n\nReturn EXACTLY valid JSON matching this schema:\n{json_schema}"
        messages[0]["content"] = system_instruction
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            raw_content = completion.choices[0].message.content
            if not raw_content:
                raise ValueError(f"Provider {self.provider} returned an empty response.")
                
            # Parse and validate against the provided Pydantic model
            return response_model.model_validate_json(raw_content)
            
        except Exception as error:
            # If we hit a Rate Limit error (429), trigger the circuit breaker for this provider.
            if "429" in str(error):
                logger.warning(f"Rate limit hit for {self.model}. Tripping circuit for {self.provider}.")
                mark_failure(self.provider)
            raise error

def make_llm_client(role: str, tier: str = "cheap") -> Optional[LLMClient]:
    """
    Factory function to create an LLMClient based on role and tier.
    Automatically handles provider cooldowns and falls back to secondary options.
    """
    models_cfg = load_config("models")
    if not models_cfg or "roles" not in models_cfg:
        logger.error("LLM configuration is missing 'roles' section.")
        return None
        
    role_settings = models_cfg["roles"].get(role)
    if not role_settings:
        logger.error(f"Role '{role}' is not defined in models configuration.")
        return None
    
    # Select the model tier (e.g., 'cheap' or 'premium')
    tier_settings = role_settings.get(tier) or list(role_settings.values())[0]
    provider_name = tier_settings["provider"]
    provider_cfg = models_cfg["providers"].get(provider_name)
    
    # Circuit Breaker Logic: Check if the provider is currently cooling down
    if not is_cooled_down(provider_name):
        logger.warning(f"Provider '{provider_name}' is currently offline. Attempting fallback.")
        if tier != "fallback":
            return make_llm_client(role, tier="fallback")
    
    # Retrieve API key for the chosen provider
    api_key_env_var = provider_cfg.get("api_key_env")
    api_key = os.environ.get(api_key_env_var)
    if not api_key:
        logger.error(f"Required API Key '{api_key_env_var}' is missing from .env file.")
        
    client_instance = OpenAI(
        base_url=provider_cfg.get("base_url"),
        api_key=api_key or "missing"
    )
    
    return LLMClient(
        client=client_instance, 
        model=tier_settings["model"], 
        temperature=tier_settings.get("temperature", 0.0), 
        max_tokens=tier_settings["max_tokens"],
        provider=provider_name
    )
