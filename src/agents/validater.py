import asyncio
from pydantic import BaseModel, Field
from loguru import logger
from src.llm import make_llm_client, get_limiter
from src.retry import with_retry
from src.config import load_config
from src.state_manager import update_hashes_status

class Verification(BaseModel):
    is_real: bool = Field(description="Is this a genuine tech opportunity?")
    is_relevant: bool = Field(description="Is this relevant to the specified Interest Group?")
    score: float = Field(description="Relevancy score from 0.0 to 1.0", ge=0, le=1)
    reason: str = Field(description="One sentence justification")

@with_retry
async def _verify_one(item, client, limiter, min_score):
    groups = load_config("interest_groups")
    ig_keywords = ", ".join(groups.get(item.ig, {}).get("keywords", []))
    
    messages = [
        {"role": "system", "content": f"You are a verifier for the {item.ig} Interest Group. Focus on keywords: {ig_keywords}."},
        {"role": "user", "content": f"Title: {item.title}\nText: {item.text[:2000]}"}
    ]
    
    async with limiter:
        try:
            verif = await asyncio.to_thread(client.create, Verification, messages)
            
            if not verif.is_real or not verif.is_relevant or verif.score < min_score:
                logger.info(f"Dropped ({verif.score:.2f}): {item.title[:50]}")
                return None
                
            logger.info(f"Verified ({verif.score:.2f}): {item.title[:50]}")
            return {"item": item, "score": verif.score, "status": "ready"}
            
        except Exception as e:
            logger.error(f"LLM error for {item.url}: {e}")
            return {"item": item, "score": 0.0, "status": "flagged"}

async def run_validater(items):
    """
    Validates items for genuineness and relevance.
    Matches 'validater' agent role.
    """
    if not items:
        return []
        
    pipeline_cfg = load_config("pipeline")
    routing = pipeline_cfg.get("ig_routing", {})
    min_score = pipeline_cfg.get("min_verified_score", 0.5)
    max_premium = pipeline_cfg.get("max_premium_items_per_run", 50)
    
    premium_used = 0
    premium_lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(pipeline_cfg.get("verifier_concurrency", 2))
    
    logger.info(f"Validating {len(items)} items (Concurrency: {pipeline_cfg.get('verifier_concurrency', 2)})...")
    
    async def process_item(item):
        nonlocal premium_used
        
        # 1. Skip if already verified
        if getattr(item, "status", None) == "verified":
            logger.info(f"Skipping Validater: {item.title[:50]} (Already verified)")
            return {"item": item, "score": 1.0, "status": "ready"}
            
        # 2. Resolve Tier and Check Quota
        ig_cfg = routing.get(item.ig) or routing.get("default", {})
        target_tier = ig_cfg.get("verifier", "cheap")
        
        async with premium_lock:
            if target_tier == "premium" and premium_used >= max_premium:
                logger.warning(f"Premium quota reached. {item.ig} -> cheap.")
                target_tier = "cheap"
            
        # 3. Execute Verification
        async with semaphore:
            client = make_llm_client("verifier", tier=target_tier)
            limiter = get_limiter(client.provider, client.model)
            
            res = await _verify_one(item, client, limiter, min_score)
            
            # 4. Premium tracking and Escalation
            if res:
                if target_tier == "premium":
                    async with premium_lock:
                        premium_used += 1
                
                # Heuristic Escalation (0.6 <= score < 0.8)
                elif 0.6 <= res["score"] < 0.8:
                    can_escalate = False
                    async with premium_lock:
                        if premium_used < max_premium:
                            can_escalate = True
                    
                    if can_escalate:
                        logger.info(f"Gray zone ({res['score']:.2f}) -> Escalating.")
                        p_client = make_llm_client("verifier", tier="premium")
                        p_limiter = get_limiter(p_client.provider, p_client.model)
                        p_res = await _verify_one(item, p_client, p_limiter, min_score)
                        if p_res:
                            res = p_res
                            async with premium_lock:
                                premium_used += 1
            
            return res

    results = await asyncio.gather(*[process_item(item) for item in items])
    final = [r for r in results if r is not None]
            
    # Mark passed items as verified
    update_hashes_status(final, "verified")
    
    logger.info(f"Validater: {len(items)} in -> {len(final)} out (Premium used: {premium_used})")
    return final
