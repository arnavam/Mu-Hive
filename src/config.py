import os
import yaml
from dotenv import load_dotenv

# Load .env file at the start
load_dotenv()

_config_cache = {}

# Reads any yaml from config/ folder, cached after first load
def load_config(name):
    if name not in _config_cache:
        path = os.path.join("config", f"{name}.yaml")
        with open(path, "r") as f:
            _config_cache[name] = yaml.safe_load(f)
    return _config_cache[name]
