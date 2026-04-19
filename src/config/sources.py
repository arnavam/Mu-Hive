# src/config/sources.py
# Curated list of trusted AI & tech RSS feeds for the Scout Agent.

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
    "https://openai.com/blog/rss.xml",
    "https://blogs.nvidia.com/blog/category/deep-learning/feed/",

    # --- Aggregated / Community ---
    "https://news.google.com/rss/search?q=artificial+intelligence",
    "https://hnrss.org/frontpage?q=AI",
    "https://www.reddit.com/r/artificial/.rss",
    "https://www.reddit.com/r/MachineLearning/.rss",
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
    "AI": AI_RSS_FEEDS,
    "Web Development": WEB_DEV_RSS_FEEDS,
    "UI/UX": UI_UX_RSS_FEEDS,
    "Cyber Security": CYBER_SEC_RSS_FEEDS,
    "Data Science": DATA_SCIENCE_RSS_FEEDS
}
