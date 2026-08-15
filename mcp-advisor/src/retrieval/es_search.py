import os
import json
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer, CrossEncoder

class ElasticMCPSearch:
    def __init__(self, es_url="http://localhost:9200", index_name="mcp-servers"):
        self.es = Elasticsearch(es_url)
        self.index_name = index_name
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    def search_keyword(self, query, top_k=5):
        es_query = {
            "match": {
                "text": query
            }
        }
        res = self.es.search(index=self.index_name, query=es_query, size=top_k)
        return self._parse_results(res)

    def search_vector(self, query, top_k=5):
        query_vector = self.embedding_model.encode(query).tolist()
        knn_query = {
            "field": "text_vector",
            "query_vector": query_vector,
            "k": top_k,
            "num_candidates": 100
        }
        res = self.es.search(index=self.index_name, knn=knn_query, size=top_k)
        return self._parse_results(res)

    def search_hybrid(self, query, top_k=5):
        query_vector = self.embedding_model.encode(query).tolist()
        
        # Using Reciprocal Rank Fusion (RRF) or simple linear combination
        # For simplicity in ES 8 without RRF license, we combine score via bool query or script score.
        # But we can also use knn combined with match. ES normalizes and combines them automatically.
        knn_query = {
            "field": "text_vector",
            "query_vector": query_vector,
            "k": top_k,
            "num_candidates": 100,
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
        
        res = self.es.search(index=self.index_name, knn=knn_query, query=match_query, size=top_k)
        return self._parse_results(res)

    def search_hybrid_rerank(self, query, top_k=5):
        # Retrieve top 20 candidates from hybrid
        candidates = self.search_hybrid(query, top_k=20)
        
        # Prepare pairs for cross-encoder
        pairs = [[query, c['text']] for c in candidates]
        
        # Score pairs
        rerank_scores = self.cross_encoder.predict(pairs)
        
        for i, score in enumerate(rerank_scores):
            candidates[i]['score'] = float(score)
            
        # Sort by rerank score
        candidates = sorted(candidates, key=lambda x: x['score'], reverse=True)
        return candidates[:top_k]

    def _parse_results(self, es_res):
        results = []
        for hit in es_res['hits']['hits']:
            source = hit['_source']
            results.append({
                "owner": source.get("owner"),
                "repo": source.get("repo"),
                "text": source.get("text"),
                "score": hit['_score']
            })
        return results

if __name__ == "__main__":
    import time
    engine = ElasticMCPSearch()
    query = "database connection PostgreSQL"
    
    print(f"\\n=== Query: '{query}' ===")
    
    print("\\n--- Keyword Search ---")
    start = time.time()
    res = engine.search_keyword(query, top_k=3)
    print(f"Time: {time.time()-start:.3f}s")
    for r in res:
        print(f"[{r['owner']}/{r['repo']}] (Score: {r['score']:.3f}): {r['text'][:100]}...")

    print("\\n--- Vector Search ---")
    start = time.time()
    res = engine.search_vector(query, top_k=3)
    print(f"Time: {time.time()-start:.3f}s")
    for r in res:
        print(f"[{r['owner']}/{r['repo']}] (Score: {r['score']:.3f}): {r['text'][:100]}...")

    print("\\n--- Hybrid Search ---")
    start = time.time()
    res = engine.search_hybrid(query, top_k=3)
    print(f"Time: {time.time()-start:.3f}s")
    for r in res:
        print(f"[{r['owner']}/{r['repo']}] (Score: {r['score']:.3f}): {r['text'][:100]}...")
        
    print("\\n--- Hybrid + Reranking Search ---")
    start = time.time()
    res = engine.search_hybrid_rerank(query, top_k=3)
    print(f"Time: {time.time()-start:.3f}s")
    for r in res:
        print(f"[{r['owner']}/{r['repo']}] (Score: {r['score']:.3f}): {r['text'][:100]}...")
