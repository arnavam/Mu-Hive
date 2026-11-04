import os
import sys
import logging
from dotenv import load_dotenv

# Must run before any logging call: Windows cp1252 cannot encode the arrow
# and emoji used in console output.
from src.config.console import configure_stdio
configure_stdio()
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.exceptions import ModelAPIError
from pydantic_ai.settings import ModelSettings

load_dotenv()
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ── Shared LLM settings (env-configurable) ──
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "512"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
shared_model_settings = ModelSettings(
    max_tokens=MAX_TOKENS,
    temperature=TEMPERATURE,
)

# Fail fast if API key is missing — don't let the pipeline silently break
if not GROQ_API_KEY:
    logger.error(
        "GROQ_API_KEY is not set. "
        "Create a .env file with your key: GROQ_API_KEY=gsk_..."
    )
    sys.exit(1)

# ── Build model chain: bulk Groq → configured Groq → OpenRouter fallback ──
# Daily bulk classification is routed to the high-TPD free model first.
# GROQ_MODEL (if different) stays as a quality fallback.
BULK_MODEL_NAME = os.getenv("GROQ_BULK_MODEL", "openai/gpt-oss-20b")
ACTIVE_BULK_MODEL = BULK_MODEL_NAME

chain_names: list[str] = []
if GROQ_MODEL_NAME != BULK_MODEL_NAME:
    chain_names.append(BULK_MODEL_NAME)
    chain_names.append(GROQ_MODEL_NAME)
else:
    chain_names.append(GROQ_MODEL_NAME)

groq_models = {name: GroqModel(model_name=name) for name in chain_names}
primary_model = groq_models[chain_names[0]]

fallback_models = [groq_models[name] for name in chain_names[1:]]

# Add OpenRouter as final fallback
if OPENROUTER_API_KEY:
    from pydantic_ai.providers.openai import OpenAIProvider
    openrouter_provider = OpenAIProvider(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )
    openrouter_model = OpenAIModel(
        model_name="google/gemini-2.5-flash",
        provider=openrouter_provider,
    )
    fallback_models.append(openrouter_model)
    logger.info("OpenRouter fallback enabled (google/gemini-2.5-flash)")

from src.utils.groq_quota import groq_quota_available, parse_and_record_groq_usage

class QuotaAwareFallbackModel(FallbackModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._all_models = list(self.models)

    @property
    def models(self):
        from pydantic_ai.models.groq import GroqModel
        # Drop only Groq models whose own daily budget is exhausted, keeping
        # any model that still has headroom (and always keeping non-Groq).
        filtered = [
            m for m in self._all_models
            if not (isinstance(m, GroqModel)
                    and not groq_quota_available(getattr(m, "model_name", None)))
        ]
        if filtered and len(filtered) != len(self._all_models):
            logger.info(
                "Groq daily budget guard active — routing to: %s",
                ", ".join(type(m).__name__ for m in filtered),
            )
        return filtered or self._all_models

    @models.setter
    def models(self, value):
        self._all_models = value

def _should_fallback(exc: Exception) -> bool:
    if isinstance(exc, ModelAPIError):
        logger.warning(f"LLM API error: {exc}. Falling back to next model...")
        err_msg = str(exc)
        if "429" in err_msg or "rate limit" in err_msg.lower():
            parse_and_record_groq_usage(err_msg)
        return True
    return False

if fallback_models:
    model = QuotaAwareFallbackModel(primary_model, *fallback_models, fallback_on=[_should_fallback])
    names = list(chain_names)
    if OPENROUTER_API_KEY:
        names.append("openrouter/gemini-2.5-flash")
    logger.info(f"LLM configured with fallback chain: {' -> '.join(names)}")
else:
    model = primary_model
    logger.info(f"LLM configured: Groq/{chain_names[0]}")


