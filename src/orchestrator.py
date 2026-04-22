import logging
from src.agents.scout import run_scout
from src.agents.intelligence import run_intelligence
from src.agents.communicator import run_communicator

logger = logging.getLogger(__name__)

# --- Pipeline Configuration ---
INTELLIGENCE_BATCH_LIMIT = 15

def run_pipeline():
    """Executes the full Mu-Hive intelligence pipeline sequentially.
    Each phase is error-isolated so failures don't block subsequent phases."""
    logger.info("=" * 50)
    logger.info("Mu-Hive Intelligence Pipeline - Starting")
    logger.info("=" * 50)

    # Phase 1: Scout — Search & Scraping
    try:
        logger.info("Phase 1: Running Scout Agent (Search & Scraping)...")
        run_scout()
    except Exception as e:
        logger.error(f"Scout Agent failed: {e}. Continuing with existing data...")

    # Phase 2: Intelligence — LLM evaluation
    try:
        logger.info("Phase 2: Running Intelligence Agent (LLM evaluation)...")
        run_intelligence(batch_limit=INTELLIGENCE_BATCH_LIMIT)
    except Exception as e:
        logger.error(f"Intelligence Agent failed: {e}. Continuing with existing scores...")

    # Phase 3: Communicator — curated digest output
    try:
        logger.info("Phase 3: Running Communicator (curated digest output)...")
        run_communicator()
    except Exception as e:
        logger.error(f"Communicator failed: {e}")

    logger.info("Pipeline execution complete.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_pipeline()
