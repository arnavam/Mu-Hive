# Mu-Hive

Agents that **search the web for links**, store them in **MongoDB**, then **scrape each page** and save titles, descriptions, and text summaries on the same records. You can browse results in **MongoDB Compass** or any MongoDB client.

---

## What this project does

1. **Search agent** — Builds queries from keywords and categories, searches with **DuckDuckGo** (and **Tavily** if DuckDuckGo fails and an API key is set). Each new result is inserted into MongoDB with `status: "not processed"`. Duplicates are avoided using the pair `(link, keyword_used)`.

2. **Scraper agent** — Finds documents that are still `"not processed"`, downloads each URL, extracts readable content from the HTML, and updates that document with `status: "scraped"` or `"scrape_failed"` plus the scraped fields.

3. **Full run** — `main.py` runs the search agent first, then the scraper agent, so new links are collected and then enriched in one go.

---

## Prerequisites

- **Python** 3.10 or newer (recommended)
- **MongoDB** running and reachable (default in code: `mongodb://localhost:27017/`)
- **Internet** for search and for fetching web pages

---

## Step-by-step: first-time setup

Do these steps from the **`Mu-Hive`** directory (the folder that contains `main.py`, `requirements.txt`, and the other scripts).

### Step 1 — Create a virtual environment

**Windows (PowerShell or Command Prompt):**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2 — Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Start MongoDB

Start your MongoDB service (local install, Docker, or Atlas). The code expects the default connection unless you change it in `database.py` inside the `Database(...)` constructor.

- **Database name:** `mu_hive`
- **Collection:** `events`

### Step 4 — (Optional) Tavily API key for fallback search

If DuckDuckGo errors or is blocked, the search agent can use **Tavily**.

1. Create a file named `.env` in the **`Mu-Hive`** folder (same folder as `search_engine.py`).
2. Add one line (use your real key from [https://app.tavily.com](https://app.tavily.com)):

   ```
   TAVILY_API_KEY=tvly-your_key_here
   ```

The project loads this `.env` from the script directory, so it still works if you run commands from another folder.

---

## Step-by-step: how to run

Always activate the virtual environment first (Step 1 above), then work from **`Mu-Hive`**.

### Option A — Full pipeline (recommended)

Runs search, then scrape:

```bash
python main.py
```

### Option B — Search only

Adds new links to MongoDB; they stay `"not processed"` until you scrape:

```bash
python search_engine.py
```

### Option C — Scrape only

Processes up to 50 pending documents per run (default). Use this after search, or to retry failed pages:

```bash
python scraper_agent.py
```

---

## Project layout (main files)

| File | Role |
|------|------|
| `main.py` | Runs search agent, then scraper agent |
| `search_engine.py` | Search + insert into MongoDB |
| `scraper_agent.py` | Fetch URLs, parse HTML, update MongoDB |
| `database.py` | MongoDB connection and helpers |
| `requirements.txt` | Python packages |

---

## Troubleshooting (short)

- **Cannot connect to MongoDB** — Ensure the server is running and the URI in `database.py` matches your setup.
- **No scrape results / many `scrape_failed`** — Some sites block automated requests; that is normal for a simple scraper.
- **Search returns nothing** — Check network access; if using Tavily, confirm `TAVILY_API_KEY` in `.env`.
