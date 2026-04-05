import requests
print("Testing GET")
try:
    r = requests.get("https://api.devfolio.co/api/search/hackathons?page=1&limit=5", timeout=5)
    print(r.status_code, r.text[:300])
except Exception as e:
    print(e)

print("Testing POST")
try:
    r = requests.post("https://api.devfolio.co/api/search/hackathons", json={"from": 0, "size": 5}, timeout=5)
    print(r.status_code, r.text[:300])
except Exception as e:
    print(e)
