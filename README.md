# 🐝 MuHive v1: Modular Agentic Discovery Engine

MuHive v1 is a state-of-the-art, modular AI pipeline designed to autonomously discover, verify, and structure technical opportunities for student Interest Groups. It uses a multi-agent architecture to ensure high data quality and system resilience.

## 🚀 Key Features

- **Agentic Multi-Stage Pipeline**: Clear separation between Scraping, Classification, Validation, and Summarization agents.
- **Tiered Model Routing**: Intelligently routes tasks to different AI models (e.g., Groq 70B for premium tasks, Llama 8B for general filtering).
- **Consolidated Configuration**: All system settings, sources, and interest groups are managed through a single `config.yaml`.
- **Status-Aware Caching**: Uses a hash database (`data/seen_hashes.json`) to deduplicate and track processing states.
- **Circuit Breaker & Fallbacks**: Automatically detects provider outages and shifts to fallbacks with configurable cooldowns.

---

## 📂 Project Structure

```text
MuHive/
├── config.yaml          # SINGLE source of truth for all configuration
├── main.py              # Entry point for the orchestrator
├── data/                # Persistent data (Hashes, Circuit states, Exports)
├── src/
│   ├── agents/          # Modular AI Agent personas (Classifier, Validater, Summarizer)
│   ├── scraping/        # Specialized scrapers (RSS, Search, Site, API)
│   ├── db/              # Database and Data Schema management
│   ├── llm/             # LLM Client and provider abstractions
│   ├── config/          # Configuration loader and constants
│   ├── orchestrator.py  # Central coordinator for the pipeline
│   ├── agent_config.py  # Agent-specific routing and personas
│   └── [utils...]       # Focused helpers (HTTP, Retry, Circuit Breaker)
└── .env.example         # Template for required API keys
```

---

## 🛠️ Quick Start

### 1. Installation
```bash
# Recommended: Use the existing virtual environment
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration
Copy the template and fill in your API keys (Groq, Together, NewsAPI, Tavily, etc.):
```bash
cp .env.example .env
```
Edit `config.yaml` to customize your Interest Groups and sources.

### 3. Execution
```bash
# Run for a specific Interest Group
python main.py --ig AI

# Run for all active groups
python main.py
```

---

## 🏆 Key Technologies
- **Python 3.12+**: Core logic and Asyncio.
- **Groq & OpenRouter**: High-speed LLM inference.
- **Tavily & DuckDuckGo**: Advanced search capabilities.
- **Pydantic**: Robust data validation and schema handling.
- **Trafilatura**: Professional-grade web content extraction.
- **Tenacity**: resilient exponential backoff handling.
- **Loguru**: Structured and beautiful logging.
