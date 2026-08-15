import json
import os
import urllib.request
import concurrent.futures

INPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "servers.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "documents.json")

def fetch_readme(server):
    owner = server.get('owner')
    repo = server.get('repo')
    if not owner or not repo:
        return None
        
    branches = ["main", "master"]
    content = ""
    
    for branch in branches:
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            with urllib.request.urlopen(req, timeout=5) as response:
                content = response.read().decode('utf-8', errors='ignore')
                if len(content.strip()) > 0:
                    server['readme'] = content
                    server['readme_url'] = url
                    print(f"[OK] {owner}/{repo}")
                    return server
        except Exception:
            continue
            
    print(f"[FAILED] {owner}/{repo}")
    return None

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        servers = json.load(f)
        
    print(f"Found {len(servers)} servers to process.")
    
    # We will slice to first 300 to keep it manageable and high quality for the MVP, 
    # but still large enough for a real-world evaluation dataset.
    # Note: awesome-mcp-servers lists curated items first, but extracting all github links might include extraneous links.
    servers_to_process = servers[:300]
    
    print(f"Starting parallel download for {len(servers_to_process)} servers...")
    
    documents = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(fetch_readme, servers_to_process))
        for r in results:
            if r is not None:
                documents.append(r)
                
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2)
        
    print(f"\nFinished! Successfully extracted READMEs for {len(documents)} / {len(servers_to_process)} servers.")
    print(f"Documents saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
