from tenacity import retry, stop_after_attempt, wait_exponential
from src.config import load_config

# Tenacity wrapper using backoff from config.yaml
def with_retry(fn):
    pipeline_cfg = load_config("pipeline")
    return retry(
        stop=stop_after_attempt(pipeline_cfg.get("max_retries", 3)),
        wait=wait_exponential(
            multiplier=2, # Increased multiplier for free tier
            min=pipeline_cfg.get("retry_backoff_seconds", [1, 2, 4])[0], 
            max=pipeline_cfg.get("retry_backoff_seconds", [1, 2, 4])[-1]
        ),
        reraise=True
    )(fn)
