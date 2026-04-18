import logging
from src.db.database import get_connection

logger = logging.getLogger(__name__)

# Strictly enforced MVPs from Phase 3 Intelligence tagging
MVP_IGS = ["AI", "Data Science", "Web Development", "Cyber Security", "UI/UX"]

def plan_digests():
    """
    Queries database for the highest scored opportunities strictly mapping to each IG.
    Returns a dictionary mapping each IG to a list of its top articles.
    """
    logger.info("Initializing Planner Agent...")
    conn = get_connection()
    cursor = conn.cursor()
    digests = {}
    
    for ig in MVP_IGS:
        # SQLite trick: finding a specific tag within the JSON array by searching the raw string.
        # Ensure we only pick explicitly evaluated content (quality_score >= 5).
        # Limits to Top 5 items per IG week to prevent spam.
        query = '''
            SELECT title, summary, link, quality_score 
            FROM opportunities 
            WHERE ig_tags LIKE ? AND quality_score >= 5
            ORDER BY quality_score DESC
            LIMIT 5
        '''
        # We search exactly for the quoted string e.g., '%"AI"%'
        cursor.execute(query, (f'%"{ig}"%',))
        rows = cursor.fetchall()
        
        opportunities = []
        for r in rows:
            opportunities.append({
                "title": r[0],
                "summary": r[1],
                "link": r[2],
                "score": r[3]
            })
        
        if opportunities:
            digests[ig] = opportunities
            logger.info(f"Planner selected {len(opportunities)} items for {ig}.")
            
    conn.close()
    return digests
