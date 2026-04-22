import json
import os
from typing import List, Dict
from loguru import logger
from src.config import load_config
from src.state_manager import get_hash
from src.db.data_schemas import RawItem

def run_classifier(items: List[RawItem]) -> List[RawItem]:
    """
    The Filtering Agent: Cleans raw data before AI processing.
    1. Removes duplicate URLs/hashes from the persistent database.
    2. Filters out items containing blocklisted words or domains.
    """
    if not items:
        return []
        
    pipeline_cfg = load_config("pipeline")
    blocklist_cfg = load_config("blocklist")
    
    # Path to our 'memory' file
    hash_file = pipeline_cfg.get("seen_hashes_file", "data/seen_hashes.json")
    
    # Load previously seen hashes (the system's memory)
    seen_hashes: Dict[str, Dict] = {}
    if os.path.exists(hash_file):
        with open(hash_file, "r") as f:
            try:
                seen_hashes = json.load(f)
            except Exception:
                logger.warning("Could not load seen_hashes.json, starting fresh.")
                seen_hashes = {}
                
    passed_items: List[RawItem] = []
    stats = {"duplicates": 0, "blocked": 0}
    
    blocked_words = [word.lower() for word in blocklist_cfg.get("words", [])]
    blocked_domains = [domain.lower() for domain in blocklist_cfg.get("domains", [])]
    
    for item in items:
        # A. Domain Filter
        domain = item.url.split("//")[-1].split("/")[0].lower()
        if any(blocked_domain in domain for blocked_domain in blocked_domains):
            stats["blocked"] += 1
            continue
            
        # B. Keyword Filter (Title & Full Text)
        content_buffer = f"{item.title} {item.text}".lower()
        if any(blocked_word in content_buffer for blocked_word in blocked_words):
            stats["blocked"] += 1
            continue
            
        # C. Duplicate & Status Check
        item_hash = get_hash(item)
        if item_hash in seen_hashes:
            current_status = seen_hashes[item_hash].get("status", "seen")
            
            # If it's already finished the whole pipeline, skip it!
            if current_status == "structured":
                stats["duplicates"] += 1
                continue
            
            # Otherwise, keep its existing status
            item.status = current_status
        
        passed_items.append(item)
        
        # Mark as seen so we don't pick it up twice in the same day
        if item_hash not in seen_hashes:
            seen_hashes[item_hash] = {"status": "seen", "source": item.source}
        
    # Save our memory back to the file
    os.makedirs(os.path.dirname(hash_file), exist_ok=True)
    with open(hash_file, "w") as f:
        json.dump(seen_hashes, f, indent=2)
        
    logger.info(f"Classifier: {len(items)} items processed -> {len(passed_items)} passed")
    logger.info(f"Summary: {stats['duplicates']} dups removed, {stats['blocked']} blocked by keywords")
    
    return passed_items
