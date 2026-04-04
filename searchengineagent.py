from ddgs import DDGS
import time
from database import Database

def run_search_agent(keywords, categories):
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting scheduled search agent...")
    db = Database()

    print("--------- Keyword Expansion -------------")
    search_queries = []
    for keyword in keywords:
        for category in categories:
            query = f"{keyword} {category}"
            search_queries.append(query)
            print(f"- {query}")

    print("\n--- Searching DuckDuckGo ---")
    
    ddgs = DDGS()
    for query in search_queries:
        print(f"\nResults for '{query}':")
        try:
            # Get top 5 results for each expanded query
            results = list(ddgs.text(query, max_results=5))
            if not results:
                print("   No results found.")
            else:
                for i, result in enumerate(results, start=1):
                    title = result.get('title', 'No Title')
                    link = result.get('href', 'No Link')
                    print(f"{i}. {title}")
                    print(f"   Link: {link}")
                    
                    if not db.link_exists(link, query):
                        db.insert_event(title, link, query, 'DuckDuckGo', 'not processed')
        except Exception as e:
            print(f"   Error searching for '{query}': {e}")
        
        # Small delay to avoid hitting rate limits too quickly
        time.sleep(1)
             
    db.close()

def main():
    print("Search agent started. Running search...")
    print("Press Ctrl+C to exit.")
    
    keywords = ["Artificial intelligence", "web development"]
    categories = ["internships", "Current news", "workshops", "events", "hackathons"]
    
    # Run the search agent immediately
    run_search_agent(keywords, categories)
 
if __name__ == "__main__":
    main()
 