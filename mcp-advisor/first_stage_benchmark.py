import json
import sys
import os
import time
import numpy as np
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer, CrossEncoder

EVAL_FILE = os.path.join("data", "eval", "validation_realistic_v1.json")
ES_URL = os.getenv("ES_URL", "http://localhost:9200")
INDEX_NAME = "mcp-servers"

class Benchmarker:
    def __init__(self):
        self.es = Elasticsearch(ES_URL)
        print("Loading embedding model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Loading cross encoder...")
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
    def _parse_results(self, es_res):
        results = []
        for hit in es_res['hits']['hits']:
            source = hit['_source']
            results.append({
                "server_id": source.get("server_id", "unknown"),
                "score": hit['_score']
            })
        return results
        
    def _deduplicate(self, chunks, max_unique=50):
        unique_servers = []
        seen = set()
        for c in chunks:
            sid = c['server_id']
            if sid not in seen:
                seen.add(sid)
                unique_results_entry = {"server_id": sid, "score": c['score']}
                unique_servers.append(unique_results_entry)
                if len(unique_servers) >= max_unique:
                    break
        return unique_servers

    def search_keyword(self, query, top_k=30):
        es_query = {"match": {"text": query}}
        res = self.es.search(index=INDEX_NAME, query=es_query, size=top_k)
        return self._parse_results(res)

    def search_vector(self, query, top_k=30, num_candidates=100):
        query_vector = self.model.encode(query).tolist()
        knn_query = {
            "field": "text_vector",
            "query_vector": query_vector,
            "k": top_k,
            "num_candidates": num_candidates
        }
        res = self.es.search(index=INDEX_NAME, knn=knn_query, size=top_k)
        return self._parse_results(res)

    def search_hybrid(self, query, top_k=30, num_candidates=100):
        query_vector = self.model.encode(query).tolist()
        knn_query = {
            "field": "text_vector",
            "query_vector": query_vector,
            "k": top_k,
            "num_candidates": num_candidates,
            "boost": 0.5
        }
        match_query = {
            "match": {
                "text": {
                    "query": query,
                    "boost": 0.5
                }
            }
        }
        res = self.es.search(index=INDEX_NAME, knn=knn_query, query=match_query, size=top_k)
        return self._parse_results(res)

def get_metrics(results, relevant_server_ids):
    # results is a list of dict with 'server_id'
    
    unique_servers = []
    seen = set()
    for r in results:
        sid = r['server_id']
        if sid not in seen:
            seen.add(sid)
            unique_servers.append(sid)
            
    # Candidate Recall
    recall_10 = 1 if any(s in unique_servers[:10] for s in relevant_server_ids) else 0
    recall_30 = 1 if any(s in unique_servers[:30] for s in relevant_server_ids) else 0
    recall_50 = 1 if any(s in unique_servers[:50] for s in relevant_server_ids) else 0
    
    # Hit/MRR/Recall on Top 5
    hit1 = 1 if any(s in unique_servers[:1] for s in relevant_server_ids) else 0
    hit5 = 1 if any(s in unique_servers[:5] for s in relevant_server_ids) else 0
    
    mrr5 = 0.0
    for i, sid in enumerate(unique_servers[:5]):
        if sid in relevant_server_ids:
            mrr5 = 1.0 / (i + 1)
            break
            
    found_count_in_5 = sum(1 for s in unique_servers[:5] if s in relevant_server_ids)
    recall5 = found_count_in_5 / len(relevant_server_ids) if relevant_server_ids else 0.0
    
    return {
        "num_unique": len(unique_servers),
        "cand_rec_10": recall_10,
        "cand_rec_30": recall_30,
        "cand_rec_50": recall_50,
        "hit1": hit1,
        "hit5": hit5,
        "mrr5": mrr5,
        "recall5": recall5
    }

def merge_rrf(list1, list2, k_rrf=60):
    scores = {}
    for i, doc in enumerate(list1):
        sid = doc['server_id']
        scores[sid] = scores.get(sid, 0) + 1.0 / (k_rrf + i + 1)
        
    for i, doc in enumerate(list2):
        sid = doc['server_id']
        scores[sid] = scores.get(sid, 0) + 1.0 / (k_rrf + i + 1)
        
    # Sort
    sorted_sids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return [{"server_id": sid, "score": scores[sid]} for sid in sorted_sids]

def main():
    with open(EVAL_FILE, 'r', encoding='utf-8') as f:
        val_data = json.load(f)
        
    queries = val_data["queries"]
    benchmarker = Benchmarker()
    
    # Define variants
    # A variant is a function that takes (benchmarker, query_text) and returns a list of result dicts
    
    def var1_baseline_hybrid(bm, q):
        chunks = bm.search_hybrid(q, top_k=30, num_candidates=100)
        return bm._deduplicate(chunks, max_unique=30)
        
    def var2_vector_oversample(bm, q):
        chunks = bm.search_vector(q, top_k=200, num_candidates=500)
        return bm._deduplicate(chunks, max_unique=50)
        
    def var3_bm25_oversample(bm, q):
        chunks = bm.search_keyword(q, top_k=200)
        return bm._deduplicate(chunks, max_unique=50)
        
    def var4_rrf_fusion(bm, q):
        list_vector = var2_vector_oversample(bm, q)
        list_bm25 = var3_bm25_oversample(bm, q)
        return merge_rrf(list_vector, list_bm25, k_rrf=60)[:50]
        
    def var5_vector_nc100(bm, q):
        chunks = bm.search_vector(q, top_k=200, num_candidates=100)
        return bm._deduplicate(chunks, max_unique=50)
        
    def var6_v4_rrf_plus_ce(bm, q):
        v4_results = var4_rrf_fusion(bm, q)
        if not v4_results: return []
        
        # We need the text for each candidate to run CE.
        # But v4_results only has 'server_id' and 'score'.
        # Since we just want the benchmark, we can fetch the text from ES quickly or just run the CE logic.
        # This might be tricky without modifying es_search or fetching all texts.
        # Actually, let's write a small helper to get text for CE.
        es_query = {"terms": {"server_id": [r["server_id"] for r in v4_results]}}
        res = bm.es.search(index=INDEX_NAME, query=es_query, size=1000)
        
        server_texts = {}
        for hit in res['hits']['hits']:
            src = hit['_source']
            sid = src.get("server_id")
            if sid not in server_texts: server_texts[sid] = []
            server_texts[sid].append(f"[{src.get('heading', '')}]\\n{src.get('text', '')}")
            
        candidates = []
        for r in v4_results:
            sid = r["server_id"]
            agg_text = "\\n\\n".join(server_texts.get(sid, []))
            candidates.append({"server_id": sid, "text": agg_text})
            
        pairs = [[q, c['text']] for c in candidates]
        if not pairs: return v4_results
        
        # cross_encoder is in ElasticMCPSearch. We can import it or initialize it.
        # It's better to just use engine.cross_encoder
        ce = bm.cross_encoder
        scores = ce.predict(pairs)
        for i, score in enumerate(scores):
            candidates[i]['score'] = float(score)
            
        sorted_cands = sorted(candidates, key=lambda x: x['score'], reverse=True)
        return sorted_cands

    variants = {
        "V4: RRF Fusion (V2 + V3)": var4_rrf_fusion,
        "V6: V4 RRF + CrossEncoder": var6_v4_rrf_plus_ce
    }
    
    for name, func in variants.items():
        print(f"\\n{'='*50}\\nRunning {name}\\n{'='*50}")
        
        totals = {"cand_rec_10": 0, "cand_rec_30": 0, "cand_rec_50": 0, 
                  "hit1": 0, "hit5": 0, "mrr5": 0.0, "recall5": 0.0}
        unique_counts = []
        latencies = []
        valid_queries = 0
        
        breakdown = {
            "simple_intent": {k: 0.0 for k in totals.keys()},
            "constraint_heavy": {k: 0.0 for k in totals.keys()},
            "ambiguous_realistic": {k: 0.0 for k in totals.keys()}
        }
        for k in breakdown:
            breakdown[k]["count"] = 0
            
        for q in queries:
            if q.get('no_relevant_server', False):
                continue
                
            query_text = q['query']
            relevant_server_ids = q.get('relevant_server_ids', [])
            qtype = q.get('query_type', 'simple_intent')
            
            t0 = time.time()
            try:
                results = func(benchmarker, query_text)
            except Exception as e:
                print(f"Error on query {q['query_id']}: {e}")
                results = []
            t1 = time.time()
            latencies.append(t1 - t0)
            
            valid_queries += 1
            metrics = get_metrics(results, relevant_server_ids)
            
            unique_counts.append(metrics["num_unique"])
            for k in totals:
                totals[k] += metrics[k]
                
            breakdown[qtype]["count"] += 1
            for k in totals:
                breakdown[qtype][k] += metrics[k]
                
        n = valid_queries
        print(f"Overall (N={n}):")
        print(f"Avg Unique Servers: {np.mean(unique_counts):.1f} (p50: {np.percentile(unique_counts, 50):.0f}, p95: {np.percentile(unique_counts, 95):.0f})")
        print(f"Candidate Recall @10: {totals['cand_rec_10']/n:.3f} | @30: {totals['cand_rec_30']/n:.3f} | @50: {totals['cand_rec_50']/n:.3f}")
        print(f"Hit@1: {totals['hit1']/n:.3f} | Hit@5: {totals['hit5']/n:.3f} | MRR@5: {totals['mrr5']/n:.3f} | Recall@5: {totals['recall5']/n:.3f}")
        print(f"Latency: p50={np.percentile(latencies, 50)*1000:.1f}ms, p95={np.percentile(latencies, 95)*1000:.1f}ms")
        
        print("\\nBreakdown:")
        for k, bd in breakdown.items():
            cnt = bd["count"]
            if cnt > 0:
                print(f"  {k} (N={cnt}): CR@30={bd['cand_rec_30']/cnt:.3f}, Hit@1={bd['hit1']/cnt:.3f}, Hit@5={bd['hit5']/cnt:.3f}, MRR@5={bd['mrr5']/cnt:.3f}")
                
if __name__ == "__main__":
    main()
