# Mu-Hive Search Engine Agent

This project collects event links from search engine and stores them in MongoDB.

## Setup

1. Clone the repository

2. Create virtual environment

   ```bash
   python -m venv .venv
   ```

3. Activate environment

   **Windows:**
   ```bash
   .venv\Scripts\activate
   ```

4. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

5. Configure environment variables

   Copy `.env.example` or create a `.env` file in the project root and add your Tavily API key:
   ```
   TAVILY_API_KEY=tvly-your_actual_api_key_here
   ```
   Get your free API key at [https://app.tavily.com](https://app.tavily.com)

   > **Note:** The `.env` file is listed in `.gitignore` and will not be pushed to version control.

6. Start MongoDB server

7. Run the search engine agent

   ```bash
   python search_engine.py
   ```

## How It Works

- **Primary search:** Uses DuckDuckGo (via `ddgs` library)
- **Fallback search:** If DuckDuckGo fails, automatically falls back to the **Tavily Search API**
- **Storage:** Results are stored in a MongoDB collection with duplicate detection