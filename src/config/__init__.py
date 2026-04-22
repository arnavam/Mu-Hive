import os
import yaml
from dotenv import load_dotenv

# Load .env file at the start
load_dotenv()

_config_cache = None

def load_config(section=None):
    """Loads the consolidated config.yaml from root."""
    global _config_cache
    if _config_cache is None:
        # Looking for config.yaml in the root (one level up from src)
        # However, to keep it simple and portable, we assume it's in the CWD
        # which is usually the project root.
        path = "config.yaml"
        if not os.path.exists(path):
            # Fallback for when running from within src/ or tests/
            path = os.path.join(os.path.dirname(__file__), "../../config.yaml")
        
        with open(path, "r") as f:
            _config_cache = yaml.safe_load(f)
            
    if section:
        return _config_cache.get(section, {})
    return _config_cache
