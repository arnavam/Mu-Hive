# 🐝 MuHive v1: High-Efficiency Discovery Engine

MuHive v1 is a production-grade, configuration-driven AI pipeline that autonomously discovers, verifies, and structures technical opportunities for student Interest Groups.

## 🚀 The High-Efficiency Engine (v1)
This version features a sophisticated modular architecture designed for maximum reliability and cost-efficiency, consolidating scraping techniques from all project branches into a unified, parallelized core.

- **Tiered Model Routing**: Intelligently routes tasks to different AI "Brains" (e.g., Groq 70B for premium IGs, Llama 8B for general tasks) via `models.yaml`.
- **Status-Aware Caching**: Uses a dictionary-based hash database (`seen_hashes.json`) to skip previously verified or structured items, reducing redundant LLM calls.
- **Circuit Breaker & Fallbacks**: Detects provider outages (429/500) and automatically shifts to **OpenRouter** fallbacks with configurable cooldown periods.
- **Parallelized Processing**: Uses `asyncio` semaphores to manage high-throughput processing while strictly respecting Free-Tier rate limits (RPM/TPM).
- **Stealth & Resilience**: Mimics real browser behavior with randomized jitter and User-Agent rotation.

---

## 📂 Project Structure

```text
MuHive/
├── main.py              # The Master Orchestrator
├── config/              # ALL logic settings (No code changes needed!)
│   ├── sources.yaml     # Scraper targets (RSS, Search, Sites)
│   ├── groups.yaml      # Interest Group definitions & keywords
│   ├── models.yaml      # Tiered Routing & LLM parameters
│   └── settings.yaml    # Concurrency, Quotas, and Rate Limits
├── src/
│   ├── pipeline/        # The Modular Stages (01-05)
│   ├── config.py        # Centralized YAML & .env loader
│   ├── llm_client.py    # Multi-brain client with rate limiting
│   ├── state_manager.py # Hashing & Persistence logic
│   └── [utils...]       # Focused helper modules (HTTP, Retry, Circuit)
├── tests/               # Pytest Unit Suite & Diagnostic Scripts
├── state/               # Persistent data (Hashes, Circuit states)
├── output/              # Final processed data (JSON, CSV)
└── .env.example         # Environment template
```

---

## 🛠️ Quick Start

### 1. Installation
```bash
# Recommended: Create a virtual environment first
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration
Copy the template and fill in your API keys:
```bash
cp .env.example .env
```

### 3. Execution
```bash
# Run for a specific Interest Group
python main.py --ig AI

# Run for all active groups
python main.py
```

---

## 🧪 Testing & Maintenance

- **Unit Tests**: Run the full test suite with `pytest tests/`.
- **Status Reset**: To re-process items, run `rm state/seen_hashes.json`.
- **Circuit State**: Check `state/circuit_state.json` to monitor current provider cooldowns.
- **Hardening**: All rate limits and concurrency settings are controlled via `config/settings.yaml`.

## 🏆 Key Technologies
- **Python 3.10+**: Core logic and Asyncio.
- **Groq & OpenRouter**: Primary and fallback AI "Brains".
- **Tavily**: Advanced search fallback.
- **Pydantic**: Strict data validation & schema extraction.
- **Trafilatura & BeautifulSoup**: Multi-layer content extraction.
- **Tenacity**: Robust exponential backoff for network resilience.
