import json
import sys
import os

# Add parent dir to path to import es_search
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'retrieval'))
from es_search import ElasticMCPSearch

EVAL_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "eval", "ground_truth.json")

def calculate_metrics(results_list, expected_owner, expected_repo):
    hit1 = 0
    hit5 = 0
    mrr = 0.0
    
    for i, res in enumerate(results_list):
        # We consider it a hit if the owner/repo matches
        if res.get('owner') == expected_owner and res.get('repo') == expected_repo:
            if i == 0:
                hit1 = 1
            if i < 5:
                hit5 = 1
            mrr = 1.0 / (i + 1)
            break
            
    return hit1, hit5, mrr

def main():
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
            expected_owner = q['expected_owner']
            expected_repo = q['expected_repo']
            
            try:
                results = search_func(query_text, top_k=5)
            except Exception as e:
                print(f"Error during search: {e}")
                results = []
                
            hit1, hit5, mrr = calculate_metrics(results, expected_owner, expected_repo)
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
