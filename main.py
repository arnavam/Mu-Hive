import logging
import os
from dotenv import load_dotenv

# Load environment variables before any other imports that depend on them
load_dotenv()

from src.orchestrator import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

if __name__ == "__main__":
    run_pipeline()
