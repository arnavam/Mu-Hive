# 🐝 Mu-Hive: Intelligence & Extraction Service

This directory contains the **Intelligence & Extraction Engine** for the Mu-Hive project. It is a multi-agent pipeline designed to autonomously scout, analyze, and store technical technical data from the web.

> [!NOTE]
> This is a component of the larger Mu-Hive ecosystem, focusing on the data acquisition and AI-driven intelligence layer.

---

## 🏗️ Project Structure

The project follows a decoupled, agentic architecture to ensure each component can be scaled or modified independently.

```text
IG PROJECT/
├── main.py                 # CLI Entry Point (Batch processing & Pipeline execution)
├── app.py                  # Optional Web Dashboard (Flask-based visualization)
├── requirements.txt        # Project dependencies
├── src/
│   ├── agents/             # Core AI Agents
│   │   ├── scout.py        # ScoutAgent: Handles Firecrawl scraping & serialization
│   │   ├── intelligence.py  # IntelligenceAgent: Handles LLM-based summarization (Groq)
│   │   └── planner.py      # PlannerAgent: Orchestrates the Scrape -> Analyze -> Store flow
│   ├── db/
│   │   └── database.py     # MongoDB connection & data persistence logic
│   ├── config/
│   │   └── settings.py     # Environment variable management
│   └── llm/
│       └── agent_config.py # LLM hyperparameter configurations
└── templates/              # Dashboard UI components (HTML/JS)
```

---

## ⚙️ Core Pipeline Logic

The system operates on an automated pipeline managed by the **Planner Agent**:

1.  **Scouting**: The `ScoutAgent` uses the Firecrawl API to extract high-quality Markdown from target URLs (single page or full crawl).
2.  **Intelligence**: The raw data is passed to the `IntelligenceAgent`, which uses **Groq (Llama-3.1-8B)** to generate concise technical summaries.
3.  **Persistence**: The resulting intelligence (URL, raw data, and AI summary) is stored in **MongoDB Atlas** for use by other Mu-Hive modules.

---

## 🚀 Usage

### Standalone Pipeline (Recommended for Group Integration)
Use the CLI to process tasks in the background or batch.
```bash
# Single URL
python main.py --urls https://example.com

# Batch URLs
python main.py --urls site1.com site2.com --mode crawl

# Load from file
python main.py --file targets.txt
```

### Dashboard (For Visualization)
```bash
python app.py
```
Visit `http://localhost:5000` to interact with the scraper and view AI summaries in real-time.

---

## 🛠️ Configuration
Ensure your `.env` contains the keys for the components:
- `FIRECRAWL_API_KEY`: For web extraction.
- `GROQ_API_KEY`: For AI analysis.
- `MONGO_URI`: For data persistence.

---

## 👥 Contributors
This is a group project. Please ensure that logic changes are made within the `src/agents/` directory to maintain the decoupled architecture.
