"""Check GitHub API access and list remote files."""
import urllib.request
import json

url = "https://api.github.com/repos/wcy88/HyperBrain/contents"
req = urllib.request.Request(url, headers={"User-Agent": "HyperBrain-Push"})
try:
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read().decode())
    print(f"Status: {resp.status}, Files: {len(data)}")
    for item in data[:10]:
        print(f"  {item['type']}: {item['name']}")
except Exception as e:
    print(f"Error: {e}")