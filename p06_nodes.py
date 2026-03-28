"""
MuLearn Stage 2 — Orchestrator Node
───────────────────────────────────
Main entry point for 'Stage 2' processing.
Orchestrates the flow:
1. Filters (Zero-LLM) - p03_pre_filtering.py
2. Fast Classification (Groq) - p06_nodes.py (internal)
3. Conditional Search (Tavily) - p07_web_searching.py
4. Deep Quality Pass (Gemini) - p06_nodes.py (internal)
5. Scoring & Merging - p08_trust_scoring.py

Functions:
- stage2_node: Process a single item
- run_stage2_batch: Process multiple items in parallel (bounded)
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any
from dotenv import load_dotenv

# Env & Config setup
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys.env"))

from models import (
    ScoutItem,
    GroupSlice,
    Stage2Result,
    FastFilterResult,
    QualityResult,
)
from p01_configuration import load_config
from p02_text_processing import get_hash
from p03_pre_filtering import pre_filter
from p09_circuit_breaker import is_circuit_open, trip_circuit
from p04_llm_orchestrator import make_fast_llm, make_quality_llm
from p07_web_searching import search_tool
from p05_prompt_library import build_fast_filter_prompt, build_quality_prompt
from p08_trust_scoring import compute_trust_score

logger = logging.getLogger("muhive.stage2")

# ────────────────────────────────────────────────────
# Core Logic
# ────────────────────────────────────────────────────

async def stage2_node(item: ScoutItem) -> Stage2Result:
    """
    Main pipeline for a single item.
    """
    cfg = load_config()
    s2 = cfg["stage2"]

    # 1. Pre-filter (Local logic)
    res = pre_filter(item)
    if res["status"] != "pass":
        return Stage2Result(
            item_hash=res["item_hash"], status="fail", group_slices=[],
            rough_score=0.0, fail_reason=res["fail_reason"], review_needed=False,
            source_tier=0.0, search_used=False
        )

    # 2. Fast Classification
    fast = await _run_fast_filter(item, cfg)
    if not fast:
        return Stage2Result(
            item_hash=res["item_hash"], status="review", group_slices=[],
            rough_score=0.0, fail_reason="classification_failed", review_needed=True,
            source_tier=res["source_tier"], search_used=False
        )

    if fast.status == "fail":
        return Stage2Result(
            item_hash=res["item_hash"], status="fail", group_slices=[],
            rough_score=fast.rough_score, fail_reason=fast.fail_reason or "low_score",
            source_tier=res["source_tier"], search_used=False
        )

    # 3. Search (if score is high enough)
    search_snippet = None
    if fast.rough_score >= s2["search"]["trigger_min_rough_score"]:
        query = f"latest {item.title} update"
        search_snippet = await search_tool(query, s2["search"]["max_results"], cfg)

    # 4. Deep Quality Pass
    groups = [gs.group for gs in fast.group_slices]
    quality = await _run_quality_pass(item, groups, search_snippet, cfg)
    
    if not quality:
        # Fallback to classification results if quality pass fails
        return Stage2Result(
            item_hash=res["item_hash"], status="review", 
            group_slices=[], rough_score=fast.rough_score,
            fail_reason="quality_pass_failed", review_needed=True,
            source_tier=res["source_tier"], search_used=search_snippet is not None
        )

    # 5. Merge & Score
    final_slices = []
    trust_thresh = s2["trust_threshold_for_ready"]
    q_lookup = {gs.group: gs for gs in quality.group_slices}

    for f_gs in fast.group_slices:
        q_gs = q_lookup.get(f_gs.group)
        trust = compute_trust_score(
            f_gs.relevance_score, res["source_tier"],
            q_gs.detail_score if q_gs else 0.5,
            q_gs.consistency_score if q_gs else 0.5,
            q_gs.grounding_score if q_gs else 0.0,
            bool(q_gs and q_gs.unsupported_claims),
            cfg
        )
        
        final_slices.append(GroupSlice(
            group=f_gs.group,
            relevance_score=f_gs.relevance_score,
            match_reason=f_gs.match_reason,
            tailored_summary=q_gs.tailored_summary if q_gs else "[No summary]",
            final_trust_score=trust,
            grounding_score=q_gs.grounding_score if q_gs else 0.0,
            ready_for_stage3=trust >= trust_thresh
        ))

    # Determine status
    has_pass = any(s.ready_for_stage3 for s in final_slices)
    status = "pass" if has_pass else "review"

    return Stage2Result(
        item_hash=res["item_hash"], status=status, group_slices=final_slices,
        rough_score=fast.rough_score, fail_reason=None if status=="pass" else "below_trust",
        review_needed=status=="review", source_tier=res["source_tier"],
        search_used=search_snippet is not None, search_snippet=search_snippet,
        verifier_notes=quality.verifier_notes
    )

# ────────────────────────────────────────────────────
# Internals
# ────────────────────────────────────────────────────

async def _run_fast_filter(item: ScoutItem, cfg: dict) -> FastFilterResult | None:
    s2 = cfg["stage2"]
    prompt = build_fast_filter_prompt(cfg)
    for p in ["groq", "openrouter"]:
        if is_circuit_open(p, s2["circuit_breaker_cooldown_minutes"]): continue
        llm = make_fast_llm(p, cfg)
        for _ in range(s2["max_retries"]):
            try:
                structured = llm.with_structured_output(FastFilterResult)
                return await structured.ainvoke(prompt.format_messages(
                    title=item.title, description=item.description,
                    source=item.source, deadline=item.deadline or "unknown"
                ))
            except Exception as e:
                logger.warning("Fast filter attempt failed (%s). Retrying: %s", p, e)
                await asyncio.sleep(s2["retry_backoff_seconds"][0])
        trip_circuit(p)
    return None

async def _run_quality_pass(item: ScoutItem, groups: list[str], snippet: str | None, cfg: dict) -> QualityResult | None:
    s2 = cfg["stage2"]
    prompt = build_quality_prompt(cfg)
    for p in ["gemini", "openrouter"]:
        if is_circuit_open(p, s2["circuit_breaker_cooldown_minutes"]): continue
        llm = make_quality_llm(p, cfg)
        for _ in range(s2["max_retries"]):
            try:
                structured = llm.with_structured_output(QualityResult)
                return await structured.ainvoke(prompt.format_messages(
                    title=item.title, description=item.description,
                    source=item.source, deadline=item.deadline or "unknown",
                    matched_groups=", ".join(groups), search_snippet=snippet or "None"
                ))
            except Exception as e:
                logger.warning("Quality pass attempt failed (%s). Retrying: %s", p, e)
                await asyncio.sleep(s2["retry_backoff_seconds"][0])
        trip_circuit(p)
    return None

async def run_stage2_batch(items: list[ScoutItem]) -> list[Stage2Result]:
    cfg = load_config()
    sem = asyncio.Semaphore(cfg["stage2"]["max_parallel"])
    async def b(i):
        async with sem:
            try: return await stage2_node(i)
            except Exception as e:
                return Stage2Result(item_hash=get_hash(i), status="review", group_slices=[],
                                  rough_score=0.0, fail_reason=str(e), review_needed=True)
    return await asyncio.gather(*[b(i) for i in items])
