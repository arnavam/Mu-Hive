import json
import os
from loguru import logger
from src.config import load_config
from src.state_manager import get_hash

def run_classifier(items):
    """
    Deduplication and Blocklist filtering.
    Matches 'classifier' role in agent-based structure.
    """
    pipeline_cfg = load_config("pipeline")
    blocklist = load_config("blocklist")
    
    hash_file = pipeline_cfg.get("seen_hashes_file", "data/seen_hashes.json")
    
    # Load seen hashes
    if os.path.exists(hash_file):
        with open(hash_file, "r") as f:
            try:
                seen_data = json.load(f)
                if isinstance(seen_data, list):
                    seen_hashes = {h: {"status": "seen"} for h in seen_data}
                else:
                    seen_hashes = seen_data
            except Exception:
                seen_hashes = {}
    else:
        seen_hashes = {}
        
    passed = []
    dropped_dups = 0
    dropped_block = 0
    
    blocked_words = [w.lower() for w in blocklist.get("words", [])]
    blocked_domains = [d.lower() for d in blocklist.get("domains", [])]
    
    for item in items:
        # Check domain blocklist
        domain = item.url.split("//")[-1].split("/")[0].lower()
        if any(d in domain for d in blocked_domains):
            dropped_block += 1
            continue
            
        # Check word blocklist
        content = f"{item.title} {item.text}".lower()
        if any(w in content for w in blocked_words):
            dropped_block += 1
            continue
            
        # Check duplicate & Status
        h = get_hash(item)
        if h in seen_hashes:
            status = seen_hashes[h].get("status", "seen")
            if status == "structured":
                dropped_dups += 1
                continue
            item.status = status
        
        passed.append(item)
        if h not in seen_hashes:
            seen_hashes[h] = {"status": "seen", "source_id": item.source}
        
    # Save hashes
    os.makedirs(os.path.dirname(hash_file), exist_ok=True)
    with open(hash_file, "w") as f:
        json.dump(seen_hashes, f, indent=2)
        
    logger.info(f"Classifier: {len(items)} in -> {len(passed)} out ({dropped_dups} dups, {dropped_block} blocked)")
    return passed
