import logging
import time
from typing import List, Literal
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from src.db.database import Database
from src.llm.agent_config import model

logger = logging.getLogger(__name__)

class OpportunityIntelligence(BaseModel):
    """Schema enforced by Pydantic AI for LLM structured output."""
    is_relevant: bool = Field(
        description="True if this is informative tech/AI news or a real opportunity. False if spam or irrelevant."
    )
    quality_score: int = Field(
        ge=1, le=10,
        description="Score from 1-10 assessing the novelty, quality, and importance of the article."
    )
    reasoning: str = Field(
        description="A short 1-sentence explanation of the score."
    )
    ig_tags: List[Literal["AI", "Data Science", "Web Development", "Cyber Security", "UI/UX"]] = Field(
        description="Select the most relevant Interest Groups. Must select at least one if relevant."
    )


intelligence_agent = Agent(
    model,
    output_type=OpportunityIntelligence,
    system_prompt=(
        "You are an expert technical intelligence agent for Mu-Hive. "
        "Your job is to read the title and text content of a scraped tech article/opportunity. "
        "You must evaluate its quality on a scale of 1-10 and precisely categorize it into the correct Interest Groups. "
        "Be strict about quality (rarely give 10s unless groundbreaking) and never hallucinate tags outside the provided literals."
    ),
)


def run_intelligence(batch_limit=15):
    """
    Evaluates and classifies unprocessed opportunities using the LLM.
    Processes up to batch_limit items per run to conserve API calls.
    """
    logger.info("Initializing Intelligence Agent (Evaluator + Classifier)...")
    db = Database()

    docs = db.get_unprocessed_for_intelligence(limit=batch_limit)

    if not docs:
        logger.info("No new opportunities require evaluation.")
        db.close()
        return

    processed_count = 0
    for doc in docs:
        item_id = doc["_id"]
        title = doc.get("title", "")
        # Use full extracted text if available; otherwise fallback to summary
        content = doc.get("scraped_full_text") or doc.get("summary", "")
        
        prompt = f"Title: {title}\nContent: {content}\n\nEvaluate and classify this."
        logger.info(f"Evaluating ID {item_id}: {title[:60]}...")

        try:
            result = intelligence_agent.run_sync(prompt)
            intelligence: OpportunityIntelligence = result.output

            final_score = intelligence.quality_score if intelligence.is_relevant else 0
            
            db.update_intelligence(item_id, final_score, intelligence.ig_tags)
            processed_count += 1
            logger.info(f"  -> Score: {final_score} | Tags: {intelligence.ig_tags}")

            time.sleep(3)
        except Exception as e:
            logger.error(f"Intelligence processing failed for ID {item_id}: {e}")
            db.update_intelligence(item_id, 0, [])

    db.close()
    logger.info(f"Intelligence Agent finished. Evaluated {processed_count}/{len(docs)} items.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_intelligence()
