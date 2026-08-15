import time
import os
import sys
from elasticsearch import Elasticsearch

# Add src to path
sys.path.append(os.path.dirname(__file__))
from ingestion.fetch_registry import fetch_registry
from ingestion.fetch_readmes import main as fetch_readmes
from retrieval.es_index import main as es_index

def wait_for_es():
    es_url = os.getenv("ES_URL", "http://localhost:9200")
    print(f"Waiting for Elasticsearch at {es_url}...")
    es = Elasticsearch(es_url)
    
    for _ in range(30):
        try:
            if es.ping():
                print("Elasticsearch is up and running!")
                return True
        except Exception:
            pass
        print("Waiting...")
        time.sleep(2)
        
    print("Failed to connect to Elasticsearch.")
    return False

def main():
    print("=== MCP Advisor Initialization ===")
    
    # 1. Wait for ES
    if not wait_for_es():
        sys.exit(1)
        
    # Check if data already exists to avoid re-fetching on every restart
    data_file = os.path.join(os.path.dirname(__file__), "..", "data", "documents.json")
    if os.path.exists(data_file):
        print("Data already exists. Skipping ingestion and jumping to indexing to ensure schema is correct.")
        print("--- Running Indexing ---")
        es_index()
        print("=== Initialization Complete ===")
        return

    # 2. Fetch Registry
    print("\\n--- Phase 1: Fetching Registry ---")
    try:
        fetch_registry()
    except Exception as e:
        print(f"Error fetching registry: {e}")
        sys.exit(1)
        
    # 3. Fetch READMEs
    print("\\n--- Phase 2: Fetching READMEs ---")
    try:
        fetch_readmes()
    except Exception as e:
        print(f"Error fetching readmes: {e}")
        sys.exit(1)
        
    # 4. Indexing
    print("\\n--- Phase 3: Chunking and Indexing ---")
    try:
        es_index()
    except Exception as e:
        print(f"Error during indexing: {e}")
        sys.exit(1)
        
    print("\\n=== Initialization Complete ===")

if __name__ == "__main__":
    main()
