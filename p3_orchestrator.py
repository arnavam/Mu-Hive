"""
MuHive Intelligence Pipeline

Filtering, LLM calls, web search, scoring, and orchestration.
"""

import asyncio
import logging
import os
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from p1_data_schemas import ScoutItem, GroupSlice, Stage2Result, FastFilterResult, QualityResult
from p2_logic_utils import load_config, get_hash, get_domain, is_circuit_open, trip_circuit

logger = logging.getLogger("muhive.pipeline")

# ==============================================================================
# SECTION 1: MEMORY & STATE
# ==============================================================================

MEMORY_HASH_SET: set[str] = set()

def clear_hash_set() -> None:
    """Resets the in-memory deduplication tracker."""
    MEMORY_HASH_SET.clear()

# ==============================================================================
# SECTION 2: PROCESSING LOGIC
# ==============================================================================

def pre_filter(item: ScoutItem) -> dict[str, Any]:
    """Deduplication and blocklist checks. Returns status dict."""
    cfg = load_config()
    s2 = cfg["stage2"]
    h = get_hash(item)
    domain = get_domain(item.source)
    tier = s2["source_tiers"].get(domain, s2["default_source_tier"])

    # Duplicate check
    if h in MEMORY_HASH_SET:
        return {"status": "fail", "fail_reason": "duplicate", "item_hash": h, "source_tier": tier}
    MEMORY_HASH_SET.add(h)

    # Empty title check
    if not item.title or not item.title.strip():
        return {"status": "fail", "fail_reason": "empty_title", "item_hash": h, "source_tier": tier}

    # Blocklist check
    text = f"{item.title} {item.description}".lower()
    for word in s2["blocklist"]:
        if word.lower() in text:
            return {"status": "fail", "fail_reason": f"blocked:{word}", "item_hash": h, "source_tier": tier}

    return {"status": "pass", "item_hash": h, "source_tier": tier}

def compute_trust_score(rel: float, tier: float, det: float, cons: float, gro: float, penalty: bool, cfg: dict) -> float:
    """Calculates a weighted average Trust Score (0-100)."""
    w = cfg["stage2"]["trust_weights"]
    r_norm = min(rel / 5.0, 1.0)
    p_val = 1.0 if penalty else 0.0

    raw = 100.0 * (
        w["relevance"]       * r_norm +
        w["source_tier"]     * tier +
        w["detail"]          * det +
        w["consistency"]     * cons +
        w["penalty_missing"] * (1.0 - p_val) +
        w["grounding"]       * gro
    )
    
    return round(max(0.0, min(100.0, raw)), 2)

# ==============================================================================
# SECTION 3: PROMPT LIBRARY
# ==============================================================================

def build_fast_filter_prompt(cfg: dict) -> ChatPromptTemplate:
    """Instructions for initial classification (Groq/Llama-3)."""
    s2 = cfg["stage2"]
    groups = "\n".join(f"- {n}: {g['keywords']}" for n, g in s2["groups"].items())
    system = f"""You are a strict classifier for MuLearn. 
Groups:
{groups}
Scoring: auto-fail < {s2['score_thresholds']['auto_fail']}, pass >= {s2['score_thresholds']['pass']}."""
    user = "Classify: {title}\nDesc: {description}\nSrc: {source}\nDue: {deadline}"
    return ChatPromptTemplate.from_messages([("system", system), ("user", user)])

def build_quality_prompt(cfg: dict) -> ChatPromptTemplate:
    """Instructions for deep analysis and tailoring (Gemini/OpenRouter)."""
    system = """You are a quality evaluator for MuLearn.

For each matched group, return:
- tailored_summary: A 2-line summary tailored for that group's audience.
- detail_score: 0.0-1.0 — How detailed and specific the source content is.
- consistency_score: 0.0-1.0 — How internally consistent the claims are.
- grounding_score: 0.0-1.0 — How well claims are supported by the search snippet.
- unsupported_claims: List any claims not supported by evidence.

Also return verifier_notes: a brief summary of your hallucination check."""
    user = "Evaluate: {title}\nGroups: {matched_groups}\nSearch: {search_snippet}"
    return ChatPromptTemplate.from_messages([("system", system), ("user", user)])

# ==============================================================================
# SECTION 4: LLM FACTORY
# ==============================================================================

def _make_llm(model_key: str, provider: str, cfg: dict) -> Any:
    """Core factory for chat models. Fails explicitly if API key is missing."""
    name = cfg["stage2"]["models"][model_key]
    temp = 0.0
    if provider == "groq":
        key = os.environ.get("GROQ_API_KEY")
        if not key: raise ValueError("GROQ_API_KEY not set")
        return ChatGroq(model=name, temperature=temp, api_key=key)
    if provider == "gemini":
        key = os.environ.get("GEMINI_API_KEY")
        if not key: raise ValueError("GEMINI_API_KEY not set")
        return ChatGoogleGenerativeAI(model=name, temperature=temp, google_api_key=key)
    if provider == "openrouter":
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key: raise ValueError("OPENROUTER_API_KEY not set")
        return ChatOpenAI(model=name, temperature=temp, api_key=key, base_url="https://openrouter.ai/api/v1")
    raise ValueError(f"Unknown provider: {provider}")

async def _call_structured_llm(mode: Literal["fast", "quality"], schema: Any, prompt_builder: Any, inputs: dict, cfg: dict) -> Any | None:
    """Unified helper for LLM calls with circuit breaking."""
    s2 = cfg["stage2"]
    providers = ["groq", "openrouter"] if mode == "fast" else ["gemini", "openrouter"]
    factory_key = lambda p: "groq" if p=="groq" else ("gemini" if p=="gemini" else (f"openrouter_{mode}"))
    
    for p in providers:
        if is_circuit_open(p, s2["circuit_breaker_cooldown_minutes"]):
            continue
        try:
            llm = _make_llm(factory_key(p), p, cfg)
        except ValueError as e:
            # Config error (missing API key) — skip provider, don't trip circuit
            logger.error(f"Skipping {p}: {e}")
            continue
        backoff_list = s2["retry_backoff_seconds"]
        for attempt in range(s2["max_retries"]):
            try:
                prompt_msgs = prompt_builder(cfg).format_messages(**inputs)
                return await llm.with_structured_output(schema).ainvoke(prompt_msgs)
            except Exception as e:
                wait = backoff_list[min(attempt, len(backoff_list) - 1)]
                logger.warning(f"{mode} failed ({p}, attempt {attempt+1}): {e}")
                await asyncio.sleep(wait)
        trip_circuit(p)
    return None

# ==============================================================================
# SECTION 5: WEB TOOLS
# ==============================================================================

async def search_tool(query: str, max_results: int, cfg: dict) -> str | None:
    """Search with automatic Tavily → DuckDuckGo fallback."""
    key = os.environ.get("TAVILY_API_KEY")
    if cfg["stage2"]["search"]["primary"] == "tavily" and key:
        try:
            from langchain_community.tools import TavilySearchResults
            res = await TavilySearchResults(max_results=max_results, api_key=key).ainvoke(query)
            return " | ".join(r["content"] for r in res[:max_results] if "content" in r)
        except Exception as e:
            logger.warning(f"Tavily search failed, falling back to DDG: {e}")
    return await search_duckduckgo(query, max_results)

async def search_duckduckgo(query: str, max_results: int) -> str | None:
    """Fallback DDG search."""
    from ddgs import DDGS
    try:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, lambda: list(DDGS().text(query, max_results=max_results)))
        return " | ".join(r.get("body", "") for r in res)
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed: {e}")
        return None


# ==============================================================================
# SECTION 6: STAGE 2 ORCHESTRATOR
# ==============================================================================

async def stage2_node(item: ScoutItem) -> Stage2Result:
    """Orchestrates the full pipeline for a single item."""
    cfg = load_config()
    s2 = cfg["stage2"]
    item_hash = get_hash(item)

    # Step 1: Pre-filter (dedup, blocklist)
    res = pre_filter(item)
    if res["status"] != "pass":
        return Stage2Result(
            item_hash=item_hash,
            status="fail",
            fail_reason=res["fail_reason"],
            source_tier=res["source_tier"],
        )

    # Step 2: Fast classification (Groq)
    fast_inputs = {
        "title": item.title,
        "description": item.description,
        "source": item.source,
        "deadline": item.deadline or "unknown",
    }
    fast = await _call_structured_llm("fast", FastFilterResult, build_fast_filter_prompt, fast_inputs, cfg)

    if not fast or fast.status == "fail":
        return Stage2Result(
            item_hash=item_hash,
            status="review" if not fast else "fail",
            fail_reason=fast.fail_reason if fast else "llm_failed",
            review_needed=(not fast),
            source_tier=res["source_tier"],
        )

    # Step 2b: Enforce score thresholds (don't trust LLM status alone)
    thresholds = s2["score_thresholds"]
    if fast.rough_score < thresholds["auto_fail"]:
        return Stage2Result(
            item_hash=item_hash,
            status="fail",
            fail_reason=f"rough_score {fast.rough_score} < auto_fail {thresholds['auto_fail']}",
            rough_score=fast.rough_score,
            source_tier=res["source_tier"],
        )

    # Step 3: Web search (if score high enough)
    snippet = None
    if fast.rough_score >= s2["search"]["trigger_min_rough_score"]:
        snippet = await search_tool(
            item.title,
            s2["search"]["max_results"],
            cfg,
        )

    # Step 4: Quality analysis (Gemini)
    matched = ", ".join(gs.group for gs in fast.group_slices)
    quality_inputs = {
        "title": item.title,
        "matched_groups": matched,
        "search_snippet": snippet or "None",
    }
    quality = await _call_structured_llm("quality", QualityResult, build_quality_prompt, quality_inputs, cfg)

    if not quality:
        return Stage2Result(
            item_hash=item_hash,
            status="review",
            rough_score=fast.rough_score,
            review_needed=True,
            source_tier=res["source_tier"],
            search_used=(snippet is not None),
        )

    # Step 5: Merge fast + quality into final slices
    q_lookup = {gs.group: gs for gs in quality.group_slices}
    final_slices = []

    for f_gs in fast.group_slices:
        q_gs = q_lookup.get(f_gs.group)
        if not q_gs:
            logger.warning(f"Quality pass missing group '{f_gs.group}' for '{item.title[:40]}' — using defaults")

        trust = compute_trust_score(
            rel=f_gs.relevance_score,
            tier=res["source_tier"],
            det=q_gs.detail_score if q_gs else 0.5,
            cons=q_gs.consistency_score if q_gs else 0.5,
            gro=q_gs.grounding_score if q_gs else 0.0,
            penalty=bool(q_gs and q_gs.unsupported_claims),
            cfg=cfg,
        )

        final_slices.append(GroupSlice(
            group=f_gs.group,
            relevance_score=f_gs.relevance_score,
            match_reason=f_gs.match_reason,
            tailored_summary=q_gs.tailored_summary if q_gs else "[No summary]",
            final_trust_score=trust,
            grounding_score=q_gs.grounding_score if q_gs else 0.0,
            ready_for_stage3=(trust >= s2["trust_threshold_for_ready"]),
        ))

    # Step 6: Final verdict
    has_pass = any(s.ready_for_stage3 for s in final_slices)
    return Stage2Result(
        item_hash=item_hash,
        status="pass" if has_pass else "review",
        group_slices=final_slices,
        rough_score=fast.rough_score,
        review_needed=(not has_pass),
        source_tier=res["source_tier"],
        search_used=(snippet is not None),
        search_snippet=snippet,
        verifier_notes=quality.verifier_notes,
    )

async def run_stage2_batch(items: list[ScoutItem]) -> list[Stage2Result]:
    """Processes multiple items in parallel using a semaphore."""
    sem = asyncio.Semaphore(load_config()["stage2"]["max_parallel"])
    async def b(i):
        async with sem:
            try: return await stage2_node(i)
            except Exception as e: return Stage2Result(item_hash=get_hash(i), status="review", fail_reason=str(e), review_needed=True)
    return await asyncio.gather(*[b(i) for i in items])
