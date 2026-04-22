import asyncio
import sys
import os
from loguru import logger
from src.orchestrator import run_pipeline

async def main():
    # Setup Logger
    logger.remove()
    logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
    
    # Environment Check
    if not any(k in os.environ for k in ["TOGETHER_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY"]):
         logger.warning("No LLM API keys found in environment!")
    
    # Argument Parsing
    ig_filter = None
    if "--ig" in sys.argv:
        idx = sys.argv.index("--ig")
        if idx + 1 < len(sys.argv):
             ig_filter = sys.argv[idx + 1]
             logger.info(f"IG Filter: {ig_filter}")

    # Launch Pipeline
    await run_pipeline(ig_filter=ig_filter)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        sys.exit(1)
