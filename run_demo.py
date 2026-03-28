#!/usr/bin/env python3
"""
MuLearn Stage 2 — Demo Runner
Runs 5 sample ScoutItems through the full Stage 2 pipeline.

Usage:
  1. Fill in your API keys in keys.env
  2. pip install -r requirements.txt
  3. python run_demo.py
"""

import asyncio
import json
import logging
import sys

from models import ScoutItem
from p06_nodes import run_stage2_batch
from utils import clear_hash_set

# ── Logging setup ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    stream=sys.stdout,
)

# ── Sample ScoutItems (mix of AI / Cyber / WebDev / spam / duplicate) ──
SAMPLE_ITEMS = [
    ScoutItem(
        title="Google DeepMind releases Gemma 3 open weights — state-of-the-art small LLM",
        description=(
            "Google DeepMind has released Gemma 3, an open-weight language model family "
            "achieving state-of-the-art performance among sub-10B parameter models. "
            "The models support 140+ languages, multimodal input, and a 128K context window. "
            "Available via Kaggle, Hugging Face, and Vertex AI."
        ),
        url="https://blog.google/technology/developers/gemma-3/",
        source="blog.google",
        deadline=None,
        raw_html=None,
    ),
    ScoutItem(
        title="DEF CON CTF 2026 — Qualifiers Open for Registration",
        description=(
            "DEF CON CTF 2026 qualifier rounds are now open. Teams can register on the "
            "official DEFCON CTF platform. Challenges will span binary exploitation, "
            "reverse engineering, cryptography, and web security. Top 16 teams qualify "
            "for the finals in Las Vegas."
        ),
        url="https://defcon.org/ctf-2026-quals",
        source="defcon.org",
        deadline="2026-05-15",
        raw_html=None,
    ),
    ScoutItem(
        title="Next.js 16 launched with React Server Actions v2 and Edge Runtime improvements",
        description=(
            "Vercel has released Next.js 16 featuring React Server Actions v2 with automatic "
            "form handling, improved Edge Runtime performance, built-in i18n routing, and "
            "a redesigned developer experience with instant HMR. The update also includes "
            "native TypeScript project references support."
        ),
        url="https://nextjs.org/blog/next-16",
        source="nextjs.org",
        deadline=None,
        raw_html=None,
    ),
    ScoutItem(
        title="🎉 FREE CRYPTO GIVEAWAY — Win 10 BTC NOW!!!",
        description=(
            "Join our exclusive crypto giveaway and win up to 10 BTC! "
            "Just click the link and enter your wallet address. Sponsored by CryptoKings."
        ),
        url="https://scam-site.xyz/giveaway",
        source="scam-site.xyz",
        deadline=None,
        raw_html=None,
    ),
    ScoutItem(
        title="MLH Global Hack Week: AI Edition — Build with LLMs in 7 days",
        description=(
            "Major League Hacking presents Global Hack Week: AI Edition. Build AI-powered "
            "projects using LLMs, computer vision, or reinforcement learning. Free workshops, "
            "mentorship sessions, and prizes from Google, Meta, and Microsoft. Open to all "
            "students worldwide."
        ),
        url="https://mlh.io/events/ai-hack-week-2026",
        source="mlh.io",
        deadline="2026-04-01",
        raw_html=None,
    ),
]


async def main():
    """Run the demo batch and print results."""
    clear_hash_set()  # Start fresh

    print("=" * 70)
    print("MuLearn Stage 2 Pipeline — Demo Run")
    print("=" * 70)
    print(f"\nProcessing {len(SAMPLE_ITEMS)} items...\n")

    results = await run_stage2_batch(SAMPLE_ITEMS)

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    for i, result in enumerate(results):
        print(f"\n{'─' * 60}")
        print(f"Item {i + 1}: {SAMPLE_ITEMS[i].title[:60]}...")
        print(f"  Status:       {result.status}")
        print(f"  Rough Score:  {result.rough_score}")
        print(f"  Source Tier:  {result.source_tier}")
        print(f"  Search Used:  {result.search_used}")
        print(f"  Fail Reason:  {result.fail_reason or '—'}")
        print(f"  Review Need:  {result.review_needed}")

        if result.group_slices:
            for gs in result.group_slices:
                print(f"\n  ┌─ {gs.group}")
                print(f"  │ Relevance:     {gs.relevance_score}/5.0")
                print(f"  │ Trust Score:   {gs.final_trust_score}/100")
                print(f"  │ Grounding:     {gs.grounding_score}")
                print(f"  │ Ready:         {gs.ready_for_stage3}")
                print(f"  │ Match Reason:  {gs.match_reason}")
                print(f"  │ Summary:       {gs.tailored_summary}")
                print(f"  └─")

        if result.verifier_notes:
            print(f"\n  Verifier: {result.verifier_notes}")

    # ── Dump full JSON ──
    print("\n" + "=" * 70)
    print("FULL JSON OUTPUT")
    print("=" * 70)
    output = [r.model_dump() for r in results]
    print(json.dumps(output, indent=2, default=str))

    # ── Summary ──
    passed = sum(1 for r in results if r.status == "pass")
    failed = sum(1 for r in results if r.status == "fail")
    review = sum(1 for r in results if r.status == "review")
    print(f"\n{'=' * 70}")
    print(f"SUMMARY: {passed} passed | {failed} failed | {review} review")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(main())
