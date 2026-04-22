import asyncio
import sys
import argparse
from src.orchestrator import orchestrator

async def main():
    parser = argparse.ArgumentParser(description="Mu-Hive Intelligence Pipeline")
    parser.add_argument("--urls", nargs="+", help="One or more URLs to process")
    parser.add_argument("--mode", choices=["scrape", "crawl"], default="scrape", help="Scraping mode")
    parser.add_argument("--file", help="Path to a text file containing URLs (one per line)")

    args = parser.parse_args()

    target_urls = []
    
    if args.urls:
        target_urls.extend(args.urls)
    
    if args.file:
        try:
            with open(args.file, 'r') as f:
                target_urls.extend([line.strip() for line in f if line.strip()])
        except Exception as e:
            print(f"Error reading file {args.file}: {e}")
            return

    if not target_urls:
        print("Usage examples:")
        print("  python main.py --urls https://example.com")
        print("  python main.py --urls https://site1.com https://site2.com --mode crawl")
        print("  python main.py --file links.txt")
        return

    print(f"=== Mu-Hive Pipeline Started (Total URLs: {len(target_urls)}) ===")
    results = await orchestrator.run_batch(target_urls, mode=args.mode)
    print("=== Pipeline Completed ===")
    
    # Simple summary of results
    for res in results:
        status = "✅ Success" if "error" not in res else "❌ Failed"
        print(f"- {res['url']}: {status}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Pipeline stopped by user.")
    except Exception as e:
        print(f"\n[!] Fatal error: {e}")
