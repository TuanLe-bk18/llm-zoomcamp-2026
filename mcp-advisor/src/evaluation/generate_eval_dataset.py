import json
import os
import random
import time
from google import genai
from google.genai import types

INPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "documents.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "eval", "ground_truth.json")

def generate_queries_with_gemini(servers, api_key):
    client = genai.Client(api_key=api_key)
    
    prompt = """
    You are generating an evaluation dataset for a Model Context Protocol (MCP) recommendation system.
    I will provide you with a list of MCP servers and their descriptions.
    For each server, generate ONE realistic user query that a developer might ask when looking for such a tool.
    
    CRITICAL RULES:
    1. The query MUST NOT contain the server name, repository name, or owner name.
    2. The query should describe the capabilities, use cases, or problems the developer is trying to solve.
    3. Include a rationale explaining why this server is relevant.
    4. Provide the output as a JSON array of objects with the exact keys: "server_id", "query", "constraints", "rationale".
    """
    
    server_context = ""
    for s in servers:
        server_context += f"\\n--- Server ID: {s['server_id']} ---\\nDescription: {s.get('description', '')[:500]}\\n"
        
    prompt += server_context
    
    print("Calling Gemini API to generate queries...")
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7
        )
    )
    
    try:
        results = json.loads(response.text)
        formatted_results = []
        for r in results:
            formatted_results.append({
                "query": r.get("query", ""),
                "relevant_server_ids": [r.get("server_id", "")],
                "constraints": r.get("constraints", []),
                "rationale": r.get("rationale", "")
            })
        return formatted_results
    except Exception as e:
        print(f"Failed to parse Gemini response: {e}")
        return []

def generate_fallback_query(server):
    server_id = server.get('server_id', '')
    text = server.get('readme', '')
    
    # Extract meaningful keyword
    topics = server_id.split('/')[-1].replace('mcp', '').replace('server', '').replace('-', ' ').strip()
    if not topics:
        topics = server_id.split('/')[0]

    templates = [
        f"I need a tool that lets an AI agent interact with {topics}",
        f"Looking for a way to connect Claude to {topics}",
        f"Is there a {topics} integration for Model Context Protocol?",
        f"I want to automate my {topics} workflow",
        f"Provide read access to {topics} data"
    ]
    
    constraints = []
    if "local" in text.lower() or "stdio" in text.lower():
        constraints.append("must run locally")
    if "api key" in text.lower() or "token" in text.lower() or "auth" in text.lower():
        constraints.append("requires authentication")
        
    return [{
        "query": random.choice(templates),
        "relevant_server_ids": [server_id],
        "constraints": constraints,
        "rationale": f"The user is looking for {topics} capabilities. The {server_id} server provides exactly this."
    }]

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    api_key = os.getenv("GEMINI_API_KEY")

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        documents = json.load(f)
        
    # Group by server_id
    servers_dict = {}
    for doc in documents:
        key = doc.get('server_id')
        if key and key not in servers_dict:
            servers_dict[key] = doc
            
    unique_servers = list(servers_dict.values())
    print(f"Found {len(unique_servers)} unique servers.")
    
    # Generate 50 realistic use cases
    sample_size = min(50, len(unique_servers))
    sampled = random.sample(unique_servers, sample_size)
    
    eval_dataset = []
    
    if api_key:
        print("Using Gemini API for realistic query generation...")
        batch_size = 10
        for i in range(0, len(sampled), batch_size):
            batch = sampled[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(sampled) + batch_size - 1)//batch_size}...")
            batch_results = generate_queries_with_gemini(batch, api_key)
            eval_dataset.extend(batch_results)
            time.sleep(2) # avoid rate limits
    else:
        print("GEMINI_API_KEY not set. Using fallback heuristic generation...")
        for s in sampled:
            eval_dataset.extend(generate_fallback_query(s))
        
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(eval_dataset, f, indent=2)
        
    print(f"Generated {len(eval_dataset)} evaluation cases at {OUTPUT_FILE}")

if __name__ == "__main__":
    random.seed(42)
    main()
