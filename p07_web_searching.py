"""
MuHive Search Integration
─────────────────────────
Performs external searches to verify item details or find missing info.
Uses Tavily as the primary tool with a DuckDuckGo fallback.

Functions:
- search_tool: High-level search interface with automatic fallback
- search_duckduckgo: Low-level DDG search scraper
"""

import asyncio
import os
import logging
from typing import Any

logger = logging.getLogger("muhive.search")

async def search_tool(query: str, max_results: int, cfg: dict) -> str | None:
    """
    Try primary search (Tavily), fallback to DuckDuckGo if needed.
    """
    tavily_key = os.environ.get("TAVILY_API_KEY", "")
    primary = cfg["stage2"]["search"]["primary"]
    
    # 1. Try Tavily
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
                if snippets:
                    return " | ".join(snippets)
        except Exception as e:
            logger.warning("Tavily failed: %s. Falling back.", e)
            
    # 2. Fallback to DDG
    return await search_duckduckgo(query, max_results)

async def search_duckduckgo(query: str, max_results: int) -> str | None:
    """
    Lightweight fallback search using DuckDuckGo.
    """
    try:
        from ddgs import DDGS
        
        def _run_ddg():
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=max_results))

        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, _run_ddg)
        
        if results:
            snippets = [r.get("body", "") for r in results if isinstance(r, dict) and "body" in r]
            return " | ".join(snippets)
        return None
    except Exception as e:
        logger.error("DuckDuckGo search failed: %s", e)
        return None
