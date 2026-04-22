import asyncio
import random
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger
from src.llm import make_llm_client, get_limiter
from src.retry import with_retry
from src.config import load_config
from src.state_manager import update_hashes_status, get_hash
from src.db.data_schemas import CleanItem
from src.agent_config import AGENT_PROMPTS

class Extraction(BaseModel):
    summary: str = Field(description="2-sentence summary")
    category: str = Field(description="One of the provided categories")
    deadline: Optional[str] = Field(description="Deadline date if found")

@with_retry
async def _structure_one(entry, client, limiter):
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

async def run_summarizer(verified_entries):
    """
    Summarizes and structures verified items.
    Matches 'summarizer' agent role.
    """
    if not verified_entries:
        return []
        
    pipeline_cfg = load_config("pipeline")
    routing = pipeline_cfg.get("ig_routing", {})
    semaphore = asyncio.Semaphore(pipeline_cfg.get("structurer_concurrency", 2))
    
    logger.info(f"Summarizing {len(verified_entries)} items (Concurrency: {pipeline_cfg.get('structurer_concurrency', 2)})...")
    
    async def process_entry(entry):
        item = entry["item"]
        ig_cfg = routing.get(item.ig) or routing.get("default", {})
        target_tier = ig_cfg.get("structurer", "cheap")
        
        async with semaphore:
            client = make_llm_client("structurer", tier=target_tier)
            limiter = get_limiter(client.provider, client.model)
            
            return await _structure_one(entry, client, limiter)

    results = await asyncio.gather(*[process_entry(e) for e in verified_entries])
    final = [r for r in results if r is not None]
            
    # Mark successfully structured items
    update_hashes_status(final, "structured")
    
    logger.info(f"Summarizer: {len(final)} items completed")
    return final
