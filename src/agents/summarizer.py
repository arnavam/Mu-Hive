import asyncio
import random
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from loguru import logger
from src.llm import make_llm_client, get_limiter
from src.retry import with_retry
from src.config import load_config
from src.state_manager import update_hashes_status, get_hash
from src.db.data_schemas import CleanItem
from src.agent_config import AGENT_PROMPTS

class Extraction(BaseModel):
    summary: str = Field(description="2-sentence summary of the item")
    category: str = Field(description="One of the provided categories")
    deadline: Optional[str] = Field(description="Application or registration deadline date if found")

@with_retry
async def _structure_one(entry: Dict, client, limiter) -> CleanItem:
    """Internal helper to extract structured data from a verified item."""
    item = entry["item"]
    groups = load_config("interest_groups")
    categories = ", ".join(groups.get(item.ig, {}).get("categories", []))
    
    system_prompt = AGENT_PROMPTS["summarizer"].format(ig=item.ig, categories=categories)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Title: {item.title}\nText: {item.text[:3000]}"}
    ]
    
    # Small random jitter to prevent burst TPM hits
    await asyncio.sleep(random.uniform(0.5, 2.0))
    
    async with limiter:
        try:
            # client.create handles the thread-pooling and API interaction
            extraction: Extraction = await asyncio.to_thread(client.create, Extraction, messages)
            
            logger.info(f"Structured: {item.title[:50]}")
            return CleanItem(
                hash=get_hash(item),
                title=item.title,
                url=item.url,
                summary=extraction.summary,
                ig=item.ig,
                source=item.source,
                category=extraction.category,
                deadline=extraction.deadline,
                score=entry["score"],
                status=entry["status"],
                created_at=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Structure extraction failed for {item.url}: {e}")
            # Fallback to a basic 'flagged' item so the data isn't lost
            return CleanItem(
                hash=get_hash(item),
                title=item.title,
                url=item.url,
                summary="[AI extraction failed]",
                ig=item.ig,
                source=item.source,
                category="other",
                deadline=None,
                score=entry["score"],
                status="flagged",
                created_at=datetime.now().isoformat()
            )

async def run_summarizer(verified_entries: List[Dict]) -> List[CleanItem]:
    """
    The Structurer Agent: Turns verified raw text into structured data.
    1. Extracts summary, category, and deadline via LLM.
    2. Returns a list of 'CleanItem' objects ready for export.
    """
    if not verified_entries:
        return []
        
    pipeline_cfg = load_config("pipeline")
    routing = pipeline_cfg.get("ig_routing", {})
    semaphore = asyncio.Semaphore(pipeline_cfg.get("structurer_concurrency", 1))
    
    logger.info(f"Structuring {len(verified_entries)} items into final format...")
    
    async def process_entry(entry: Dict):
        item = entry["item"]
        ig_cfg = routing.get(item.ig) or routing.get("default", {})
        target_tier = ig_cfg.get("structurer", "cheap")
        
        async with semaphore:
            client = make_llm_client("structurer", tier=target_tier)
            limiter = get_limiter(client.provider, client.model)
            return await _structure_one(entry, client, limiter)

    # Gather all results in parallel while respecting concurrency limit
    results = await asyncio.gather(*[process_entry(e) for e in verified_entries])
    final_items = [r for r in results if r is not None]
            
    # Final state update: Mark items as fully structured
    update_hashes_status(final_items, "structured")
    
    logger.info(f"Summarizer: Completed {len(final_items)} structured items")
    return final_items
