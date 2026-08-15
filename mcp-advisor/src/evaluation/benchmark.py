import json
import sys
import os

# Add parent dir to path to import es_search
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'retrieval'))
from es_search import ElasticMCPSearch

EVAL_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "eval", "ground_truth.json")

def calculate_metrics(results_list, relevant_server_ids):
    hit1 = 0
    hit5 = 0
    mrr = 0.0
    
    # Extract unique server_ids from results while preserving order
    unique_results = []
    seen = set()
    for res in results_list:
        sid = res.get('server_id')
        if sid and sid not in seen:
            seen.add(sid)
            unique_results.append(sid)
            
    for i, sid in enumerate(unique_results):
        if sid in relevant_server_ids:
            if i == 0:
                hit1 = 1
            if i < 5:
                hit5 = 1
            mrr = 1.0 / (i + 1)
            break
            
    return hit1, hit5, mrr

def main():
    if not os.path.exists(EVAL_FILE):
        print(f"Error: {EVAL_FILE} not found. Run generate_eval_dataset.py first.")
        return
        
    with open(EVAL_FILE, 'r', encoding='utf-8') as f:
        queries = json.load(f)
        
    engine = ElasticMCPSearch()
    
    methods = [
        ("Keyword", engine.search_keyword),
        ("Vector", engine.search_vector),
        ("Hybrid", engine.search_hybrid),
        ("Hybrid+Rerank", engine.search_hybrid_rerank)
    ]
    
    print(f"Benchmarking {len(queries)} queries...")
    
    for method_name, search_func in methods:
        total_hit1 = 0
        total_hit5 = 0
        total_mrr = 0.0
        
        for q in queries:
            query_text = q['query']
            relevant_server_ids = q.get('relevant_server_ids', [])
            
            try:
                # search_hybrid_rerank already returns unique servers.
                # other methods return top chunks, so we fetch more (e.g. 15) to get 5 unique servers.
                results = search_func(query_text, top_k=15 if method_name != "Hybrid+Rerank" else 5)
            except Exception as e:
                print(f"Error during search: {e}")
                results = []
                
            hit1, hit5, mrr = calculate_metrics(results, relevant_server_ids)
            total_hit1 += hit1
            total_hit5 += hit5
            total_mrr += mrr
            
        n = len(queries)
        print(f"--- {method_name} ---")
        print(f"Hit@1: {total_hit1/n:.3f}")
        print(f"Hit@5: {total_hit5/n:.3f}")
        print(f"MRR:   {total_mrr/n:.3f}\\n")

if __name__ == "__main__":
    main()
