# 🐝 MuHive v1: High-Efficiency Discovery Engine

MuHive v1 is a production-grade, configuration-driven AI pipeline that autonomously discovers, verifies, and structures technical opportunities for student Interest Groups.

## 🚀 The High-Efficiency Engine (v1)
This version features a sophisticated multi-brain architecture designed for maximum reliability and cost-efficiency, consolidating every scraping technique from all project branches.

- **Tiered Model Routing**: Intelligently routes tasks to different AI "Brains" (e.g., Groq 70B for premium IGs like AI/Cyber, Llama 8B for general tasks) to optimize precision vs. cost.
- **Status-Aware Caching**: Uses a persistent metadata-rich hash database to **skip** previously verified or structured items, reducing redundant LLM calls by up to 90%.
- **Circuit Breaker & Fallbacks**: Automatically detects provider outages (429/500) and switches to Together AI fallbacks with a 5-minute cooldown mechanism.
- **Stealth & Resilience**: Mimics real browser behavior with randomized jitter and User-Agent rotation to bypass scraper protections.
- **Zero-Code Scaling**: Manage everything (sources, model tiers, interest groups, result caps) purely through YAML configurations.

---

## 📂 Project Structure

```
MuHive/
├── src/                 # The Production Logic (Numbered by Flow)
│   ├── stage_01_scraper.py
│   ├── stage_02_filter.py 
│   ├── stage_03_verifier.py
│   ├── stage_04_structurer.py
│   ├── stage_05_writer.py
│   ├── utils.py         # Shared Helpers (Limiters, Circuit Breaker)
│   └── schemas.py       # Pydantic Data Models
├── config/              # ALL logic settings (No code changes needed!)
│   ├── sources.yaml
│   ├── groups.yaml
│   ├── models.yaml      # Tiered Routing Config
│   └── settings.yaml    # Quotas and Rate Limits
├── state/               # Persistence (Hashes with Status, Cooldowns)
├── output/              # Final processed data
├── main.py              # The Master Orchestrator
└── requirements.txt     # Optimized dependencies
```

---

## 🛠️ Quick Start

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Configuration (API Keys)
Create a file named **`.env`** in the root directory:
```bash
TOGETHER_API_KEY=your_key
GROQ_API_KEY=your_key
TAVILY_API_KEY=your_key
NEWSAPI_KEY=your_key
APIFY_API_TOKEN=your_key
```

### 3. Execution
Run for a specific Interest Group or the entire list:

```bash
# Run for AI group only
python main.py --ig AI

# Run for all active groups
python main.py
```

---

## 🧪 Maintenance & Ops

- **Status Reset**: To re-process previously seen items, run `rm state/seen_hashes.json`. Note that items marked as "structured" are skipped entirely unless the cache is cleared.
- **Circuit State**: Check `state/circuit_state.json` to see which providers are currently in cooldown.
- **Advanced Scraping**: Includes NewsAPI, Apify Social Social Monitoring, and specialized API scrapers for Unstop, Devfolio, etc.

## 🏆 Key Technologies
- **Python 3.10+**: Core logic and Asyncio.
- **Groq & Together AI**: High-performance "Brains".
- **Tavily**: Advanced search fallback.
- **Pydantic**: Strict data validation.
- **Trafilatura & BeautifulSoup**: Multi-layer content extraction.
- **Httpx**: Modern, async HTTP client with user simulation.
