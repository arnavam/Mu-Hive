# MuLearn AI Pipeline — Stage 2 (Processing Node)

This is the production-ready **Stage 2 Data Processing Pipeline** for the MuLearn AI Interest Group.

---

## 📂 Project Structure (Task-Based Flow)

The codebase is organized into task-specific modules numbered in their execution order:

1.  **[p01_configuration.py](file:///home/johan-b-joy/MuHive/p01_configuration.py)**: Loads/caches settings from `config.yaml`.
2.  **[p02_text_processing.py](file:///home/johan-b-joy/MuHive/p02_text_processing.py)**: Cleans URLs and generates unique fingerprints.
3.  **[p03_pre_filtering.py](file:///home/johan-b-joy/MuHive/p03_pre_filtering.py)**: Performs Stage 2a deduplication and blocklisting.
4.  **[p04_llm_orchestrator.py](file:///home/johan-b-joy/MuHive/p04_llm_orchestrator.py)**: Initializes AI models (Groq, Gemini, etc.).
5.  **[p05_prompt_library.py](file:///home/johan-b-joy/MuHive/p05_prompt_library.py)**: Central store for all AI instructions.
6.  **[p06_nodes.py](file:///home/johan-b-joy/MuHive/p06_nodes.py)**: The main orchestrator (Stage 2 Logic).
7.  **[p07_web_searching.py](file:///home/johan-b-joy/MuHive/p07_web_searching.py)**: Stage 2b web search verification.
8.  **[p08_trust_scoring.py](file:///home/johan-b-joy/MuHive/p08_trust_scoring.py)**: Final 0-100 Trust Score calculation.
9.  **[p09_circuit_breaker.py](file:///home/johan-b-joy/MuHive/p09_circuit_breaker.py)**: Failure protection for AI providers.

---

## 🚀 How to Run

1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Setup Keys**: Add keys to `keys.env`.
3. **Demo**: `python run_demo.py`
