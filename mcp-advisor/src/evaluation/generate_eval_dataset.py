import json
import os
import random
import time
import re
from google import genai
from google.genai import types

INPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "documents.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "eval", "ground_truth.json")

def redact_text(text, server_id):
    if not text or not server_id:
        return text
    
    owner, repo = server_id.split('/') if '/' in server_id else ("", server_id)
    redacted = text

    # Remove github urls
    redacted = re.sub(r'https?://github\.com/[\w.-]+/[\w.-]+', '[REDACTED_URL]', redacted, flags=re.IGNORECASE)
    
    # Remove npx commands
    redacted = re.sub(r'npx\s+-y\s+@[\w.-]+/[\w.-]+', 'npx -y [REDACTED_PACKAGE]', redacted, flags=re.IGNORECASE)
    redacted = re.sub(r'npx\s+@[\w.-]+/[\w.-]+', 'npx [REDACTED_PACKAGE]', redacted, flags=re.IGNORECASE)
    
    # Remove direct occurrences
    redacted = redacted.replace(server_id, "[REDACTED_SERVER]")
    if repo:
        redacted = redacted.replace(repo, "[REDACTED_REPO]")
    if owner:
        redacted = redacted.replace(owner, "[REDACTED_OWNER]")
    
    return redacted

def generate_query_for_server(server_doc, api_key, max_retries=3):
    client = genai.Client(api_key=api_key)
    server_id = server_doc.get("server_id", "")
    owner, repo = server_id.split('/') if '/' in server_id else ("", server_id)
    raw_evidence = server_doc.get("readme", "")[:1500] # Provide ample context
    
    redacted_evidence = redact_text(raw_evidence, server_id)
    
    prompt = f"""
You are generating an evaluation dataset for a Model Context Protocol (MCP) recommendation system.
Generate ONE realistic user query that a developer might ask when looking for a tool with these capabilities.

CRITICAL RULES:
1. The query MUST NOT contain the real server name, repository name, or owner name. You MUST NOT leak any specific identifiers.
2. The query should describe capabilities, use cases, or problems the developer is trying to solve.
3. Make the query realistic. Sometimes developers mention constraints like "must be local", "needs authentication", "must be read-only".
4. ONLY use capabilities explicitly supported by the provided README excerpt. Do not hallucinate features.
5. Provide the output as JSON with exactly these keys: "query", "constraints", "rationale".

--- SERVER_001 README Excerpt ---
{redacted_evidence}
"""

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-3.1-flash-lite',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7 + (attempt * 0.1) # increase temp on retry
                )
            )
            
            result = json.loads(response.text)
            query = result.get("query", "").lower()
            
            # Validation: Strict leakage check
            if repo.lower() in query or (owner and owner.lower() in query):
                print(f"  [Retry] Leakage detected in query: {query}")
                continue # Try again
                
            return {
                "query": result.get("query", ""),
                "relevant_server_ids": [server_id],
                "constraints": result.get("constraints", []),
                "rationale": result.get("rationale", ""),
                "source_chunk_id": server_id,
                "supporting_evidence": raw_evidence
            }
            
        except Exception as e:
            err_str = str(e)
            print(f"  [Retry] Error generating for {server_id}: {err_str}")
            if "429" in err_str:
                print("  [Rate Limit] Sleeping for 65 seconds...")
                time.sleep(65)
            else:
                time.sleep(2)
            
    print(f"Failed to generate valid query for {server_id} after {max_retries} attempts.")
    return None

def generate_fallback_query(server):
    server_id = server.get('server_id', '')
    text = server.get('text', '')[:1000]
    
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
        
    return {
        "query": random.choice(templates),
        "relevant_server_ids": [server_id],
        "constraints": constraints,
        "rationale": f"The user is looking for {topics} capabilities. The {server_id} server provides exactly this.",
        "source_chunk_id": server.get("id", ""),
        "supporting_evidence": text
    }

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    api_key = os.getenv("GEMINI_API_KEY")

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        documents = json.load(f)
        
    # Group by server_id to get one chunk per server (preferably the first chunk which has the main README intro)
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
        for i, server in enumerate(sampled):
            print(f"[{i+1}/{len(sampled)}] Generating query for {server['server_id']}...")
            result = generate_query_for_server(server, api_key)
            if result:
                eval_dataset.append(result)
            time.sleep(1)
    else:
        print("GEMINI_API_KEY not set. Using fallback heuristic generation...")
        for s in sampled:
            eval_dataset.append(generate_fallback_query(s))
        
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(eval_dataset, f, indent=2)
        
    print(f"Generated {len(eval_dataset)} evaluation cases at {OUTPUT_FILE}")

if __name__ == "__main__":
    random.seed(42)
    main()
