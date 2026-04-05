import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

res = requests.get('https://devfolio.co/hackathons', headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(res.text, 'html.parser')

print("Testing a tags...")

# We know hackathon links end with .devfolio.co
for a in soup.find_all('a', href=True):
    link = a['href']
    parsed = urllib.parse.urlparse(link)
    if parsed.netloc.endswith('.devfolio.co') and parsed.netloc not in ['guide.devfolio.co', 'status.devfolio.co', 'api.devfolio.co']:
        print(f"\n--- Found {link} ---")
        title = a.get_text(strip=True)
        print(f"Title inside a tag: '{title}'")
        
        # Traverse up parents to find more text
        p = a.parent
        for i in range(5):
            if p:
                text = p.get_text(separator=' | ', strip=True)
                print(f"Parent {i+1} text: '{text}'")
                p = p.parent
        break
