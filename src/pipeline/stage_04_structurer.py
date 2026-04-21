import asyncio
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger
from ..llm_client import make_llm_client, get_limiter
from ..retry import with_retry
from ..config import load_config
from ..state_manager import update_hashes_status, get_hash
from ..schemas import CleanItem

class Extraction(BaseModel):
    summary: str = Field(description="2-sentence summary")
    category: str = Field(description="One of the provided categories")
    deadline: Optional[str] = Field(description="Deadline date if found")

@with_retry
async def _structure_one(entry, client, limiter):
    item = entry["item"]
    groups = load_config("groups")["interest_groups"]
    categories = ", ".join(groups.get(item.ig, {}).get("categories", []))
    
    messages = [
        {"role": "system", "content": f"Extract info for {item.ig}. Categories: {categories}. Summarize in 2 sentences. Specifically search for and extract any application or registration deadlines found in the text. Don't guess dates."},
        {"role": "user", "content": f"Title: {item.title}\nText: {item.text[:3000]}"}
    ]
    
    async with limiter:
        try:
            ext = await asyncio.to_thread(client.create, Extraction, messages)
            
            logger.info(f"Structured: {item.title[:50]}")
            return CleanItem(
                hash=get_hash(item),
                title=item.title,
                url=item.url,
                summary=ext.summary,
                ig=item.ig,
                source=item.source,
                category=ext.category,
                deadline=ext.deadline,
                score=entry["score"],
                status=entry["status"],
                created_at=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Extraction failed for {item.url}: {e}")
            return CleanItem(
                hash=get_hash(item),
                title=item.title,
                url=item.url,
                summary="[Failed to extract summary]",
                ig=item.ig,
                source=item.source,
                category="other",
                deadline=None,
                score=entry["score"],
                status="flagged",
                created_at=datetime.now().isoformat()
            )

async def run_structurer(verified_entries):
    if not verified_entries:
        return []
        
    settings = load_config("settings")["pipeline"]
    routing = settings.get("ig_routing", {})
    semaphore = asyncio.Semaphore(settings["structurer_concurrency"])
    
    logger.info(f"Structuring {len(verified_entries)} items with tiered routing (Concurrency: {settings['structurer_concurrency']})...")
    final = []
    
    async def process_entry(entry):
        item = entry["item"]
        
        # 1. Resolve Tier
        ig_cfg = routing.get(item.ig) or routing.get("default", {})
        target_tier = ig_cfg.get("structurer", "cheap")
        
        async with semaphore:
            client = make_llm_client("structurer", tier=target_tier)
            limiter = get_limiter(client.provider, client.model)
            
            res = await _structure_one(entry, client, limiter)
            if res:
                # Check per-IG structuring limits (simplified for parallel)
                # We filter at the end if needed to be strict.
                return res
        return None

    results = await asyncio.gather(*[process_entry(e) for e in verified_entries])
    final = [r for r in results if r is not None]
            
    # Mark successfully structured items in the global hash database
    update_hashes_status(final, "structured")
    
    logger.info(f"Structurer: {len(final)} items completed")
    return final
