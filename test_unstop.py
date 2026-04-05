import requests
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
r = requests.get("https://unstop.com/api/public/opportunity/search-result?opportunity=hackathons&page=1&per_page=20", headers=headers)
print(r.status_code)
print(str(r.json())[:300])
