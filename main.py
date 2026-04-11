import logging
import os
from dotenv import load_dotenv

# Load environment variables before any other imports that depend on them
load_dotenv()

from src.db.database import init_db
from src.agents.scout import run_scout
from src.agents.intelligence import run_intelligence
from src.agents.communicator import run_communicator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_pipeline():
    """Executes the full Mu-Hive intelligence pipeline sequentially."""
    logger.info("=" * 50)
    logger.info("Mu-Hive Intelligence Pipeline - Starting")
    logger.info("=" * 50)

    logger.info("Phase 1: Initializing database...")
    init_db()

    logger.info("Phase 2: Running Scout Agent (RSS feed collection)...")
    run_scout()

    logger.info("Phase 3: Running Intelligence Agent (LLM evaluation)...")
    run_intelligence(batch_limit=15)

    logger.info("Phase 4: Running Communicator (curated digest output)...")
    run_communicator()

    logger.info("Pipeline execution complete.")


if __name__ == "__main__":
    run_pipeline()
