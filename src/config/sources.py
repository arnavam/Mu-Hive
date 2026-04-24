# src/config/sources.py
# Curated list of trusted AI & tech RSS feeds for the Scout Agent.
# Note: Sites like reddit.com, openai.com, news.google.com block automated
# scraping (403 Forbidden) and have been excluded intentionally.

AI_RSS_FEEDS = [
    # --- Major Tech & AI News ---
    "https://www.wired.com/feed/category/business/artificial-intelligence/rss",
    "https://www.theverge.com/rss/index.xml",
    "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "https://techcrunch.com/tag/artificial-intelligence/feed/",

    # --- Research & Academic ---
    "https://news.mit.edu/rss/topic/artificial",
    "https://deepmind.google/blog/rss.xml",
    "https://blogs.nvidia.com/blog/category/deep-learning/feed/",

    # --- Aggregated / Community ---
    "https://hnrss.org/frontpage?q=AI",  # Hacker News — open access, no bot blocks
]


WEB_DEV_RSS_FEEDS = [
    "https://css-tricks.com/feed/",
    "https://smashingmagazine.com/feed/",
    "https://frontendfoc.us/rss",
    "https://davidwalsh.name/feed"
]

UI_UX_RSS_FEEDS = [
    "https://uxdesign.cc/feed",
    "https://www.awwwards.com/blog/feed/",
    "https://uxplanet.org/feed"
]

CYBER_SEC_RSS_FEEDS = [
    "https://krebsonsecurity.com/feed/",
    "https://www.darkreading.com/rss",
    "https://thehackernews.com/feeds/posts/default"
]

DATA_SCIENCE_RSS_FEEDS = [
    "https://towardsdatascience.com/feed",
    "https://www.kdnuggets.com/feed",
    "https://datatau.net/rss"
]

ALL_RSS_FEEDS = {
    "ai": AI_RSS_FEEDS,
    "web development": WEB_DEV_RSS_FEEDS,
    "ui ux": UI_UX_RSS_FEEDS,
    "cybersecurity": CYBER_SEC_RSS_FEEDS,
    "data science": DATA_SCIENCE_RSS_FEEDS
}
