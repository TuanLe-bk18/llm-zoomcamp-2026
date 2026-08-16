import json
import os
import sys
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
    chunk_index = 0
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
            
        heading = "General"
        text = section
        
        match = re.match(r'^(#+)\s+(.*)', section)
        if match:
            heading = match.group(2).strip()
            
        if len(text) < 50:
            continue
            
        max_chunk_size = 1000
        overlap = 150
        
        if len(text) <= max_chunk_size:
            chunks.append({
                "chunk_id": f"{server_id}_{chunk_index}",
                "server_id": server_id,
                "heading": heading[:200],
                "text": text,
                "source_url": source_url
            })
            chunk_index += 1
            continue
            
        # Split long sections by paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        current_chunk = ""
        
        for p in paragraphs:
            # If current chunk is getting too big, flush it
            if len(current_chunk) + len(p) > max_chunk_size and len(current_chunk) > 0:
                chunks.append({
                    "chunk_id": f"{server_id}_{chunk_index}",
                    "server_id": server_id,
                    "heading": heading[:200],
                    "text": current_chunk.strip(),
                    "source_url": source_url
                })
                chunk_index += 1
                current_chunk = current_chunk[-overlap:] + "\n\n" + p
            else:
                current_chunk = current_chunk + "\n\n" + p if current_chunk else p
                
            # If the paragraph itself is huge, split by characters
            while len(current_chunk) > max_chunk_size + 200:
                chunks.append({
                    "chunk_id": f"{server_id}_{chunk_index}",
                    "server_id": server_id,
                    "heading": heading[:200],
                    "text": current_chunk[:max_chunk_size].strip(),
                    "source_url": source_url
                })
                chunk_index += 1
                current_chunk = current_chunk[max_chunk_size - overlap:]
                
        if len(current_chunk.strip()) >= 50:
            chunks.append({
                "chunk_id": f"{server_id}_{chunk_index}",
                "server_id": server_id,
                "heading": heading[:200],
                "text": current_chunk.strip(),
                "source_url": source_url
            })
            chunk_index += 1
            
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
        
        if not chunks:
            text = doc.get('description', '')
            if text:
                chunks = [{"chunk_id": f"{server_id}_0", "server_id": server_id, "heading": "General", "text": text, "source_url": source_url}]
                
        for chunk in chunks:
            description = doc.get("description", "")
            enriched_text = f"Server: {chunk['server_id']}\nDescription: {description}\nSection: {chunk['heading']}\n\n{chunk['text']}"
            
            embedding = model.encode(enriched_text).tolist()
            
            action = {
                "_index": INDEX_NAME,
                "_id": chunk["chunk_id"],
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

def smoke_test():
    test_content = """# Short section
This is fine.

# Long section
""" + "A" * 800 + "\n\n" + "B" * 800 + """

# Huge paragraph
""" + "C" * 2500

    print("--- SMOKE TEST ---")
    chunks = chunk_markdown_by_headings(test_content, "test/repo", "http://test")
    for i, c in enumerate(chunks):
        print(f"Chunk {i}: {len(c['text'])} chars, starts with {c['text'][:20]}")
    print("------------------\n")

if __name__ == "__main__":
    if "--test" in sys.argv:
        smoke_test()
    else:
        main()
