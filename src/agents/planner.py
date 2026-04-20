import logging
from src.db.database import Database

logger = logging.getLogger(__name__)

# Strictly enforced MVPs from Phase 3 Intelligence tagging
MVP_IGS = ["AI", "Data Science", "Web Development", "Cyber Security", "UI/UX"]

def plan_digests():
    """
    Queries database for the highest scored opportunities strictly mapping to each IG.
    Returns a dictionary mapping each IG to a list of its top articles.
    """
    logger.info("Initializing Planner Agent...")
    db = Database()
    digests = {}
    
    for ig in MVP_IGS:
        # Fetch directly from MongoDB helper method
        rows = db.get_top_opportunities_by_ig(ig, limit=5)
        
        opportunities_by_cat = {}
        for r in rows:
            cat = r.get("category", "News")
            if cat not in opportunities_by_cat:
                opportunities_by_cat[cat] = []
                
            opportunities_by_cat[cat].append({
                "title": r.get("title", "No Title"),
                "summary": r.get("summary", ""),
                "link": r.get("link", ""),
                "score": r.get("quality_score", 0)
            })
        
        if opportunities_by_cat:
            digests[ig] = opportunities_by_cat
            total_items = sum(len(cat_list) for cat_list in opportunities_by_cat.values())
            logger.info(f"Planner selected {total_items} items for {ig}.")
            
    db.close()
    return digests

