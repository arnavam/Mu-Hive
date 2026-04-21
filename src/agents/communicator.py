import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from src.agents.planner import plan_digests

logger = logging.getLogger(__name__)
console = Console()

def format_digest(ig, opportunities_by_cat):
    """Prints a curated digest block for terminal display using Rich."""
    console.print(f"\n[bold cyan]>> TOP {ig.upper()} OPPORTUNITIES[/bold cyan]")
    
    for cat_name, opps in opportunities_by_cat.items():
        if not opps: continue
        
        table = Table(title=f"[bold magenta]--- {cat_name.upper()} ---[/bold magenta]", show_lines=True)
        table.add_column("Score", style="yellow", justify="center")
        table.add_column("Details", style="white")

        for opp in opps:
            summary = opp['summary'][:200]
            if len(opp['summary']) > 200:
                summary += "..."
            summary = summary.replace('\\n', '\n')
            
            details = f"[bold]{opp['title']}[/bold]\n[blue][link={opp['link']}]{opp['link']}[/link][/blue]\n[dim]{summary}[/dim]"
            table.add_row(f"{opp['score']}/10", details)
            
        console.print(table)

def run_communicator():
    """Curates and displays the top-scored opportunities per Interest Group."""
    logger.info("Initializing Communicator Agent...")
    digests = plan_digests()

    if not digests:
        logger.warning("No opportunities passed quality threshold (score >= 5). Nothing to display.")
        return

    console.print(Panel.fit("[bold green]MU-HIVE INTELLIGENCE DIGEST[/bold green]"))

    for ig, opportunities_by_cat in digests.items():
        format_digest(ig, opportunities_by_cat)
        total_items = sum(len(cat_list) for cat_list in opportunities_by_cat.values())
        logger.info(f"Displayed {total_items} curated items for IG: {ig}")

    console.print(Panel.fit("[bold green]Pipeline complete. All digests displayed above.[/bold green]"))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_communicator()
