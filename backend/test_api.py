import requests

payload = {
    "url": "https://example.com",
    "mode": "crawl"
}

resp = requests.post('http://localhost:5000/api/scrape', json=payload)
print(resp.status_code)
print(resp.json())
