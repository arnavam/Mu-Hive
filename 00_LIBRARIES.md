# Project Libraries & Dependencies

This document provides an overview of the external libraries used in the MuLearn Stage 2 Pipeline and their specific roles.

## 🧠 AI & Orchestration

- **LangChain (`langchain`)**: The core framework used to orchestrate the "Stage 2" pipeline. It manages the flow between different LLM providers and tools.
- **LangChain Core (`langchain-core`)**: Provides the base abstractions for prompts and structured outputs.
- **LangChain Groq (`langchain-groq`)**: Adapter for the **Groq API**. Used in `p04_llm_orchestrator.py` to run high-speed inference on `llama-3.1`.
- **LangChain Google GenAI (`langchain-google-genai`)**: Adapter for **Google Gemini**. Used for the high-quality tailoring and verification pass.
- **LangChain OpenAI (`langchain-openai`)**: Used as an adapter for **OpenRouter**, providing a unified fallback for multiple models.

## 🔍 Search & Verification

- **Tavily (`langchain-community`)**: The primary search engine tool used in `p07_web_searching.py` for fact-checking and grounding LLM responses.
- **DuckDuckGo Search (`duckduckgo-search`)**: A zero-cost fallback search provider used when Tavily credits are exhausted.

## 🛠️ Utilities & Data

- **Pydantic**: Used in `models.py` to enforce strict data schemas. It guarantees that the pipeline's output is always valid JSON for Stage 3 storage.
- **PyYAML**: Used in `p01_configuration.py` to parse the `config.yaml` settings file.
- **python-dotenv**: Used to securely load API keys from the `keys.env` file into the environment.
- **Pydash / Mashumaro (Optional)**: Sometimes used for deep dictionary manipulation and fast serialization.

## ⚙️ Core Python Built-ins

- **asyncio**: Used for non-blocking parallel processing of article batches.
- **hashlib**: Used in `p02_text_processing.py` to generate unique MD5 fingerprints for deduplication.
- **logging**: Provides a robust tracking mechanism for pipeline health and circuit breaker status.
