import logging
import time
from typing import List, Literal
from pydantic import BaseModel, Field
from pydantic_ai import Agent
import asyncio

from src.db.postgres_database import DatabaseFacade as Database
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


INTELLIGENCE_SYSTEM_PROMPT = """\
You are an expert technical intelligence classifier for Mu-Hive, a tech community platform.
Your job is to evaluate scraped articles/opportunities and classify them into the correct Interest Groups (IGs).

## Interest Group Definitions (ONLY tag if content is DIRECTLY about these topics):

- **AI**: Artificial intelligence, machine learning, deep learning, LLMs, NLP, computer vision, neural networks, GenAI, AI research papers, AI tools and frameworks (TensorFlow, PyTorch, Hugging Face).
- **Data Science**: Data analytics, data engineering, big data, data visualization, statistical modeling, Kaggle, pandas, business intelligence, data pipelines.
- **Web Development**: Frontend/backend development, JavaScript, TypeScript, React, Next.js, Node.js, Django, Flask, Vue, Angular, HTML/CSS, web frameworks, APIs, DevOps, cloud deployment.
- **Cyber Security**: Cybersecurity, infosec, ethical hacking, penetration testing, CTFs, vulnerability disclosures, malware analysis, threat intelligence, SOC, network security, zero-day exploits, trojans, phishing, ransomware, NFC attacks, data breaches, APT campaigns.
- **UI/UX**: User experience design, user interface design, UX research, Figma, prototyping, wireframing, interaction design, product design, usability testing, design systems.

## Strict Classification Rules:
1. ONLY tag an IG if the content is DIRECTLY and PRIMARILY about that domain. Do NOT tag loosely related content.
2. Political news, sports, entertainment, world events, opinion pieces about non-tech topics, and general business news are NEVER relevant. Set is_relevant=False and quality_score=1 for these.
3. If the content mentions tech only tangentially (e.g., a political article that briefly mentions AI policy), it is NOT relevant.
4. Be strict with quality scores: 1-3 = low quality/irrelevant, 4-5 = borderline, 6-7 = good, 8-9 = very good, 10 = groundbreaking.
5. If content has no clear connection to ANY tech Interest Group, set is_relevant=False and quality_score=1.
6. A single article can belong to multiple IGs ONLY if it substantively covers multiple domains.

## Common Misclassification Errors — DO NOT make these mistakes:
- Malware, trojans, phishing, NFC attacks, data breaches, ransomware, APT groups → these are ONLY "Cyber Security", NEVER "AI"
- An article about a security vulnerability or hacking campaign is NOT "AI" just because it involves technology
- Hardware news, chip manufacturing, semiconductor news → NOT any IG unless it is specifically about AI chips/models
- General tech company earnings, mergers, layoffs → NOT relevant unless specifically about the IG's domain
- A cybersecurity tool that uses ML internally is still "Cyber Security", NOT "AI" — classify by the article's PRIMARY topic
- Design of physical products, architecture, fashion design → NOT "UI/UX" (UI/UX is digital interface design only)
"""

intelligence_agent = Agent(
    model,
    output_type=OpportunityIntelligence,
    system_prompt=INTELLIGENCE_SYSTEM_PROMPT,
)


# Keywords that strongly indicate a specific IG — used for post-LLM validation
_CYBER_KEYWORDS = {
    "malware", "trojan", "ransomware", "phishing", "vulnerability", "exploit",
    "cve-", "apt", "breach", "nfc attack", "botnet", "zero-day", "0day",
    "backdoor", "infosec", "threat actor", "campaign", "stealing", "fraud",
    "hacker", "hacking", "cyberattack", "data theft", "pin", "atm fraud",
}


def _validate_tags(llm_tags: list, title: str, content: str, source_ig: list) -> list:
    """
    Post-LLM validation: cross-check LLM tags against content keywords
    to catch obvious misclassifications (e.g., malware tagged as AI).
    """
    title_lower = title.lower()
    content_lower = content[:2000].lower() if content else ""
    combined = title_lower + " " + content_lower

    # Check if content is clearly cybersecurity
    is_clearly_cyber = any(kw in combined for kw in _CYBER_KEYWORDS)

    if is_clearly_cyber:
        # If content is clearly cyber, remove AI/Data Science/Web Dev/UI-UX tags
        # unless original source also tagged it as those IGs
        validated = []
        for tag in llm_tags:
            if tag == "Cyber Security":
                validated.append(tag)
            elif tag in source_ig:
                # Trust the source if it originally tagged this IG too
                validated.append(tag)
            else:
                logger.info(
                    f"  -> Validation removed spurious tag '{tag}' (content is clearly Cyber Security)")

        # Ensure Cyber Security is in the list
        if "Cyber Security" not in validated:
            validated.append("Cyber Security")
        return validated

    return llm_tags


async def run_intelligence(batch_limit=15):
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
        category = doc.get("category", "Unknown")
        source_ig = doc.get("ig_tags", [])

        # Include source context so LLM can validate/reject initial classification
        prompt = (
            f"Title: {title}\n"
            f"Category: {category}\n"
            f"Original IG Tags (from source — validate or override these): {
                source_ig}\n"
            f"Content: {content[:3000]}\n\n"
            f"Evaluate this content's relevance and quality. Classify into the correct Interest Groups."
        )
        logger.info(f"Evaluating ID {item_id}: {title[:60]}...")

        try:
            result = await intelligence_agent.run(prompt)
            intelligence: OpportunityIntelligence = result.output

            final_score = intelligence.quality_score if intelligence.is_relevant else 0

            # Post-LLM validation to catch misclassifications
            validated_tags = _validate_tags(
                intelligence.ig_tags, title, content, source_ig)

            db.update_intelligence(item_id, final_score, validated_tags)
            processed_count += 1
            logger.info(
                f"  -> Score: {final_score} | Tags: {validated_tags} | {intelligence.reasoning}")

            await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Intelligence processing failed for ID {
                         item_id}: {e}")
            db.update_intelligence(item_id, 0, [])

    db.close()
    logger.info(f"Intelligence Agent finished. Evaluated {
                processed_count}/{len(docs)} items.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_intelligence())
