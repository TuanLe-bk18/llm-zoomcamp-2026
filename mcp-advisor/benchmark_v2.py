import json
import sys
import os
import time
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'retrieval'))
from es_search import ElasticMCPSearch

EVAL_FILE = os.path.join("data", "eval", "validation_realistic_v1.json")

def calculate_metrics(results_list, relevant_server_ids):
    if not relevant_server_ids:
        return 0, 0, 0.0, 0.0
        
    hit1 = 0
    hit5 = 0
    mrr = 0.0
    
    unique_results = []
    seen = set()
    for res in results_list:
        sid = res.get('server_id')
        if sid and sid not in seen:
            seen.add(sid)
            unique_results.append(sid)
            
    found_count_in_5 = 0
    for i, sid in enumerate(unique_results):
        if sid in relevant_server_ids:
            if i == 0:
                hit1 = 1
            if i < 5:
                hit5 = 1
                found_count_in_5 += 1
            if mrr == 0.0:
                mrr = 1.0 / (i + 1)
                
    recall5 = found_count_in_5 / len(relevant_server_ids)
    
    return hit1, hit5, mrr, recall5

def main():
    with open(EVAL_FILE, 'r', encoding='utf-8') as f:
        val_data = json.load(f)
        
    queries = val_data["queries"]
    
    engine = ElasticMCPSearch()
    
    methods = [
        ("BM25 / Keyword", engine.search_keyword),
        ("Dense Vector", engine.search_vector),
        ("Hybrid (Vector + Keyword)", engine.search_hybrid),
        ("RRF + Oversampling", engine.search_rrf)
    ]
    
    print(f"Benchmarking {len(queries)} queries...")
    
    for method_name, search_func in methods:
        total_hit1 = 0
        total_hit5 = 0
        total_mrr = 0.0
        total_recall5 = 0.0
        
        latencies = []
        
        breakdown = {
            "simple_intent": {"hit1": 0, "hit5": 0, "mrr": 0.0, "recall5": 0.0, "count": 0},
            "constraint_heavy": {"hit1": 0, "hit5": 0, "mrr": 0.0, "recall5": 0.0, "count": 0},
            "ambiguous_realistic": {"hit1": 0, "hit5": 0, "mrr": 0.0, "recall5": 0.0, "count": 0}
        }
        
        no_relevant_count = 0
        returned_for_no_relevant = []
        
        valid_queries = 0
        
        for q in queries:
            query_text = q['query']
            relevant_server_ids = q.get('relevant_server_ids', [])
            intent_category = q.get('query_type', 'simple_intent')
            is_no_relevant = q.get('no_relevant_server', False)
            
            t0 = time.time()
            try:
                results = search_func(query_text, top_k=30 if method_name != "Hybrid+CrossEncoder" else 5)
            except Exception as e:
                print(f"Error during search: {e}")
                results = []
            t1 = time.time()
            
            latencies.append(t1 - t0)
            
            if is_no_relevant:
                no_relevant_count += 1
                returned_for_no_relevant.append(len(results))
            else:
                hit1, hit5, mrr, recall5 = calculate_metrics(results, relevant_server_ids)
                total_hit1 += hit1
                total_hit5 += hit5
                total_mrr += mrr
                total_recall5 += recall5
                valid_queries += 1
                
                cat = breakdown[intent_category]
                cat["hit1"] += hit1
                cat["hit5"] += hit5
                cat["mrr"] += mrr
                cat["recall5"] += recall5
                cat["count"] += 1
                
        n = valid_queries
        p50 = np.percentile(latencies, 50) * 1000
        p95 = np.percentile(latencies, 95) * 1000
        avg_ret_no_rel = np.mean(returned_for_no_relevant) if no_relevant_count > 0 else 0
        
        print(f"--- {method_name} ---")
        print(f"Overall (N={n}):")
        print(f"Hit@1:    {total_hit1/n:.3f}")
        print(f"Hit@5:    {total_hit5/n:.3f}")
        print(f"MRR:      {total_mrr/n:.3f}")
        print(f"Recall@5: {total_recall5/n:.3f}")
        print(f"Latency:  p50={p50:.1f}ms, p95={p95:.1f}ms")
        if no_relevant_count > 0:
            print(f"No Relevant Queries (N={no_relevant_count}): avg results returned = {avg_ret_no_rel:.1f}")
            
        print("Breakdown:")
        for cat_name, cat_stats in breakdown.items():
            if cat_stats["count"] > 0:
                cn = cat_stats["count"]
                print(f"  {cat_name} (N={cn}): Hit@1={cat_stats['hit1']/cn:.3f}, Hit@5={cat_stats['hit5']/cn:.3f}, MRR={cat_stats['mrr']/cn:.3f}, Recall@5={cat_stats['recall5']/cn:.3f}")
        print("\\n")
        
if __name__ == "__main__":
    main()
