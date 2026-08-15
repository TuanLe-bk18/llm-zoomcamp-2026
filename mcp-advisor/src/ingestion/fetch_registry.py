import json
import urllib.request
import re
import os

README_URL = "https://raw.githubusercontent.com/punkpeye/awesome-mcp-servers/main/README.md"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "servers.json")

def fetch_registry():
    print(f"Fetching awesome-mcp-servers list from {README_URL}...")
    req = urllib.request.Request(README_URL)
    with urllib.request.urlopen(req) as response:
        content = response.read().decode('utf-8')
    
    # Extract github URLs: https://github.com/owner/repo
    pattern = re.compile(r'https://github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)')
    matches = pattern.findall(content)
    
    unique_repos = list(set(matches))
    print(f"Found {len(unique_repos)} unique GitHub repositories.")
    
    servers = []
    for owner, repo in unique_repos:
        servers.append({
            "name": f"{owner}/{repo}",
            "description": f"MCP server from {owner}/{repo}",
            "repository": {
                "url": f"https://github.com/{owner}/{repo}.git"
            },
            "owner": owner,
            "repo": repo
        })
        
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(servers, f, indent=2)
        
    print(f"Successfully saved {len(servers)} servers to {OUTPUT_FILE}")

if __name__ == "__main__":
    fetch_registry()
