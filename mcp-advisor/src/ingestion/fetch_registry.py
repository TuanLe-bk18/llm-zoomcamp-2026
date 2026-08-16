import json
import urllib.request
import re
import os

OFFICIAL_REPO_URL = "https://raw.githubusercontent.com/modelcontextprotocol/servers/main/README.md"
AWESOME_REPO_URL = "https://raw.githubusercontent.com/punkpeye/awesome-mcp-servers/main/README.md"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "servers.json")

def fetch_content(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        return response.read().decode('utf-8')

def extract_repos(content, source_name):
    # Extract github URLs: https://github.com/owner/repo
    pattern = re.compile(r'https://github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)')
    matches = pattern.findall(content)
    
    servers = []
    seen = set()
    
    for owner, repo in matches:
        repo_id = f"{owner}/{repo}"
        # Skip duplicates but maintain order
        if repo_id in seen:
            continue
        seen.add(repo_id)
        
        servers.append({
            "server_id": repo_id,
            "name": repo,
            "description": f"MCP server from {repo_id}",
            "repository": f"https://github.com/{repo_id}",
            "version": "unknown",
            "package_endpoint": f"github:{repo_id}",
            "transport": "unknown",
            "source": source_name,
            "owner": owner,
            "repo": repo
        })
    return servers

def fetch_registry():
    print("Fetching registries...")
    
    try:
        official_content = fetch_content(OFFICIAL_REPO_URL)
        official_servers = extract_repos(official_content, "Official MCP Reference Servers (modelcontextprotocol/servers)")
    except Exception as e:
        print(f"Error fetching official registry: {e}")
        official_servers = []

    try:
        awesome_content = fetch_content(AWESOME_REPO_URL)
        awesome_servers = extract_repos(awesome_content, "Community (awesome-mcp-servers)")
    except Exception as e:
        print(f"Error fetching awesome registry: {e}")
        awesome_servers = []
        
    # Merge deterministically
    final_servers = []
    seen = set()
    
    for s in official_servers + awesome_servers:
        if s['server_id'] not in seen:
            seen.add(s['server_id'])
            final_servers.append(s)
            
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_servers, f, indent=2)
        
    print(f"Successfully saved {len(final_servers)} servers to {OUTPUT_FILE}")

if __name__ == "__main__":
    fetch_registry()
