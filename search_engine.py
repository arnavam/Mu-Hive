from ddgs import DDGS
import requests
import time
import os
from dotenv import load_dotenv
from database import Database

load_dotenv()

def run_search_agent(keywords, categories, max_result=5):
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
            results = []
            source_engine = 'DuckDuckGo'
            
            try:
                # Get top results for each expanded query via DuckDuckGo
                results = list(ddgs.text(query, max_results=max_result))
            except Exception as ddg_error:
                print(f"   [!] DuckDuckGo failed ({ddg_error}). Falling back to Tavily...")
                source_engine = 'Tavily'
                time.sleep(2)  # Avoid fast consecutive requests
                try:
                    results = get_tavily_results(query, max_result)
                except Exception as t_error:
                    print(f"   [!] Tavily Search also failed: {t_error}")

            if not results:
                print("   No results found.")
            else:
                for i, result in enumerate(results, start=1):
                    title = result.get('title', 'No Title')
                    link = result.get('href', result.get('url', 'No Link'))
                    print(f"{i}. [{source_engine}] {title}")
                    print(f"   Link: {link}")
                    
                    if not db.link_exists(link, query):
                        db.insert_event(title, link, query, source_engine, 'not processed')
        except Exception as e:
            print(f"   Error searching for '{query}': {e}")
        
        # Small delay to avoid hitting rate limits too quickly
        time.sleep(1)
             
    db.close()

# Searching using Tavily Search API
def get_tavily_results(query, max_results=5):
    """Fetch results from Tavily Search API (fallback when DuckDuckGo fails)."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key or api_key == "your_tavily_api_key_here":
        print("   [!] Tavily API key not configured in .env")
        print("   [!] Get your API key at https://app.tavily.com and add it to .env")
        return []
    
    url = "https://api.tavily.com/search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "query": query,
        "search_depth": "basic",
        "include_answer": False,
        "max_results": max_results
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()
    
    results = []
    for item in data.get('results', [])[:max_results]:
        results.append({
            'title': item.get('title', 'No Title'),
            'url': item.get('url', 'No Link')
        })
    return results


def main():
    print("Search agent started. Running search...")
    print("Press Ctrl+C to exit.")
    
    keywords = ["Artificial intelligence", "web development"]
    categories = ["internships", "Current news", "workshops", "events", "hackathons"]
    
    # Run the search agent immediately
    run_search_agent(keywords, categories)
 
if __name__ == "__main__":
    main()
 
