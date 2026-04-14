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
import logging
import os
import sys

from dotenv import load_dotenv
from p1_data_schemas import ScoutItem
from p3_orchestrator import run_stage2_batch, clear_hash_set

# Load API keys from keys.env into os.environ
load_dotenv(os.path.join(os.path.dirname(__file__), "keys.env"))

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

    ),
]


async def main():
    """Run the demo batch and print results."""
    clear_hash_set()
    
    print("\n" + "═" * 60)
    print("  MUHIVE STAGE 2 — INTEL PIPELINE DEMO")
    print("═" * 60)
    print(f"  → Processing {len(SAMPLE_ITEMS)} samples...\n")

    results = await run_stage2_batch(SAMPLE_ITEMS)

    for i, res in enumerate(results):
        icon = {"pass": "✅", "fail": "❌", "review": "⚠️"}.get(res.status, "•")
        print(f"{icon} ITEM {i+1}: {SAMPLE_ITEMS[i].title[:50]}...")
        print(f"  └─ Status: {res.status.upper()} | Score: {res.rough_score}/5.0 | Search: {'Yes' if res.search_used else 'No'}")
        
        if res.group_slices:
            for gs in res.group_slices:
                ready = "READY" if gs.ready_for_stage3 else "LOW_TRUST"
                print(f"     ◈ {gs.group:<12} | Trust: {gs.final_trust_score:>5.1f}/100 | {ready}")

    passed = sum(1 for r in results if r.status == "pass")
    print("\n" + "═" * 60)
    print(f"  PIPELINE COMPLETE: {passed}/{len(results)} items ready for Stage 3")
    print("═" * 60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
