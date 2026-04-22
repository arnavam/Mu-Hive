import pytest
import os
from unittest.mock import patch, MagicMock
from src.llm import make_llm_client

@pytest.fixture
def mock_models_cfg():
    return {
        "providers": {
            "groq": {
                "base_url": "https://api.groq.com/openai/v1",
                "api_key_env": "GROQ_API_KEY",
                "rpm": 30
            },
            "openrouter": {
                "base_url": "https://openrouter.ai/api/v1",
                "api_key_env": "OPENROUTER_API_KEY",
                "rpm": 10
            }
        },
        "roles": {
            "verifier": {
                "cheap": {
                    "provider": "groq",
                    "model": "llama-3.1-8b-instant",
                    "temperature": 0.1,
                    "max_tokens": 500
                },
                "fallback": {
                    "provider": "openrouter",
                    "model": "openai/gpt-oss-120b:free",
                    "temperature": 0.1,
                    "max_tokens": 500
                }
            }
        }
    }

@patch("src.llm.load_config")
@patch("src.llm.is_cooled_down")
@patch("src.llm.OpenAI")
def test_make_llm_client_returns_correct_model(mock_openai, mock_cooled_down, mock_load_config, mock_models_cfg):
    # Setup
    mock_load_config.return_value = mock_models_cfg
    mock_cooled_down.return_value = True # Not in cooldown
    
    # Run
    client_wrapper = make_llm_client("verifier", tier="cheap")
    
    # Assert
    assert client_wrapper.model == "llama-3.1-8b-instant"
    assert client_wrapper.provider == "groq"

@patch("src.llm.load_config")
@patch("src.llm.is_cooled_down")
@patch("src.llm.OpenAI")
def test_make_llm_client_falls_back_on_cooldown(mock_openai, mock_cooled_down, mock_load_config, mock_models_cfg):
    # Setup
    mock_load_config.return_value = mock_models_cfg
    # First call for 'groq' returns False (is in cooldown)
    # Second call for 'openrouter' returns True (is NOT in cooldown)
    mock_cooled_down.side_effect = [False, True]
    
    # Run
    client_wrapper = make_llm_client("verifier", tier="cheap")
    
    # Assert
    assert client_wrapper.model == "openai/gpt-oss-120b:free"
    assert client_wrapper.provider == "openrouter"
