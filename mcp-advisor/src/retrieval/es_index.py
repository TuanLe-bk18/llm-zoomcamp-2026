import json
import os
import time
import re
from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer

ES_URL = os.getenv("ES_URL", "http://localhost:9200")
INDEX_NAME = "mcp-servers"
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "documents.json")

def chunk_markdown_by_headings(content, server_id, source_url):
    sections = re.split(r'\n(?=#+ )', "\n" + content)
    chunks = []
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
            
        heading = "General"
        text = section
        
        match = re.match(r'^(#+)\s+(.*)', section)
        if match:
            heading = match.group(2).strip()
            
        if len(text) > 4000:
            text = text[:4000] # naive truncation to fit embedding models
            
        if len(text) < 50:
            continue
            
        chunks.append({
            "server_id": server_id,
            "heading": heading[:200],
            "text": text,
            "source_url": source_url
        })
        
    return chunks

def main():
    print(f"Connecting to Elasticsearch at {ES_URL}...")
    es = Elasticsearch(ES_URL)
    
    # Wait for ES to be up
    for _ in range(30):
        try:
            if es.ping():
                print("Connected to Elasticsearch!")
                break
        except Exception:
            pass
        print("Waiting for Elasticsearch...")
        time.sleep(2)
        
    if not es.ping():
        print("Failed to connect to Elasticsearch.")
        return

    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)
        print(f"Deleted existing index: {INDEX_NAME}")

    mapping = {
        "mappings": {
            "properties": {
                "server_id": {"type": "keyword"},
                "heading": {"type": "keyword"},
                "text": {"type": "text"},
                "source_url": {"type": "keyword"},
                "text_vector": {
                    "type": "dense_vector",
                    "dims": 384,
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    }
    es.indices.create(index=INDEX_NAME, body=mapping)
    print(f"Created index: {INDEX_NAME}")

    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print(f"Loading data from {DATA_PATH}...")
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        documents = json.load(f)

    print("Chunking and generating embeddings (this might take a minute)...")
    actions = []
    
    for doc in documents:
        server_id = doc.get('server_id')
        if not server_id:
            # Fallback for old schema
            owner = doc.get('owner', 'unknown')
            repo = doc.get('repo', 'unknown')
            server_id = f"{owner}/{repo}"
            
        source_url = doc.get('readme_url', f"https://github.com/{server_id}")
        readme_text = doc.get('readme', '')
        
        chunks = chunk_markdown_by_headings(readme_text, server_id, source_url)
        
        # Fallback if no chunks
        if not chunks:
            text = doc.get('description', '')
            if text:
                chunks = [{"server_id": server_id, "heading": "General", "text": text, "source_url": source_url}]
                
        for chunk in chunks:
            embedding = model.encode(chunk["text"]).tolist()
            
            action = {
                "_index": INDEX_NAME,
                "_source": {
                    "server_id": chunk["server_id"],
                    "heading": chunk["heading"],
                    "text": chunk["text"],
                    "source_url": chunk["source_url"],
                    "text_vector": embedding
                }
            }
            actions.append(action)

    print(f"Prepared {len(actions)} chunks for indexing.")
    print("Bulk indexing into Elasticsearch...")
    helpers.bulk(es, actions)
    print("Indexing complete!")

if __name__ == "__main__":
    main()
