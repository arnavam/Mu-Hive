# MuLearn AI Pipeline — Stage 2 (Processing Node)

This is the production-ready **Stage 2 Data Processing Pipeline** for the MuLearn AI Interest Group. It leverages an orchestrator (LangGraph-style node execution) to classify, search, fact-check, and customize incoming scraped articles and events for specific student tech groups: AI, Cybersecurity, and Web Development.

## 🌟 What This Pipeline Does

1. **Pre-Filtering (Zero Cost)**: Instantly blocks known spam categories (crypto, sponsored giveaways) and duplicates via URL hashing before hitting any paid LLM APIs.
2. **Dual-Model Processing**:
   - Uses an ultra-fast LLM (`llama-3.1-8b`) for classification and rough scoring.
   - Uses a reasoning LLM (`gemini-2.5-flash-lite`) to digest the content and write targeted summaries.
3. **Live Web Grounding**: Employs Tavily Search (with a DuckDuckGo fallback) to dynamically scrape the web and fact-check all LLM claims, preventing hallucinations.
4. **Tailoring**: Outputs distinct, bespoke 2-line summaries for each identified interest group. (e.g., an article about Gemma 3 models gets a unique summary written for the AI group, and a different one for the WebDev group).
5. **Storage Ready**: Spits out a pristine `Stage2Result` JSON object that is strictly enforced by Pydantic, ready to be directly dumped into PostgreSQL or vector storage (Stage 3).

---

## 🧠 Models Utilized

The pipeline explicitly separates the workload to balance extreme speed and quality:

| Node | Primary Provider | Model | Fallback Provider | Model |
|------|------------------|-------|-------------------|-------|
| **1. Fast Filter** | Groq (`llama-3.1-8b-instant`) | Open-source Llama 3.1 8B | OpenRouter | `meta-llama/llama-3.1-8b-instruct:free` |
| **2. Search/Grounding** | Tavily Search API | Native Search Endpoints | DuckDuckGo | `ddgs` (Open-source Web Scraper) |
| **3. Quality Assessor & Tailoring** | Gemini API (`gemini-2.5-flash-lite`) | Google Gemini Flash | OpenRouter | `google/gemini-2.5-flash-lite:free` |

---

## 🛡️ Robust Error Handling & Fallbacks

This pipeline was built from day-1 to survive API rate-limits and outages gracefully:

1. **Built-In Retries & Backoff**: Configured in `config.yaml`. If an LLM times out or returns bad JSON, the system pauses using an exponential backoff (`Math.pow(2, retries)`) and tries again up to `max_retries`.
2. **Provider Rotation**: If the primary LLM provider (e.g., Groq) completely fails or exhausts rate limits, the pipeline instantly swaps to OpenRouter and queries a secondary free model to finish the task.
3. **Search Engine Fallback**: If Tavily exhausts search credits or returns HTTP errors, the system natively falls back to DuckDuckGo to scrape the web manually at zero cost.
4. **Safe Status Routing**: If absolutely every LLM fallback fails, the pipeline does not drop the item. It defaults the item's `status` to `"review"`. This guarantees the data isn't destroyed and allows human moderators to inspect it later.

---

## 🚀 How to Run the Pipeline

### 1. Prerequisites
Ensure you have Python installed and your environment is active.
```bash
pip install -r requirements.txt
```

### 2. Configure Your API Keys
Open `keys.env` and place your keys exactly as requested. Never commit this file to version control.
```env
# Example keys.env
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key
TAVILY_API_KEY=your_tavily_key
OPENROUTER_API_KEY=your_openrouter_key
```

### 3. Run the Demonstration
Execute the demo script to watch 5 simulated articles traverse the pipeline in real-time:
```bash
python run_demo.py
```
*Note: You can control parallelism (running 1 vs running 5 simultaneously) by modifying the `max_parallel` setting in `config.yaml` to avoid bursting free-tier API rate limits.*
