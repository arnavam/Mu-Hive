import asyncio
import random
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from loguru import logger
from src.llm import make_llm_client, get_limiter
from src.retry import with_retry
from src.config import load_config
from src.state_manager import update_hashes_status
from src.agent_config import AGENT_PROMPTS
from src.db.data_schemas import RawItem

class Verification(BaseModel):
    is_real: bool = Field(description="Is this a genuine tech opportunity or significant industry news?")
    is_relevant: bool = Field(description="Is this relevant to the specified Interest Group?")
    score: float = Field(description="Relevancy score from 0.0 to 1.0", ge=0, le=1)
    reason: str = Field(description="One sentence justification")

@with_retry
async def _verify_one(item: RawItem, client, limiter, min_score: float) -> Optional[Dict]:
    """Internal helper to verify a single item using an LLM."""
    groups = load_config("interest_groups")
    ig_keywords = ", ".join(groups.get(item.ig, {}).get("keywords", []))
    
    system_prompt = AGENT_PROMPTS["validater"].format(ig=item.ig, keywords=ig_keywords)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Title: {item.title}\nText: {item.text[:2000]}"}
    ]
    
    # Small random jitter to prevent burst TPM hits
    await asyncio.sleep(random.uniform(0.5, 2.0))
    
    async with limiter:
        try:
            # client.create is an OpenAI-style call wrapped in asyncio.to_thread in llm_client
            verif: Verification = await asyncio.to_thread(client.create, Verification, messages)
            
            if not verif.is_real or not verif.is_relevant or verif.score < min_score:
                logger.info(f"Dropped ({verif.score:.2f}): {item.title[:50]}")
                return None
                
            logger.info(f"Verified ({verif.score:.2f}): {item.title[:50]}")
            return {"item": item, "score": verif.score, "status": "ready"}
            
        except Exception as e:
            logger.error(f"LLM error during validation for {item.url}: {e}")
            return {"item": item, "score": 0.0, "status": "flagged"}

async def run_validater(items: List[RawItem]) -> List[Dict]:
    """
    The Validation Agent: Confirms genuineness and relevance.
    1. Uses tiered routing (Cheap/Premium) based on config.
    2. Escalates 'gray-zone' results to the premium model.
    3. Respects rate limits using a local semaphore.
    """
    if not items:
        return []
        
    pipeline_cfg = load_config("pipeline")
    routing = pipeline_cfg.get("ig_routing", {})
    min_score = pipeline_cfg.get("min_verified_score", 0.5)
    max_premium = pipeline_cfg.get("max_premium_items_per_run", 50)
    
    premium_used = 0
    premium_lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(pipeline_cfg.get("verifier_concurrency", 1))
    
    logger.info(f"Validating {len(items)} items using multi-tier AI...")
    
    async def process_item(item: RawItem):
        nonlocal premium_used
        
        # 1. Skip if already verified (caching check)
        if getattr(item, "status", None) == "verified":
            logger.info(f"Cache Hit: {item.title[:50]} (Already verified)")
            return {"item": item, "score": 1.0, "status": "ready"}
            
        # 2. Resolve Tier (Cheap vs Premium)
        ig_cfg = routing.get(item.ig) or routing.get("default", {})
        target_tier = ig_cfg.get("verifier", "cheap")
        
        async with premium_lock:
            if target_tier == "premium" and premium_used >= max_premium:
                logger.warning(f"Premium quota reached. Reverting {item.ig} to cheap tier.")
                target_tier = "cheap"
            
        # 3. Execute Verification
        async with semaphore:
            client = make_llm_client("verifier", tier=target_tier)
            limiter = get_limiter(client.provider, client.model)
            
            result = await _verify_one(item, client, limiter, min_score)
            
            # 4. Premium tracking and Heuristic Escalation
            if result:
                if target_tier == "premium":
                    async with premium_lock:
                        premium_used += 1
                
                # Escalation: If a cheap model gives a 'maybe' score (0.6 - 0.8), use the heavy-hitter.
                elif 0.6 <= result["score"] < 0.8:
                    can_escalate = False
                    async with premium_lock:
                        if premium_used < max_premium:
                            can_escalate = True
                    
                    if can_escalate:
                        logger.info(f"Gray zone ({result['score']:.2f}) for '{item.title[:30]}' -> Escalating to Premium.")
                        p_client = make_llm_client("verifier", tier="premium")
                        p_limiter = get_limiter(p_client.provider, p_client.model)
                        p_res = await _verify_one(item, p_client, p_limiter, min_score)
                        if p_res:
                            result = p_res
                            async with premium_lock:
                                premium_used += 1
            
            return result

    # Run everything in parallel (semaphore handles the throttling)
    results = await asyncio.gather(*[process_item(item) for item in items])
    final_verified = [r for r in results if r is not None]
            
    # Mark passed items in the state database
    update_hashes_status(final_verified, "verified")
    
    logger.info(f"Validater: {len(final_verified)} items verified (Premium usage: {premium_used})")
    return final_verified
