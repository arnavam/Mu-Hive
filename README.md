# 🚀 Production Hackathon Aggregator

A high-speed, asynchronous scraper and intelligent curation engine designed initially for engineering students. The project dynamically fetches thousands of open hackathons across major platforms globally without triggering rate limits, and curates them into an elegant terminal dashboard organized by specific Interest Groups (IGs).

## Core Features
1. **Ultra-Fast API Scraper**: Completely bypasses browser automation. Uses direct, paginated JSON/GraphQL APIs with `aiohttp` and `asyncio`.
2. **4 Platforms Supported**: Devfolio, Unstop, Devpost, HackerEarth.
3. **Intelligent Curation Strategy**: Scores datasets heavily favoring proximity, eligibility (student/college), zero cost, and monetary rewards.
4. **Keyword & IG Mapping Engine**: Implements a strict-match dictionary logic mapping scattered tags uniquely to 29 distinctive technological domains (AI, Web, Civil etc).
5. **Freshness Filter Algorithm**: Extensively parses mixed datetime formats/strings (ISO, ranges) to instantly discard and remove expired events from surfacing to the UI.

## File Breakdown
- **`advanced_scraper.py`**: The dynamic scraper generating concurrency over API fetches for maximum performance. Dumps records into `hackathons.json`.
- **`curate.py`**: The offline filtration and grouping dashboard. Eliminates expired dates, associates metadata tags to exact master areas, limits visually displayed instances strictly to the Top 5 most prominent instances per domain.

## Execution
First, install the sole required dependency:
```bash
pip install aiohttp
```

Then, execute the scraper to pull events directly from endpoints:
```bash
python advanced_scraper.py
```

Finally, review the sorted terminal visualization UI:
```bash
python curate.py
```
