# src/config/sources.py
# Curated list of trusted AI & tech RSS feeds for the Scout Agent.
# Note: feedparser.USER_AGENT is configured globally in the agents to prevent
# blocking from sites like openai.com and blog.google.

AI_RSS_FEEDS = [
    # --- Major Tech & AI News ---
    "https://openai.com/news/rss.xml",
    "https://huggingface.co/blog/feed.xml",
    "https://blog.google/technology/ai/rss/",
    "https://deepmind.google/blog/rss.xml",
    "https://blogs.nvidia.com/feed/",
    "https://blogs.nvidia.com/blog/category/deep-learning/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "https://techcrunch.com/tag/artificial-intelligence/feed/",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    "https://planet-ai.net/rss.xml",

    # --- Research & Academic ---
    "https://rss.arxiv.org/rss/cs.AI",
    "https://rss.arxiv.org/rss/cs.LG",
    "https://rss.arxiv.org/rss/cs.CL",
    "https://www.amazon.science/index.rss",
    "https://blog.ml.cmu.edu/feed/",
    "https://lilianweng.github.io/lil-log/feed.xml",
    "https://jalammar.github.io/feed.xml",

    # --- Aggregated / Community ---
    "https://hnrss.org/frontpage?q=AI",
    "https://hnrss.org/best",  # Community-curated best stories — high signal
]


WEB_DEV_RSS_FEEDS = [
    "https://blog.pragmaticengineer.com/rss/",
    "https://github.blog/engineering/feed/",
    "https://slack.engineering/feed",
    "https://devblogs.microsoft.com/feed/",
    "https://aws.amazon.com/blogs/aws/feed/",
    "https://www.producthunt.com/feed",
    "https://hnrss.org/launches",
    "https://hnrss.org/show",
    "https://www.ycombinator.com/blog/feed",
    "https://techcrunch.com/feed/",
    "https://css-tricks.com/feed/",
    "https://smashingmagazine.com/feed/",
    "https://frontendfoc.us/rss",
    "https://davidwalsh.name/feed"
]

UI_UX_RSS_FEEDS = [
    "https://uxdesign.cc/feed",
    "https://www.awwwards.com/blog/feed/",
    "https://uxplanet.org/feed",
    # --- Added: balance coverage (3 → 8 feeds) ---
    "https://www.nngroup.com/feed/rss/",          # Nielsen Norman Group — UX research gold standard
    "https://alistapart.com/main/feed/",           # A List Apart — web design standards & best practices
    "https://designmodo.com/feed/",                # Designmodo — design tools, trends, tutorials
    "https://www.interaction-design.org/literature/feed",  # IxDF — interaction design articles
    "https://uxmovement.com/feed/",                # UX Movement — UI patterns and usability
]

CYBER_SEC_RSS_FEEDS = [
    "https://krebsonsecurity.com/feed/",
    "https://thehackernews.com/feeds/posts/default",
    # --- Added: balance coverage (2 → 8 feeds) ---
    "https://www.bleepingcomputer.com/feed/",      # BleepingComputer — breach reporting & malware
    "https://www.darkreading.com/rss.xml",         # Dark Reading — enterprise security analysis
    "https://www.securityweek.com/feed/",          # SecurityWeek — CVE coverage & breach reports
    "https://feeds.feedburner.com/eset/blog",      # ESET — threat research & malware analysis
    "https://www.cisa.gov/news.xml",               # CISA — US government security advisories
    "https://blog.qualys.com/feed",                # Qualys — vulnerability research
]

DATA_SCIENCE_RSS_FEEDS = [
    "https://medium.com/feed/kaggle-blog",
    "https://towardsdatascience.com/feed",
    "https://www.kdnuggets.com/feed",
    # --- Added: balance coverage (3 → 8 feeds) ---
    "https://blog.dataiku.com/feed",               # Dataiku — enterprise data science & MLOps
    "https://databricks.com/feed",                 # Databricks — lakehouse, Spark, data engineering
    "https://aws.amazon.com/blogs/big-data/feed/", # AWS Big Data — cloud data engineering
    "https://blogs.sas.com/content/feed/",         # SAS — analytics industry insights
    "https://neptune.ai/blog/feed",                # Neptune.ai — MLOps & experiment tracking
]

DEVOPS_RSS_FEEDS = [
    "https://kubernetes.io/feed.xml",              # Kubernetes — orchestration & platform
    "https://aws.amazon.com/blogs/devops/feed/",   # AWS DevOps — CI/CD & cloud delivery
    "https://thenewstack.io/feed/",                # The New Stack — cloud native & platform eng
    "https://www.hashicorp.com/blog/feed.xml",     # HashiCorp — Terraform, Vault, IaC
    "https://www.redhat.com/en/rss/blog",          # Red Hat — Linux, OpenShift, automation
    "https://stackoverflow.blog/feed/",            # Stack Overflow — engineering practice
    "https://www.infoq.com/feed/",                 # InfoQ — architecture & DevOps reporting
]

GAME_DEV_RSS_FEEDS = [
    "https://www.gamedeveloper.com/rss.xml",       # Game Developer (Gamasutra successor)
    "https://80.lv/feed/",                         # 80 Level — art, tech & production
    "https://unity.com/blog/feed",                 # Unity Blog — engine & tooling
    "https://www.gamesindustry.biz/feed",          # GamesIndustry.biz — industry news
    "https://www.pocketgamer.biz/rss/",            # PocketGamer.biz — mobile games market
    "https://gamedevjs.com/feed/",                 # Gamedev.js — web/HTML5 game dev
]

DATA_ANALYTICS_RSS_FEEDS = [
    "https://www.analyticsvidhya.com/feed/",               # Analytics Vidhya — analytics practice
    "https://powerbi.microsoft.com/en-us/blog/feed/",      # Power BI — BI platform updates
    "https://www.kdnuggets.com/feed",                      # KDnuggets — analytics & data mining
    "https://www.datamation.com/feed/",                    # Datamation — enterprise analytics
]

DSA_RSS_FEEDS = [
    "https://dev.to/feed/tag/algorithms",                  # DEV — algorithms
    "https://dev.to/feed/tag/leetcode",                    # DEV — LeetCode practice
    "https://medium.com/feed/tag/competitive-programming", # Medium — competitive programming
    "https://medium.com/feed/tag/algorithms",              # Medium — algorithms
    "https://medium.com/feed/tag/data-structures",         # Medium — data structures
    "https://www.hackerrank.com/blog/feed/",               # HackerRank — problem solving
    "https://www.reddit.com/r/algorithms/.rss",            # r/algorithms — community discussion
    "https://www.codingninjas.com/blog/feed/",             # Coding Ninjas — DSA tutorials
]

BLOCKCHAIN_RSS_FEEDS = [
    "https://cointelegraph.com/rss",                        # Cointelegraph — market & tech news
    "https://www.coindesk.com/arc/outboundfeeds/rss/",      # CoinDesk — industry reporting
    "https://decrypt.co/feed",                             # Decrypt — Web3 & crypto news
    "https://blog.ethereum.org/feed.xml",                  # Ethereum Foundation — protocol updates
    "https://www.theblock.co/rss.xml",                     # The Block — institutional crypto
    "https://cryptoslate.com/feed/",                       # CryptoSlate — market analysis
    "https://bitcoinmagazine.com/.rss/full/",              # Bitcoin Magazine — Bitcoin ecosystem
]

QUANTUM_RSS_FEEDS = [
    "https://quantumcomputingreport.com/feed/",            # Quantum Computing Report — industry
    "https://thequantuminsider.com/feed/",                 # The Quantum Insider — ecosystem news
    "https://www.nature.com/npjqi.rss",                    # npj Quantum Information — research
    "https://www.sciencedaily.com/rss/computers_math/quantum_computers.xml",  # ScienceDaily
    "https://www.nextplatform.com/feed/",                  # The Next Platform — HPC & quantum
]

IOT_ROBOTICS_RSS_FEEDS = [
    "https://www.therobotreport.com/feed/",                # The Robot Report — robotics industry
    "https://spectrum.ieee.org/feeds/topic/robotics.rss",  # IEEE Spectrum — robotics research
    "https://hackaday.com/feed/",                          # Hackaday — hardware & embedded builds
    "https://www.raspberrypi.com/news/feed/",              # Raspberry Pi — SBC & maker projects
    "https://www.roboticsbusinessreview.com/feed/",        # Robotics Business Review
    "https://iot-analytics.com/feed/",                     # IoT Analytics — market research
    "https://spectrum.ieee.org/feeds/topic/consumer-electronics.rss",  # IEEE Spectrum — devices
]

ALL_RSS_FEEDS = {
    "AI": AI_RSS_FEEDS,
    "Web Development": WEB_DEV_RSS_FEEDS,
    "UI/UX": UI_UX_RSS_FEEDS,
    "Cyber Security": CYBER_SEC_RSS_FEEDS,
    "Data Science": DATA_SCIENCE_RSS_FEEDS,
    "Devops": DEVOPS_RSS_FEEDS,
    "Game Dev": GAME_DEV_RSS_FEEDS,
    "Data Analytics": DATA_ANALYTICS_RSS_FEEDS,
    "Data Structures and Algorithm": DSA_RSS_FEEDS,
    "Blockchain": BLOCKCHAIN_RSS_FEEDS,
    "Quantum Computing": QUANTUM_RSS_FEEDS,
    "Internet Of Things (IOT) And Robotics": IOT_ROBOTICS_RSS_FEEDS,
}


def group_feeds_by_url(feeds_by_ig: dict) -> dict:
    """Group {ig: [feed urls]} into {feed url: [igs]} preserving order.

    Shared feed URLs are fetched once and attributed to every IG that lists
    them, instead of being requested repeatedly.
    """
    grouped: dict = {}
    for ig_name, urls in (feeds_by_ig or {}).items():
        for url in urls or []:
            if not url:
                continue
            owners = grouped.setdefault(url, [])
            if ig_name not in owners:
                owners.append(ig_name)
    return grouped

# Source priority boost for quality scoring.
# Added to the LLM quality_score (capped at 10) to prioritize trusted sources.
SOURCE_PRIORITY = {
    "RSS": 2,           # Curated RSS feeds — highest trust
    "Tavily": 0,        # Tavily search — moderate trust
    "DuckDuckGo": 0,    # DuckDuckGo search — no boost
    "API": 1,           # Hackathon APIs — direct source
    "Firecrawl": 1,     # Firecrawl scraped — direct source
}

# First-party domains that get an extra scoring boost.
# Items from these domains are more likely to be original announcements.
FIRST_PARTY_DOMAINS = [
    "openai.com",
    "deepmind.google",
    "blog.google",
    "blogs.nvidia.com",
    "huggingface.co",
    "anthropic.com",
    "meta.ai",
    "ai.meta.com",
    "github.blog",
    "devblogs.microsoft.com",
    "aws.amazon.com",
    "cloud.google.com",
    "figma.com",
    "cisa.gov",
]
