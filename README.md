# Mu-Hive Intelligence Pipeline 🐝

Mu-Hive is an autonomous, multi-agent AI pipeline that discovers, evaluates, and curates global tech opportunities from RSS feeds. It uses LLM-powered intelligence to score and classify articles, then presents a curated digest — all running locally from your machine.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     main.py (Orchestrator)                      │
│         Executes each phase sequentially via function calls     │
└────────┬──────────────┬──────────────────┬──────────────────────┘
         │              │                  │
         ▼              ▼                  ▼
   ┌──────────┐  ┌──────────────┐  ┌──────────────────┐
   │  Phase 2  │  │   Phase 3    │  │     Phase 4      │
   │   Scout   │  │ Intelligence │  │  Communicator    │
   │  Agent    │  │    Agent     │  │  (Planner +      │
   │           │  │              │  │   Display)       │
   └────┬─────┘  └──────┬───────┘  └────────┬─────────┘
        │               │                   │
        │         ┌─────┴─────┐              │
        │         │ Groq API  │              │
        │         │ (LLM)     │              │
        │         └───────────┘              │
        │                                    │
        ▼                ▼                   ▼
   ┌─────────────────────────────────────────────┐
   │            mu_hive.db (SQLite)              │
   │         opportunities table                  │
   └─────────────────────────────────────────────┘
```

## Pipeline Phases

| Phase | Agent | What It Does |
|-------|-------|--------------|
| **Phase 1** | Database Init | Creates the SQLite database and `opportunities` table |
| **Phase 2** | Scout | Parses 20+ RSS feeds, extracts articles, stores them in the DB |
| **Phase 3** | Intelligence | Sends each article to Groq LLM for quality scoring (1-10) and Interest Group classification |
| **Phase 4** | Communicator | Queries top-scored articles per IG and displays a formatted digest in the terminal |

## Project Structure

```
Mu-Hive/
├── main.py                    # Entry point — runs the full pipeline
├── .env                       # Your Groq API key (not committed)
├── .env.example               # Template for .env
├── requirements.txt           # Python dependencies
├── mu_hive.db                 # SQLite database (auto-created)
├── scripts/
│   └── verify_setup.py        # Pre-flight check for DB + API key
└── src/
    ├── __init__.py
    ├── agents/
    │   ├── __init__.py
    │   ├── scout.py            # Phase 2: RSS feed scraper
    │   ├── intelligence.py     # Phase 3: LLM evaluator + classifier
    │   ├── planner.py          # Queries DB for top articles per IG
    │   └── communicator.py     # Phase 4: Terminal digest display
    ├── config/
    │   ├── __init__.py
    │   └── sources.py          # List of RSS feed URLs
    ├── db/
    │   ├── __init__.py
    │   └── database.py         # SQLite connection + schema init
    └── llm/
        ├── __init__.py
        └── agent_config.py     # Groq model setup + API key validation
```

## File Reference

### `main.py`
The orchestrator. Loads environment variables, initializes the database, then executes Scout → Intelligence → Communicator in sequence.

### `src/agents/scout.py`
Parses all RSS feeds defined in `sources.py`. For each feed, it extracts the title, link, and summary of up to 10 entries. Articles are inserted into the `opportunities` table with a `UNIQUE` constraint on `link` to prevent duplicates.

### `src/agents/intelligence.py`
The LLM-powered brain. Fetches unprocessed articles from the database, sends each one to Groq with a structured Pydantic schema, and receives back:
- **is_relevant**: spam filter (bool)
- **quality_score**: 1-10 quality rating
- **reasoning**: 1-sentence justification
- **ig_tags**: Interest Group classification (AI, Data Science, Web Development, Cyber Security, UI/UX)

Processes up to 15 articles per run to conserve API quota.

### `src/agents/planner.py`
Queries the database for the top 5 highest-scored articles (score ≥ 5) in each Interest Group. Returns a dictionary mapping each IG to its best articles.

### `src/agents/communicator.py`
Takes the planner's output and formats it into a readable terminal digest with titles, scores, links, and summaries.

### `src/config/sources.py`
A curated list of ~20 RSS feed URLs covering major tech news, AI research, and community aggregators.

### `src/db/database.py`
Manages the SQLite database. Provides `get_connection()` for all modules and `init_db()` to create the schema.

### `src/llm/agent_config.py`
Configures the Groq LLM model using Pydantic AI's `GroqModel`. Validates that the API key exists at startup and exits immediately if missing.

### `scripts/verify_setup.py`
A diagnostic script that checks if the database is accessible and the Groq API key is set. Run this before the pipeline to catch config issues early.

## Setup & Running

### Prerequisites
- Python 3.10+
- A free Groq API key ([get one here](https://console.groq.com/keys))

### Step 1: Create Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Configure API Key
```powershell
copy .env.example .env
```
Edit `.env` and paste your Groq API key:
```
GROQ_API_KEY=gsk_your_actual_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

### Step 4: Verify Setup
```powershell
python scripts/verify_setup.py
```

### Step 5: Run the Pipeline
```powershell
python main.py
```

### Running Individual Agents
You can run any agent independently:
```powershell
python -m src.agents.scout          # Only collect RSS articles
python -m src.agents.intelligence   # Only evaluate unprocessed articles
python -m src.agents.communicator   # Only display the digest
python -m src.db.database           # Only initialize the database
```

## Configuration

| Environment Variable | Required | Default | Description |
|---------------------|----------|---------|-------------|
| `GROQ_API_KEY` | ✅ Yes | — | Your Groq API key |
| `GROQ_MODEL` | No | `llama-3.1-8b-instant` | Groq model to use |
| `DB_PATH` | No | `mu_hive.db` | Path to SQLite database file |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `GROQ_API_KEY is not set` | Create a `.env` file with your key. See Step 3 above. |
| `ModuleNotFoundError` | Make sure your virtual environment is activated and dependencies are installed. |
| `No entries found` for a feed | The RSS feed may be temporarily down or have changed its URL. Check `src/config/sources.py`. |
| `No new opportunities require evaluation` | All articles have already been evaluated. Delete `mu_hive.db` to start fresh. |
| Database locked errors | Ensure only one instance of the pipeline is running at a time. |
