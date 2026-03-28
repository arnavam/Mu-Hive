from ddgs import DDGS
import sqlite3
import time

def init_db():
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT,
            keyword_used TEXT,
            source_engine TEXT,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def run_search_agent():
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting scheduled search agent...")
    conn = init_db()
    cursor = conn.cursor()
    keywords = ["Artificial intelligence", "web development"]
    categories = ["internships", "Current news", "workshops", "events", "hackathons"]

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
                    
                    cursor.execute("SELECT 1 FROM events WHERE link = ?", (link,))
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO events (title, link, keyword_used, source_engine, status)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (title, link, query, 'DuckDuckGo', 'not processed'))
                        conn.commit()
        except Exception as e:
            print(f"   Error searching for '{query}': {e}")
        
        # Small delay to avoid hitting rate limits too quickly
        time.sleep(1)
            
    conn.close()

def main():
    print("Search agent started. Running search...")
    print("Press Ctrl+C to exit.")
    
    # Run the search agent immediately
    run_search_agent()

if __name__ == "__main__":
    main()
