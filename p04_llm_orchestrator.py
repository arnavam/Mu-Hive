"""
MuHive LLM Factory
──────────────────
Standardized way to initialize Chat Models from different providers.
Supports Groq, Gemini, and OpenRouter.

Functions:
- make_fast_llm: Returns a model for quick classification (Stage 2a)
- make_quality_llm: Returns a model for deep analysis (Stage 2c)
"""

import os
from typing import Any
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

def make_fast_llm(provider: str, cfg: dict) -> Any:
    """
    Initialize a 'fast' model (usually Groq Llama-3).
    """
    if provider == "groq":
        return ChatGroq(
            model=cfg["stage2"]["models"]["groq"],
            temperature=0.0,
            api_key=os.environ.get("GROQ_API_KEY", ""),
        )
    elif provider == "openrouter":
        return ChatOpenAI(
            model=cfg["stage2"]["models"]["openrouter_fast"],
            temperature=0.0,
            api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            base_url="https://openrouter.ai/api/v1",
        )
    raise ValueError(f"Unsupported fast provider: {provider}")

def make_quality_llm(provider: str, cfg: dict) -> Any:
    """
    Initialize a 'high-quality' model (usually Gemini 1.5).
    """
    if provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=cfg["stage2"]["models"]["gemini"],
            temperature=0.0,
            google_api_key=os.environ.get("GEMINI_API_KEY", ""),
        )
    elif provider == "openrouter":
        return ChatOpenAI(
            model=cfg["stage2"]["models"]["openrouter_quality"],
            temperature=0.0,
            api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            base_url="https://openrouter.ai/api/v1",
        )
    raise ValueError(f"Unsupported quality provider: {provider}")
