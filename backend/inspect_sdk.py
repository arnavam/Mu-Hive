from firecrawl import FirecrawlApp
import inspect

app = FirecrawlApp(api_key="123")
sig = inspect.signature(app.crawl)
for name, param in sig.parameters.items():
    print(f"{name}: {param.annotation}")
