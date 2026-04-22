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

## 🚀 Current Project State: Multi-Agent Intelligence Pipeline

The project is now a fully functional multi-agent intelligence pipeline designed to discover, scrape, and structure event-based data (Hackathons, Internships, Conferences) into a centralized database.

### 🧠 Core Intelligence System
*   **Scout Agent**: Leverages **Firecrawl** to perform deep web scraping and site crawling, extracting high-fidelity markdown and metadata.
*   **Intelligence Agent**: Powered by **Groq (Llama 3.1)** and **Gemini 3 Flash**, this agent performs structured data extraction and generates concise technical summaries of raw content.
*   **Orchestrator**: A central coordinator that manages the sequential flow: **Scrape → Store Raw → Analyze → Upsert Structured Data**.

### 📊 Data Architecture (PostgreSQL)
We use a dual-layer storage strategy for maximum reliability and data integrity:
*   **`scraped_data`**: A storage layer for raw JSONB payloads from Firecrawl.
*   **`events`**: A structured table for normalized event data including:
    *   `title`, `type`, `platform`, `location`, `link` (Unique Key), `days_left`, `ig_handle`, and an AI-calculated `score`.

---

## 🛠️ Getting Started

### 1. Environment Setup
Copy `.env.example` to `.env` and fill in your credentials:
```env
FIRECRAWL_API_KEY=your_key
GROQ_API_KEY=your_key
DATABASE_URL=postgresql://user:pass@localhost:5432/mu_hive
```

### 2. Installation
```bash
# Install dependencies
pip install -r requirements.txt
```

### 3. Execution
*   **CLI Mode**: `python main.py --urls https://example.com --mode scrape`

---

## 📂 Project Structure
*   `src/orchestrator.py`: The "brain" managing the data pipeline.
*   `src/agents/`: specialized AI agents (`scout`, `intelligence`).
*   `src/db/`: Scalable Database Module
    *   `connection.py`: Centralized PostgreSQL connection management.
    *   `schema.py`: Table definitions and initialization logic.
    *   `repositories/`: Domain-specific data access objects (Scrape, Event).
    *   `database.py`: High-level Facade for application-wide use.
*   `main.py`: The primary CLI entry point.
---

## 🛠️ Group Project Scalability: Database Architecture

To ensure the project remains maintainable as the team grows, we have refactored the database layer into a decoupled, scalable architecture:

### 🧩 Components
*   **Connection Management (`connection.py`)**: Centralizes PostgreSQL connection logic using a singleton pattern. This ensures efficient resource usage and simplifies debugging of database connectivity.
*   **Schema Isolation (`schema.py`)**: Separates table definitions and initialization from application logic. This makes it easier to track schema changes and perform migrations as a group.
*   **Repository Pattern (`repositories/`)**: We use specialized "Repositories" for different data domains:
    *   `ScrapeRepository`: Focused on high-volume raw JSON data storage.
    *   `EventRepository`: Focused on structured, high-integrity event records with upsert logic.
*   **Facade Interface (`database.py`)**: Provides a clean, unified entry point for the rest of the application. Developers only need to interact with the `db` instance, while the underlying complexity is hidden.

### 👥 Team Benefits
- **Zero Merge Conflicts**: By splitting logic into multiple files, teammates can work on different data models (e.g., adding a new `users` table) without touching the same files.
- **Improved Testing**: Repositories can be unit-tested in isolation using mock database connections.
- **Clear Ownership**: Files are organized by domain, making it clear where specific logic (like an SQL query) resides.
