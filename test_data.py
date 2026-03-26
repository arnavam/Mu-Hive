from newsapi import NewsApiClient
from openai import OpenAI
import feedparser
import os

API_KEY = os.environ.get("NEWSAPI_KEY", "your_newsapi_key_here")

newsapi = NewsApiClient(api_key=API_KEY)

# OpenRouter LLM client for generating summaries
llm_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "your_openrouter_api_key_here"),
)


def generate_summary(title):
    """Generate a short summary for an article using the LLM when one is not available."""
    try:
        response = llm_client.chat.completions.create(
            model="openai/gpt-oss-120b:free",
            messages=[
                {
                    "role": "user",
                    "content": f"Write a concise 1-2 sentence summary for a news article titled: \"{title}\". Only return the summary, nothing else."
                }
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"(Summary generation failed: {e})"


print("\n========== NEWSAPI ARTICLES ==========\n")

newsapi_articles = newsapi.get_everything(
    q="AI OR artificial intelligence OR generative AI OR machine learning OR LLM",
    domains="techcrunch.com,theverge.com,venturebeat.com,wired.com,technologyreview.com,arstechnica.com,engadget.com,zdnet.com,thenextweb.com,artificialintelligence-news.com,syncedreview.com,aitrends.com,towardsdatascience.com,analyticsindiamag.com,machinelearningmastery.com",
    language="en",
    sort_by="publishedAt",
    page_size=10
)

for article in newsapi_articles["articles"]:
    title = article.get("title", "No title")
    summary = article.get("description", "")

    if not summary:
        summary = generate_summary(title)

    print("Title:", title)
    print("URL:", article.get("url", "No URL"))
    print("Summary:", summary)
    print("-" * 60)

rss_feeds = {
    "OpenAI": "https://openai.com/blog/rss/",
    "DeepMind": "https://www.deepmind.com/blog/rss.xml",
    "Hugging Face": "https://huggingface.co/blog/feed.xml",
    "Google AI": "https://ai.googleblog.com/feeds/posts/default",
    "Anthropic": "https://www.anthropic.com/news/rss",
    "Stability AI": "https://stability.ai/blog/rss",
    "NVIDIA": "https://blogs.nvidia.com/feed/",

    # X (Twitter) via Nitter RSS
    "Andrej Karpathy": "https://nitter.net/karpathy/rss",
    "Yann LeCun": "https://nitter.net/ylecun/rss",
    "François Chollet": "https://nitter.net/fchollet/rss",
    "Lilian Weng": "https://nitter.net/lilianweng/rss",
    "Rowan Cheung": "https://nitter.net/rowancheung/rss",
    "Sam Altman": "https://nitter.net/sama/rss",
    "Jeff Dean": "https://nitter.net/JeffDean/rss",
    "Demis Hassabis": "https://nitter.net/demishassabis/rss",
    "Andrew Ng": "https://nitter.net/AndrewYNg/rss",
    "Lex Fridman": "https://nitter.net/lexfridman/rss"
}

print("\n========== RSS AI BLOGS ==========\n")

for url in rss_feeds.values():

    feed = feedparser.parse(url)

    for entry in feed.entries[:5]:
        title = getattr(entry, "title", "No title")
        summary = getattr(entry, "summary", "")

        if not summary:
            summary = generate_summary(title)

        print("Title:", title)
        print("URL:", getattr(entry, "link", "No URL"))
        print("Summary:", summary)
        print("-" * 60)