# 🐝 MuHive: AI Content Pipeline

A high-performance, automated pipeline designed to filter, verify, and tailor content for the MuLearn community. MuHive transforms raw social media/news data into verified, high-trust intelligence.

---

## 🏗️ Architecture

The project has been consolidated into a sleek, 4-module structure for maximum clarity and debuggability:

- **[`p1_data_schemas.py`](file:///home/johan-b-joy/MuHive/p1_data_schemas.py)**: **The Foundation.** Definitive schemas that define how data looks.
- **[`p2_logic_utils.py`](file:///home/johan-b-joy/MuHive/p2_logic_utils.py)**: **The Infrastructure.** Background helpers (Config, Hashing, Circuit Breakers).
- **[`p3_orchestrator.py`](file:///home/johan-b-joy/MuHive/p3_orchestrator.py)**: **The Intelligence.** The main brain (Prompts, LLMs, Logic, Node).
- **[`run_demo.py`](file:///home/johan-b-joy/MuHive/run_demo.py)**: **The Execution.** The entry point to run the system.

---

## 🚀 Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys**:
   Add your keys to `keys.env`:
   - `GROQ_API_KEY` (Fast classification)
   - `GEMINI_API_KEY` (Quality analysis)
   - `TAVILY_API_KEY` (Web verification)

3. **Run the Demo**:
   ```bash
   python run_demo.py
   ```

---

## 🛠️ Key Features

- **Multi-LLM Orchestration**: Automatically switches between Groq (Llama-3) and Gemini 1.5 based on speed/quality requirements.
- **Smart Verification**: Uses Tavily and DuckDuckGo to reality-check AI claims in real-time.
- **Circuit Breaking**: Automatically skips failing providers to save credits and prevent pipeline hangs.
- **Weighted Trust Scoring**: Calculates a 0-100 reliability score based on source, grounding, and consistency.

---

MuHive is built for students who want to build high-scale, reliable agentic systems. **Clean, simple, and powerful.**
