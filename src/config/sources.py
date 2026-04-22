# src/config/sources.py
# Curated list of trusted AI & tech RSS feeds for the Scout Agent.
# Note: Sites like reddit.com, openai.com, news.google.com block automated
# scraping (403 Forbidden) and have been excluded intentionally.

AI_RSS_FEEDS = [
    # --- Major Tech & AI News ---
    "https://www.artificialintelligence-news.com/feed/",
    "https://www.wired.com/feed/category/business/artificial-intelligence/rss",
    "https://www.theverge.com/rss/index.xml",
    "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "https://techcrunch.com/tag/artificial-intelligence/feed/",
    "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",
    "https://www.forbes.com/innovation/artificial-intelligence/feed/",

    # --- Research & Academic ---
    "https://arxiv.org/rss/cs.AI",
    "https://arxiv.org/rss/cs.LG",
    "https://news.mit.edu/rss/topic/artificial-intelligence",
    "https://bair.berkeley.edu/blog/feed.xml",
    "https://deepmind.google/blog/rss.xml",
    "https://blogs.nvidia.com/blog/category/deep-learning/feed/",

    # --- Aggregated / Community ---
    "https://hnrss.org/frontpage?q=AI",  # Hacker News — open access, no bot blocks
]
