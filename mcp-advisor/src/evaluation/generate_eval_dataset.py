import json
import os
import random

INPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "documents.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "eval", "ground_truth.json")

def generate_synthetic_query(server):
    owner = server.get('owner', '')
    repo = server.get('repo', '')
    text = server.get('text', '')
    
    # Simple heuristic to extract a meaningful keyword from repo name
    keywords = repo.replace('mcp', '').replace('server', '').replace('-', ' ').strip()
    if not keywords:
        keywords = owner

    templates = [
        f"I need an MCP that lets an AI work with {keywords}",
        f"Looking for a way to connect Claude to {keywords}",
        f"Is there a {keywords} integration for Model Context Protocol?",
        f"I want to automate my {keywords} workflow locally",
        f"Provide read access to {keywords} data"
    ]
    
    return {
        "query": random.choice(templates),
        "expected_owner": owner,
        "expected_repo": repo,
        "important_constraints": "local access" if "local" in text.lower() else "remote"
    }

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        documents = json.load(f)
        
    # Group by repo
    servers_dict = {}
    for doc in documents:
        key = f"{doc['owner']}/{doc['repo']}"
        if key not in servers_dict:
            servers_dict[key] = doc
            
    unique_servers = list(servers_dict.values())
    print(f"Found {len(unique_servers)} unique servers.")
    
    # Generate 50 realistic use cases
    sample_size = min(50, len(unique_servers))
    sampled = random.sample(unique_servers, sample_size)
    
    eval_dataset = []
    for s in sampled:
        eval_dataset.append(generate_synthetic_query(s))
        
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(eval_dataset, f, indent=2)
        
    print(f"Generated {len(eval_dataset)} evaluation cases at {OUTPUT_FILE}")

if __name__ == "__main__":
    random.seed(42)
    main()
