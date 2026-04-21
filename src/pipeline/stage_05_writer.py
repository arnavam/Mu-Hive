import json
import csv
import os
from loguru import logger
from ..config import load_config

# Console output writer
def _write_console(items, cfg):
    # Get fields from config or use default
    fields = cfg.get("show_fields", ["ig", "category", "deadline", "score", "title"])
    
    # Calculate widths
    widths = {"ig": 15, "category": 12, "deadline": 15, "score": 5, "title": 50, "status": 10}
    
    print("\n" + "="*110)
    header = " | ".join([f"{f.capitalize():<{widths.get(f, 20)}}" for f in fields])
    print(header)
    print("-" * 110)
    
    for item in items:
        data = item.model_dump()
        row_parts = []
        for f in fields:
            val = data.get(f, "")
            if val is None: val = "N/A"
            w = widths.get(f, 20)
            
            if f == "score":
                row_parts.append(f"{float(val):<{w}.2f}")
            else:
                row_parts.append(f"{str(val)[:w]:<{w}}")
        
        print(" | ".join(row_parts))
    print("="*110 + "\n")

# JSON file output writer
def _write_json(items, cfg):
    path = cfg.get("path", "output/results.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = [item.model_dump() for item in items]
    indent = 2 if cfg.get("pretty") else None
    with open(path, "w") as f:
        json.dump(data, f, indent=indent)
    logger.info(f"JSON Output saved to {path}")

# CSV file output writer
def _write_csv(items, cfg):
    path = cfg.get("path", "output/results.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not items:
        return
    keys = items[0].model_dump().keys()
    with open(path, "w", newline="") as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows([item.model_dump() for item in items])
    logger.info(f"CSV Output saved to {path}")

# Main entry point to run all active outputs
def run_outputs(items):
    try:
        outputs = load_config("outputs")["outputs"]
    except Exception:
        logger.error("Could not load outputs config")
        return
    
    for name, cfg in outputs.items():
        if not cfg.get("active"):
            continue
            
        type_ = cfg.get("type")
        if type_ == "console":
            _write_console(items, cfg)
        elif type_ == "json_file":
            _write_json(items, cfg)
        elif type_ == "csv_file":
            _write_csv(items, cfg)
        else:
            logger.warning(f"Unknown output type: {type_}")
