"""Quick test to verify Tavily API is working."""
from pathlib import Path

from dotenv import load_dotenv
from search_engine import get_tavily_results

load_dotenv(Path(__file__).resolve().parent / ".env")

print("Testing Tavily Search API...")
print("-" * 40)

results = get_tavily_results("Artificial intelligence internships", max_results=3)

if results:
    print(f"\n✅ Tavily is working! Got {len(results)} results:\n")
    for i, r in enumerate(results, 1):
        print(f"  {i}. {r['title']}")
        print(f"     {r['url']}\n")
else:
    print("\n❌ No results returned. Check your TAVILY_API_KEY in .env")
