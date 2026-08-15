import os
import json
from collections import defaultdict
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer, CrossEncoder

class ElasticMCPSearch:
    def __init__(self, es_url=None, index_name="mcp-servers"):
        es_url = es_url or os.getenv("ES_URL", "http://localhost:9200")
        self.es = Elasticsearch(es_url)
        self.index_name = index_name
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    def search_keyword(self, query, top_k=30):
        es_query = {
            "match": {
                "text": query
            }
        }
        res = self.es.search(index=self.index_name, query=es_query, size=top_k)
        return self._parse_results(res)

    def search_vector(self, query, top_k=30):
        query_vector = self.embedding_model.encode(query).tolist()
        knn_query = {
            "field": "text_vector",
            "query_vector": query_vector,
            "k": top_k,
            "num_candidates": 100
        }
        res = self.es.search(index=self.index_name, knn=knn_query, size=top_k)
        return self._parse_results(res)

    def search_hybrid(self, query, top_k=30):
        query_vector = self.embedding_model.encode(query).tolist()
        
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
        # Retrieve top 30 chunks from hybrid
        chunks = self.search_hybrid(query, top_k=30)
        
        # Group by server_id
        server_groups = defaultdict(list)
        for chunk in chunks:
            server_id = chunk['server_id']
            server_groups[server_id].append(chunk)
            
        candidates = []
        for server_id, group in server_groups.items():
            # Aggregate text (heading + text)
            aggregated_text = "\\n\\n".join([f"[{c['heading']}]\\n{c['text']}" for c in group])
            
            # Use the first chunk's source_url
            source_url = group[0].get('source_url', f"https://github.com/{server_id}")
            
            candidates.append({
                "server_id": server_id,
                "text": aggregated_text,
                "source_url": source_url,
                "original_chunks": group
            })
            
        # Prepare pairs for cross-encoder
        pairs = [[query, c['text']] for c in candidates]
        
        # Score pairs
        if not pairs:
            return []
            
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
                "server_id": source.get("server_id", "unknown"),
                "heading": source.get("heading", "General"),
                "text": source.get("text", ""),
                "source_url": source.get("source_url", ""),
                "score": hit['_score']
            })
        return results

if __name__ == "__main__":
    import time
    engine = ElasticMCPSearch()
    query = "database connection PostgreSQL"
    
    print(f"\\n=== Query: '{query}' ===")
        
    print("\\n--- Hybrid + Reranking Search (Unique Servers) ---")
    start = time.time()
    res = engine.search_hybrid_rerank(query, top_k=3)
    print(f"Time: {time.time()-start:.3f}s")
    for r in res:
        print(f"[{r['server_id']}] (Score: {r['score']:.3f}): {r['text'][:150]}...\\nSource: {r['source_url']}\\n")
