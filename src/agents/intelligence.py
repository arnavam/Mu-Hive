# src/agents/intelligence.py

import json
import logging
import time
from typing import List, Literal
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from src.db.database import get_connection
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
        description="Select the most relevant Interest Groups. Must select at least 'AI' for AI news."
    )


intelligence_agent = Agent(
    model,
    output_type=OpportunityIntelligence,
    system_prompt=(
        "You are an expert technical intelligence agent for Mu-Hive. "
        "Your job is to read the title and summary of a scraped tech article/opportunity. "
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
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, title, summary FROM opportunities WHERE quality_score IS NULL LIMIT ?",
        (batch_limit,)
    )
    rows = cursor.fetchall()

    if not rows:
        logger.info("No new opportunities require evaluation.")
        conn.close()
        return

    processed_count = 0
    for row in rows:
        item_id, title, summary = row
        prompt = f"Title: {title}\nSummary: {summary}\n\nEvaluate and classify this."
        logger.info(f"Evaluating ID {item_id}: {title[:60]}...")

        try:
            result = intelligence_agent.run_sync(prompt)
            intelligence: OpportunityIntelligence = result.output

            # Drop score to 0 if flagged as completely irrelevant/spam
            final_score = intelligence.quality_score if intelligence.is_relevant else 0
            tags_json = json.dumps(intelligence.ig_tags)

            cursor.execute('''
                UPDATE opportunities 
                SET quality_score = ?, ig_tags = ?, is_processed = 1
                WHERE id = ?
            ''', (final_score, tags_json, item_id))
            processed_count += 1
            logger.info(f"  -> Score: {final_score} | Tags: {tags_json}")

            # Rate limit: wait between calls to stay under Groq free tier (30 req/min)
            time.sleep(3)

        except Exception as e:
            logger.error(f"Intelligence processing failed for ID {item_id}: {e}")
            # Mark as processed with score 0 to avoid infinite retry loops
            cursor.execute(
                'UPDATE opportunities SET is_processed = 1, quality_score = 0 WHERE id = ?',
                (item_id,)
            )

    conn.commit()
    conn.close()
    logger.info(f"Intelligence Agent finished. Evaluated {processed_count}/{len(rows)} items.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_intelligence()
