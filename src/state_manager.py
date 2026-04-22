import hashlib
import os
import time
import json
from loguru import logger
from src.config import load_config

# Hashing helper
def get_hash(item):
    return hashlib.md5(f"{item.url}{item.title}".encode()).hexdigest()

# Bulk status updater for seen_hashes.json
def update_hashes_status(items, status):
    pipeline_cfg = load_config("pipeline")
    hash_file = pipeline_cfg.get("seen_hashes_file", "data/seen_hashes.json")
    
    if not os.path.exists(hash_file):
        data = {}
    else:
        try:
            with open(hash_file, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
            
    def get_h(url, title):
        return hashlib.md5(f"{url}{title}".encode()).hexdigest()
        
    for item_data in items:
        # entry can be a CleanItem or a dict from verifier
        if isinstance(item_data, dict):
            item = item_data["item"]
        else:
            item = item_data
            
        h = get_h(item.url, item.title)
        if h in data:
            data[h]["status"] = status
            data[h]["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            
    os.makedirs(os.path.dirname(hash_file), exist_ok=True)
    with open(hash_file, "w") as f:
        json.dump(data, f, indent=2)
