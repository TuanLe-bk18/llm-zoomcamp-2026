import os
import json
from collections import defaultdict
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

class ElasticMCPSearch:
    def __init__(self, es_url=None, index_name="mcp-servers"):
        es_url = es_url or os.getenv("ES_URL", "http://localhost:9200")
        self.es = Elasticsearch(es_url)
        self.index_name = index_name
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def search_keyword(self, query, top_k=30):
        es_query = {"match": {"text": query}}
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



    def search_production(self, query, top_k=5, chunks_per_server=3):
        # 1. Vector Oversample (k=200, nc=500)
        query_vector = self.embedding_model.encode(query).tolist()
        knn_query = {
            "field": "text_vector",
            "query_vector": query_vector,
            "k": 200,
            "num_candidates": 500
        }
        res_vector = self.es.search(index=self.index_name, knn=knn_query, size=200)
        chunks_vector = self._parse_results(res_vector)
        
        # 2. Deduplicate into Top unique servers and keep top 2-3 chunks per server
        unique_servers = []
        server_chunks = defaultdict(list)
        
        for c in chunks_vector:
            sid = c['server_id']
            if sid not in unique_servers:
                if len(unique_servers) < top_k:
                    unique_servers.append(sid)
            
            if sid in unique_servers and len(server_chunks[sid]) < chunks_per_server:
                server_chunks[sid].append(c)
                
        final_candidates = []
        for sid in unique_servers[:top_k]:
            group = server_chunks[sid]
            aggregated_text = "\n\n".join([f"[{c.get('heading', '')}]\n{c.get('text', '')}" for c in group])
            source_url = group[0].get('source_url', f"https://github.com/{sid}")
            final_candidates.append({
                "server_id": sid,
                "text": aggregated_text,
                "source_url": source_url,
                "score": group[0].get('score', 0.0) # score of the best chunk
            })
            
        return final_candidates

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
    
    print(f"\n=== Query: '{query}' ===")
        
    print("\n--- Production Search (Unique Servers) ---")
    start = time.time()
    res = engine.search_production(query, top_k=3)
    print(f"Time: {time.time()-start:.3f}s")
    for r in res:
        print(f"[{r['server_id']}] (Score: {r['score']:.3f}): {r['text'][:150]}...\nSource: {r['source_url']}\n")
