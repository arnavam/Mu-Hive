import os
import sys
import logging
from dotenv import load_dotenv
from pydantic_ai.models.groq import GroqModel

load_dotenv()
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Fail fast if API key is missing — don't let the pipeline silently break
if not GROQ_API_KEY:
    logger.error(
        "GROQ_API_KEY is not set. "
        "Create a .env file with your key: GROQ_API_KEY=gsk_..."
    )
    sys.exit(1)

model = GroqModel(model_name=GROQ_MODEL_NAME)
logger.info(f"LLM configured: Groq/{GROQ_MODEL_NAME}")

import os

# Placeholder for LLM configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))
