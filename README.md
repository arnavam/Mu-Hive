# Mu-Hive  

(Define whats Mu-hive here!)
---

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

# Install dependencies
pip install -r requirements.txt
```

### Next Steps
*   Define core schemas in `src/db/`.
*   Implement basic LLM wrapper in `src/llm/`.
*   Create the first agents in `src/agents/`.

