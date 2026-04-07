from ddgs import DDGS
import requests
from bs4 import BeautifulSoup
import time
from database import Database

def get_brave_results(query, max_results=5):
    """Scrape top results from Brave Search."""
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://search.brave.com/search?q={query}"
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    results = []
    # Brave results usually have the class 'snippet'
    for div in soup.find_all('div', class_='snippet'):
        title_tag = div.find('div', class_='title')
        a_tag = div.find('a')
        if title_tag and a_tag:
            title = title_tag.get_text(strip=True)
            link = a_tag.get('href')
            results.append({'title': title, 'href': link})
            if len(results) >= max_results:
                break
    return results

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
                print(f"   [!] DuckDuckGo failed ({ddg_error}). Falling back to Brave...")
                source_engine = 'Brave Search'
                time.sleep(2)  # Avoid fast consecutive requests
                try:
                    results = get_brave_results(query, max_result)
                except Exception as b_error:
                    print(f"   [!] Brave Search also failed: {b_error}")

            if not results:
                print("   No results found.")
            else:
                for i, result in enumerate(results, start=1):
                    title = result.get('title', 'No Title')
                    link = result.get('href', 'No Link')
                    print(f"{i}. [{source_engine}] {title}")
                    print(f"   Link: {link}")
                    
                    if not db.link_exists(link, query):
                        db.insert_event(title, link, query, source_engine, 'not processed')
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
 