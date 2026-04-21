from tenacity import retry, stop_after_attempt, wait_exponential
from .config import load_config

# Tenacity wrapper using backoff from settings.yaml
def with_retry(fn):
    settings = load_config("settings")["pipeline"]
    return retry(
        stop=stop_after_attempt(settings["max_retries"]),
        wait=wait_exponential(
            multiplier=2, # Increased multiplier for free tier
            min=settings["retry_backoff_seconds"][0], 
            max=settings["retry_backoff_seconds"][-1]
        ),
        reraise=True
    )(fn)
