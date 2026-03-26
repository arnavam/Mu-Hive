"""
MuLearn Stage 2 — Pipeline Node
ScoutItem → pre_filter → Groq (fast filter) → Tavily (search) → Gemini (quality + verifier + tailoring) → Stage2Result

Every Stage2Result is 100% storage-ready. Stage 3 just writes it to DB/JSON.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any

from dotenv import load_dotenv

# Load API keys from keys.env
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys.env"))

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from models import (
    ScoutItem,
    GroupSlice,
    Stage2Result,
    FastFilterResult,
    FastFilterGroupSlice,
    QualityResult,
    QualityGroupSlice,
)
from utils import pre_filter, load_config

logger = logging.getLogger("muhive.stage2")

# ────────────────────────────────────────────────────
# Circuit Breaker (per-provider)
# ────────────────────────────────────────────────────

_circuit_breaker: dict[str, float] = {}  # provider → timestamp of last failure


def _is_circuit_open(provider: str, cooldown_minutes: int) -> bool:
    """Return True if the provider is in cooldown (circuit open)."""
    last_fail = _circuit_breaker.get(provider, 0)
    return (time.time() - last_fail) < (cooldown_minutes * 60)


def _trip_circuit(provider: str) -> None:
    """Mark a provider as failed (open circuit)."""
    _circuit_breaker[provider] = time.time()
    logger.warning("Circuit breaker tripped for provider: %s", provider)


# ────────────────────────────────────────────────────
# LLM Factory (supports provider rotation)
# ────────────────────────────────────────────────────

def _make_fast_llm(provider: str, cfg: dict) -> Any:
    """Create the fast-filter LLM (structured output)."""
    if provider == "groq":
        llm = ChatGroq(
            model=cfg["stage2"]["models"]["groq"],
            temperature=0.0,
            api_key=os.environ.get("GROQ_API_KEY", ""),
        )
    elif provider == "openrouter":
        llm = ChatOpenAI(
            model=cfg["stage2"]["models"]["openrouter_fast"],
            temperature=0.0,
            api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            base_url="https://openrouter.ai/api/v1",
        )
    else:
        raise ValueError(f"Unknown fast provider: {provider}")
    return llm


def _make_quality_llm(provider: str, cfg: dict) -> Any:
    """Create the quality/verifier LLM (structured output)."""
    if provider == "gemini":
        llm = ChatGoogleGenerativeAI(
            model=cfg["stage2"]["models"]["gemini"],
            temperature=0.0,
            google_api_key=os.environ.get("GEMINI_API_KEY", ""),
        )
    elif provider == "openrouter":
        llm = ChatOpenAI(
            model=cfg["stage2"]["models"]["openrouter_quality"],
            temperature=0.0,
            api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            base_url="https://openrouter.ai/api/v1",
        )
    else:
        raise ValueError(f"Unknown quality provider: {provider}")
    return llm


# ────────────────────────────────────────────────────
# Search (Tavily primary, DuckDuckGo fallback)
# ────────────────────────────────────────────────────

async def _search_duckduckgo(query: str, max_results: int) -> str | None:
    """Run DuckDuckGo search fallback."""
    try:
        from ddgs import DDGS
        import asyncio
        
        # duckduckgo_search is synchronous, run in executor
        def _run_ddg():
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                return results

        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, _run_ddg)
        
        if results:
            snippets = [r.get("body", "") for r in results if isinstance(r, dict) and "body" in r]
            return " | ".join(snippets) if snippets else None
        return None
    except Exception as e:
        logger.warning("DuckDuckGo search fallback failed: %s", e)
        return None


async def _search_tool(query: str, max_results: int, cfg: dict) -> str | None:
    """Run primary search (Tavily) with fallback."""
    tavily_key = os.environ.get("TAVILY_API_KEY", "")
    primary = cfg["stage2"]["search"]["primary"]
    fallback = cfg["stage2"]["search"]["fallback"]
    
    # Try Tavily first if configured and has key
    if primary == "tavily" and tavily_key:
        try:
            from langchain_community.tools import TavilySearchResults
            tool = TavilySearchResults(max_results=max_results, api_key=tavily_key)
            results = await tool.ainvoke(query)
            if results and isinstance(results, list):
                snippets = []
                for r in results[:max_results]:
                    if isinstance(r, dict) and "content" in r:
                        snippets.append(r["content"])
                    elif isinstance(r, str):
                        snippets.append(r)
                if snippets:
                    return " | ".join(snippets)
        except Exception as e:
            logger.warning("Tavily search failed, trying fallback: %s", e)
            
    # Try DuckDuckGo fallback
    if fallback == "duckduckgo" or (primary == "tavily" and not tavily_key):
        return await _search_duckduckgo(query, max_results)
        
    return None


# ────────────────────────────────────────────────────
# Prompt Templates
# ────────────────────────────────────────────────────

def _build_fast_filter_prompt(cfg: dict) -> ChatPromptTemplate:
    """Build the Groq fast-filter prompt."""
    groups_info = ""
    for group_name, group_cfg in cfg["stage2"]["groups"].items():
        groups_info += f"- {group_name}: {group_cfg['keywords']}\n"

    system = f"""You are a strict classifier for the MuLearn student community pipeline.
Your job is to classify news/hackathon items into interest groups and score them.

Groups:
{groups_info}

Scoring rules:
- rough_score < {cfg['stage2']['score_thresholds']['auto_fail']}: status = "fail"
- rough_score < {cfg['stage2']['score_thresholds']['pass']}: status = "review"
- rough_score >= {cfg['stage2']['score_thresholds']['pass']}: status = "pass"
- Only include groups where the item genuinely matches. Empty group_slices if none.
- match_reason must be specific (mention exact keywords or concepts that matched).
- Be strict: off-topic, vague, or purely promotional items get low scores.
"""

    user = """Classify this item:
Title: {title}
Description: {description}
Source: {source}
Deadline: {deadline}"""

    return ChatPromptTemplate.from_messages([("system", system), ("user", user)])


def _build_quality_prompt(cfg: dict) -> ChatPromptTemplate:
    """Build the Gemini quality + verifier + tailoring prompt."""
    system = """You are a quality evaluator, verifier, and content tailor for the MuLearn student community pipeline.

You receive an item with its classification and optional search results.
Your job:
1. Write a tailored 2-line summary for EACH matched interest group (different wording per group).
2. Score detail, consistency, and grounding for each group.
3. Verify claims: flag any unsupported claims. If a claim cannot be verified, say UNKNOWN.
4. Quote exact sentences from the input or search results. Never fabricate information.


Rules:
- tailored_summary MUST be different for each group (highlight group-relevant aspects).
- For AI group: emphasize ML/AI techniques, models, datasets.
- For Cybersecurity group: emphasize security implications, attack vectors, defenses.
- For WebDev group: emphasize frameworks, tools, web technologies, developer impact.
- grounding_score: 1.0 if all claims are supported, 0.0 if none are.
- If search results are provided, cross-reference claims against them.
- unsupported_claims: list any claims that cannot be verified. Empty list if all verified.

IMPORTANT: Output ONLY the raw JSON object. Do not output markdown code blocks (```json). Start immediately with {{ and end with }}.
"""

    user = """Evaluate and tailor this item:
Title: {title}
Description: {description}
Source: {source}
Deadline: {deadline}

Fast-filter matched groups: {matched_groups}

Search results (if available): {search_snippet}"""

    return ChatPromptTemplate.from_messages([("system", system), ("user", user)])


# ────────────────────────────────────────────────────
# Trust Score Calculator
# ────────────────────────────────────────────────────

def _compute_trust_score(
    relevance_score: float,
    source_tier: float,
    detail_score: float,
    consistency_score: float,
    grounding_score: float,
    has_unsupported_claims: bool,
    cfg: dict,
) -> float:
    """
    Trust Score = 100 × (w_R·R + w_S·S + w_D·D + w_C·C + w_P·(1-P) + w_G·G + w_V·V)
    where P = 1 if has_unsupported_claims else 0
    """
    w = cfg["stage2"]["trust_weights"]
    r_norm = min(relevance_score / 5.0, 1.0)  # normalize 0–5 to 0–1
    p = 1.0 if has_unsupported_claims else 0.0

    score = 100.0 * (
        w["relevance"] * r_norm
        + w["source_tier"] * source_tier
        + w["detail"] * detail_score
        + w["consistency"] * consistency_score
        + w["penalty_missing"] * (1.0 - p)
        + w["grounding"] * grounding_score
        + w["verification"] * grounding_score  # V ≈ grounding for now
    )
    return round(min(max(score, 0.0), 100.0), 2)


# ────────────────────────────────────────────────────
# Stage 2 Node (main logic)
# ────────────────────────────────────────────────────

async def stage2_node(item: ScoutItem) -> Stage2Result:
    """
    Full Stage 2 pipeline for a single item:
      1. Pre-filter (non-LLM)
      2. Groq fast classification
      3. Conditional Tavily search
      4. Gemini quality + verifier + tailoring
      5. Trust score computation
      → Storage-ready Stage2Result
    """
    cfg = load_config()
    s2 = cfg["stage2"]

    # ── Step 1: Pre-filter ──
    filter_result = pre_filter(item)
    if filter_result["status"] != "pass":
        return Stage2Result(
            item_hash=filter_result["item_hash"],
            status="fail",
            group_slices=[],
            rough_score=0.0,
            fail_reason=filter_result["fail_reason"],
            review_needed=False,
            source_tier=0.0,
            search_used=False,
        )

    item_hash = filter_result["item_hash"]
    source_tier = filter_result["source_tier"]

    # ── Step 2: Groq Fast Filter ──
    fast_result = await _run_fast_filter(item, cfg)

    if fast_result is None:
        return Stage2Result(
            item_hash=item_hash,
            status="review",
            group_slices=[],
            rough_score=0.0,
            fail_reason="fast_filter_all_providers_failed",
            review_needed=True,
            source_tier=source_tier,
            search_used=False,
        )

    # Check if the fast filter says fail
    if fast_result.status == "fail":
        return Stage2Result(
            item_hash=item_hash,
            status="fail",
            group_slices=[],
            rough_score=fast_result.rough_score,
            fail_reason=fast_result.fail_reason or "low_score",
            review_needed=False,
            source_tier=source_tier,
            search_used=False,
        )

    # ── Step 3: Conditional Search ──
    search_used = False
    search_snippet = None
    if fast_result.rough_score >= s2["search"]["trigger_min_rough_score"]:
        query = f"latest {item.title} deadline organizer update"
        search_snippet = await _search_tool(query, s2["search"]["max_results"], cfg)
        search_used = search_snippet is not None

    # ── Step 4: Gemini Quality + Verifier + Tailoring ──
    matched_groups = [gs.group for gs in fast_result.group_slices]
    quality_result = await _run_quality_pass(item, matched_groups, search_snippet, cfg)

    if quality_result is None:
        # Quality pass failed — return with fast-filter data only (review status)
        group_slices = [
            GroupSlice(
                group=gs.group,
                relevance_score=gs.relevance_score,
                match_reason=gs.match_reason,
                tailored_summary="[Quality pass failed — review manually]",
                final_trust_score=0.0,
                grounding_score=0.0,
                ready_for_stage3=False,
            )
            for gs in fast_result.group_slices
        ]
        return Stage2Result(
            item_hash=item_hash,
            status="review",
            group_slices=group_slices,
            rough_score=fast_result.rough_score,
            fail_reason="quality_pass_all_providers_failed",
            review_needed=True,
            source_tier=source_tier,
            search_used=search_used,
            search_snippet=search_snippet,
        )

    # ── Step 5: Merge fast + quality results → final GroupSlices ──
    trust_threshold = s2["trust_threshold_for_ready"]
    final_slices: list[GroupSlice] = []

    # Build a lookup from fast-filter group slices
    fast_lookup = {gs.group: gs for gs in fast_result.group_slices}
    quality_lookup = {gs.group: gs for gs in quality_result.group_slices}

    for group_name in matched_groups:
        fast_gs = fast_lookup.get(group_name)
        qual_gs = quality_lookup.get(group_name)

        if fast_gs is None:
            continue

        detail = qual_gs.detail_score if qual_gs else 0.5
        consistency = qual_gs.consistency_score if qual_gs else 0.5
        grounding = qual_gs.grounding_score if qual_gs else 0.0
        has_unsupported = bool(qual_gs and qual_gs.unsupported_claims)
        tailored = qual_gs.tailored_summary if qual_gs else "[No tailored summary available]"

        trust = _compute_trust_score(
            relevance_score=fast_gs.relevance_score,
            source_tier=source_tier,
            detail_score=detail,
            consistency_score=consistency,
            grounding_score=grounding,
            has_unsupported_claims=has_unsupported,
            cfg=cfg,
        )

        final_slices.append(
            GroupSlice(
                group=group_name,
                relevance_score=fast_gs.relevance_score,
                match_reason=fast_gs.match_reason,
                tailored_summary=tailored,
                final_trust_score=trust,
                grounding_score=grounding,
                ready_for_stage3=trust >= trust_threshold,
            )
        )

    # Determine overall status
    if not final_slices:
        status = "fail"
        fail_reason = "no_matching_groups_after_quality"
    elif any(gs.ready_for_stage3 for gs in final_slices):
        status = "pass"
        fail_reason = None
    elif fast_result.status == "review":
        status = "review"
        fail_reason = "below_trust_threshold"
    else:
        status = "review"
        fail_reason = "below_trust_threshold"

    return Stage2Result(
        item_hash=item_hash,
        status=status,
        group_slices=final_slices,
        rough_score=fast_result.rough_score,
        fail_reason=fail_reason,
        review_needed=status == "review",
        source_tier=source_tier,
        search_used=search_used,
        search_snippet=search_snippet,
        verifier_notes=quality_result.verifier_notes if quality_result else None,
    )


# ────────────────────────────────────────────────────
# Internal: Fast Filter with Retry + Rotation
# ────────────────────────────────────────────────────

async def _run_fast_filter(item: ScoutItem, cfg: dict) -> FastFilterResult | None:
    """
    Run the fast filter (Groq primary → OpenRouter fallback).
    Returns FastFilterResult or None if all providers fail.
    """
    s2 = cfg["stage2"]
    prompt = _build_fast_filter_prompt(cfg)
    providers = ["groq", "openrouter"]
    cooldown = s2["circuit_breaker_cooldown_minutes"]

    for provider in providers:
        if _is_circuit_open(provider, cooldown):
            logger.info("Skipping %s (circuit open)", provider)
            continue

        llm = _make_fast_llm(provider, cfg)

        for attempt in range(s2["max_retries"]):
            try:
                structured = llm.with_structured_output(FastFilterResult)
                messages = prompt.format_messages(
                    title=item.title,
                    description=item.description,
                    source=item.source,
                    deadline=item.deadline or "unknown",
                )
                result = await structured.ainvoke(messages)
                return result
            except Exception as e:
                wait = s2["retry_backoff_seconds"][min(attempt, len(s2["retry_backoff_seconds"]) - 1)]
                logger.warning(
                    "Fast filter attempt %d/%d failed (%s: %s). Retrying in %ds...",
                    attempt + 1, s2["max_retries"], provider, e, wait,
                )
                await asyncio.sleep(wait)

        _trip_circuit(provider)

    return None


# ────────────────────────────────────────────────────
# Internal: Quality Pass with Retry + Rotation
# ────────────────────────────────────────────────────

async def _run_quality_pass(
    item: ScoutItem,
    matched_groups: list[str],
    search_snippet: str | None,
    cfg: dict,
) -> QualityResult | None:
    """
    Run the quality + verifier + tailoring pass (Gemini primary → OpenRouter fallback).
    Returns QualityResult or None if all providers fail.
    """
    s2 = cfg["stage2"]
    prompt = _build_quality_prompt(cfg)
    providers = ["gemini", "openrouter"]
    cooldown = s2["circuit_breaker_cooldown_minutes"]

    for provider in providers:
        if _is_circuit_open(provider, cooldown):
            logger.info("Skipping %s (circuit open)", provider)
            continue

        llm = _make_quality_llm(provider, cfg)

        for attempt in range(s2["max_retries"]):
            try:
                structured = llm.with_structured_output(QualityResult)
                messages = prompt.format_messages(
                    title=item.title,
                    description=item.description,
                    source=item.source,
                    deadline=item.deadline or "unknown",
                    matched_groups=", ".join(matched_groups),
                    search_snippet=search_snippet or "No search results available.",
                )
                result = await structured.ainvoke(messages)
                return result
            except Exception as e:
                wait = s2["retry_backoff_seconds"][min(attempt, len(s2["retry_backoff_seconds"]) - 1)]
                logger.warning(
                    "Quality pass attempt %d/%d failed (%s: %s). Retrying in %ds...",
                    attempt + 1, s2["max_retries"], provider, e, wait,
                )
                await asyncio.sleep(wait)

        _trip_circuit(provider)

    return None


# ────────────────────────────────────────────────────
# Batch Runner (Semaphore-bounded parallelism)
# ────────────────────────────────────────────────────

async def run_stage2_batch(items: list[ScoutItem]) -> list[Stage2Result]:
    """
    Run Stage 2 on a batch of ScoutItems with bounded parallelism.
    Exceptions are caught per-item and returned as review-status results.
    """
    cfg = load_config()
    max_parallel = cfg["stage2"]["max_parallel"]
    semaphore = asyncio.Semaphore(max_parallel)

    async def bounded(item: ScoutItem) -> Stage2Result:
        async with semaphore:
            try:
                return await stage2_node(item)
            except Exception as e:
                logger.error("Unhandled error processing item '%s': %s", item.title, e)
                from utils import get_hash
                return Stage2Result(
                    item_hash=get_hash(item),
                    status="review",
                    group_slices=[],
                    rough_score=0.0,
                    fail_reason=f"unhandled_error: {str(e)[:200]}",
                    review_needed=True,
                    source_tier=0.0,
                    search_used=False,
                )

    results = await asyncio.gather(*[bounded(i) for i in items])
    return list(results)
