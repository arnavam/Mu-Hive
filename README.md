# Mu-Hive  

## 🏗️ Project Blueprint

Here is the structure we are building:

### Root Files
*   **`.env.example` ->** Template for required API keys (OpenAI, Tavily, etc.).
*   **`requirements.txt` ->** To be filled with project dependencies.
*   **`config.yaml` ->** System-wide non-secret configurations.
*   **`main.py` ->** The future entry point for the entire application.

### The Source (`src/`)
*   **`src/orchestrator.py` ->** The central logic that will coordinate agents and data flow.
*   **`src/agents/` ->** Folder for specialized AI personas (Scout, Planner, etc.).
*   **`src/llm/` ->** Wrappers and prompts for interacting with AI models.
*   **`src/scraping/` ->** Tools for fetching raw data from the web.
*   **`src/db/` ->** Database schemas and connection logic.
*   **`src/config/` ->** Internal code configurations and constants.

### Utilities & Data
*   **`scripts/` ->** One-off scripts for testing and setup verification.
*   **`tests/` ->** Unit and integration tests for each module.
*   **`data/` ->** Storage for raw exports (JSON/CSV).

---

## 🛠️ Current Status: Bootstrapping

###  Installation

#### Using `uv` 
```bash
# Install dependencies
uv init
uv add -r requirements.txt
```

#### Using standard `pip`
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

## 🚀 Current Status: Multi-Agent Intelligence Pipeline
The project is now a functional multi-agent pipeline with a web interface.

### Key Features
*   **Scout Agent**: Uses **Firecrawl** for high-quality web scraping and crawling.
*   **Intelligence Agent**: Uses **Groq (Llama 3.1)** to extract structured event data and generate summaries.
*   **Structured Storage**: Dual-layer storage using **PostgreSQL**:
    *   `scraped_data`: Stores raw web content.
    *   `events`: Stores structured event details (title, location, score, etc.) with upsert logic.
*   **Web UI**: A modern Flask-based dashboard to run extractions and visualize results.

### Running the Project
1.  **Environment Setup**:
    *   Copy `.env.example` to `.env`.
    *   Fill in `FIRECRAWL_API_KEY`, `GROQ_API_KEY`, and `DATABASE_URL`.
2.  **Installation**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run via CLI**:
    ```bash
    python main.py --urls https://example.com --mode scrape
    ```
4.  **Run via Web UI**:
    ```bash
    python app.py
    ```

### Project Structure
*   `src/orchestrator.py`: Manages the "Store Raw -> Analyze -> Upsert Final" flow.
*   `src/agents/`: specialized AI agents (Scout, Intelligence).
*   `src/db/database.py`: PostgreSQL schema and operations.
*   `templates/`: Web dashboard files.
