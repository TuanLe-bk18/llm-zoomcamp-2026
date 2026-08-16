import json
import os
import urllib.request
import urllib.error
import concurrent.futures
import time
import subprocess

INPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "servers.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "documents.json")

def get_default_branch(owner, repo):
    try:
        url = f"https://github.com/{owner}/{repo}"
        result = subprocess.run(["git", "ls-remote", "--symref", url, "HEAD"], capture_output=True, text=True, timeout=10)
        # Output looks like: ref: refs/heads/main	HEAD
        for line in result.stdout.splitlines():
            if line.startswith("ref: refs/heads/"):
                parts = line.split("\\t")
                if len(parts) > 0:
                    ref_path = parts[0].replace("ref: refs/heads/", "").strip()
                    return ref_path
    except Exception as e:
        pass
    return None

def fetch_url(url, retries=3, backoff=1.5):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.read().decode('utf-8', errors='ignore')
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None # Don't retry 404
            time.sleep(backoff * (attempt + 1))
        except Exception as e:
            if attempt == retries - 1:
                raise e
            time.sleep(backoff * (attempt + 1))
    return None

def fetch_readme(server):
    owner = server.get('owner')
    repo = server.get('repo')
    
    if not owner or not repo:
        return server, False, "Missing owner or repo"
        
    branches_to_try = ["main", "master"]
    
    # Try common branches first
    for branch in branches_to_try:
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
        try:
            content = fetch_url(url)
            if content and len(content.strip()) > 0:
                server['readme'] = content
                server['readme_url'] = url
                print(f"[OK] {owner}/{repo} (branch: {branch})")
                return server, True, None
        except Exception as e:
            pass
            
    # If main and master fail, try finding the default branch
    try:
        default_branch = get_default_branch(owner, repo)
        if default_branch and default_branch not in branches_to_try:
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}/README.md"
            content = fetch_url(url)
            if content and len(content.strip()) > 0:
                server['readme'] = content
                server['readme_url'] = url
                print(f"[OK] {owner}/{repo} (branch: {default_branch})")
                return server, True, None
    except Exception as e:
        print(f"[FAILED] {owner}/{repo} - git ls-remote error: {str(e)}")
        
    # Still nothing, maybe the repo is gone or has no README.md
    error_msg = f"README.md not found on main/master/default"
    print(f"[FAILED] {owner}/{repo} - {error_msg}")
    return server, False, error_msg

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        servers = json.load(f)
        
    print(f"Found {len(servers)} servers to process.")
    
    # Process ALL servers
    servers_to_process = servers
    
    print(f"Starting parallel download for {len(servers_to_process)} servers...")
    
    documents = []
    failed_servers = []
    
    # Reduced concurrency to avoid rate limits
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_readme, s): s for s in servers_to_process}
        for future in concurrent.futures.as_completed(futures):
            try:
                server, success, error_msg = future.result()
                if success:
                    documents.append(server)
                else:
                    failed_servers.append({
                        "server_id": server.get("server_id"),
                        "owner": server.get("owner"),
                        "repo": server.get("repo"),
                        "error": error_msg
                    })
            except Exception as e:
                s = futures[future]
                print(f"[ERROR] Unhandled exception for {s.get('owner')}/{s.get('repo')}: {str(e)}")
                failed_servers.append({
                    "server_id": s.get("server_id"),
                    "owner": s.get("owner"),
                    "repo": s.get("repo"),
                    "error": str(e)
                })
                
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2)
        
    print(f"\\nFinished! Successfully extracted READMEs for {len(documents)} / {len(servers_to_process)} servers.")
    print(f"Documents saved to: {OUTPUT_FILE}")
    
    # Save failed servers to a log file for review
    failed_log = os.path.join(os.path.dirname(OUTPUT_FILE), "failed_servers.json")
    with open(failed_log, 'w', encoding='utf-8') as f:
        json.dump(failed_servers, f, indent=2)
    print(f"Failed servers logged to: {failed_log}")

if __name__ == "__main__":
    main()
