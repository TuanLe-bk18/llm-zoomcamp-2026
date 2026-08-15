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

def check_index_exists():
    es_url = os.getenv("ES_URL", "http://localhost:9200")
    es = Elasticsearch(es_url)
    return es.indices.exists(index="mcp-servers")

def main():
    print("=== MCP Advisor Initialization ===")
    
    # Check for refresh mode
    refresh_mode = "--refresh" in sys.argv
    
    # 1. Wait for ES
    if not wait_for_es():
        sys.exit(1)
        
    if not refresh_mode:
        if check_index_exists():
            print("Elasticsearch index 'mcp-servers' already exists. Fast boot mode: skipping ingestion and indexing.")
            print("=== Initialization Complete ===")
            return
        
        data_file = os.path.join(os.path.dirname(__file__), "..", "data", "documents.json")
        if os.path.exists(data_file):
            print("Data file exists but index is missing. Running Indexing only...")
            try:
                es_index()
            except Exception as e:
                print(f"Error during indexing: {e}")
                sys.exit(1)
            print("=== Initialization Complete ===")
            return
            
    print("Refresh mode or missing data. Running full ingestion pipeline...")

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
