import json
import os
import time
from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer

ES_URL = "http://localhost:9200"
INDEX_NAME = "mcp-servers"
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "documents.json")

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

    # Delete index if exists
    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)
        print(f"Deleted existing index: {INDEX_NAME}")

    # Create index with dense_vector mapping
    # all-MiniLM-L6-v2 outputs 384 dimensions
    mapping = {
        "mappings": {
            "properties": {
                "owner": {"type": "keyword"},
                "repo": {"type": "keyword"},
                "text": {"type": "text"},
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
    
    for doc_id, doc in enumerate(documents):
        owner = doc.get('owner', 'unknown')
        repo = doc.get('repo', 'unknown')
        readme_text = doc.get('readme', '')
        
        paragraphs = [p.strip() for p in readme_text.split('\n\n') if len(p.strip()) > 50]
        
        if not paragraphs:
            if readme_text.strip():
                paragraphs = [readme_text.strip()[:1000]]
            else:
                paragraphs = [doc.get('description', '')]
        
        # Limit to 10 chunks per server
        for chunk_id, p in enumerate(paragraphs[:10]):
            embedding = model.encode(p).tolist()
            
            action = {
                "_index": INDEX_NAME,
                "_source": {
                    "owner": owner,
                    "repo": repo,
                    "text": p,
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
