import logging
from src.agents.planner import plan_digests

logger = logging.getLogger(__name__)


def format_digest(ig, opportunities):
    """Formats a curated digest block for terminal display."""
    separator = "=" * 60
    output = f"\n{separator}\n"
    output += f"  >> TOP {ig.upper()} OPPORTUNITIES\n"
    output += f"{separator}\n\n"

    for idx, opp in enumerate(opportunities, 1):
        output += f"  {idx}. {opp['title']}\n"
        output += f"     Score: {opp['score']}/10\n"
        output += f"     Link:  {opp['link']}\n"
        # Truncate long summaries for clean terminal output
        summary = opp['summary'][:200]
        if len(opp['summary']) > 200:
            summary += "..."
        output += f"     {summary}\n\n"

    return output


def run_communicator():
    """Curates and displays the top-scored opportunities per Interest Group."""
    logger.info("Initializing Communicator Agent...")
    digests = plan_digests()

    if not digests:
        logger.warning("No opportunities passed quality threshold (score >= 5). Nothing to display.")
        return

    print("\n" + "=" * 60)
    print("       MU-HIVE INTELLIGENCE DIGEST")
    print("=" * 60)

    for ig, opportunities in digests.items():
        digest_text = format_digest(ig, opportunities)
        print(digest_text)
        logger.info(f"Displayed {len(opportunities)} curated items for IG: {ig}")

    print("=" * 60)
    print("  Pipeline complete. All digests displayed above.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_communicator()
