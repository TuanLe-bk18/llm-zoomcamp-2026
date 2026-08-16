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

    def search_rrf(self, query, top_k=5, k_rrf=60):
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
        
        # 2. BM25 Oversample (k=200)
        es_query = {"match": {"text": query}}
        res_bm25 = self.es.search(index=self.index_name, query=es_query, size=200)
        chunks_bm25 = self._parse_results(res_bm25)
        
        # Helper to deduplicate and keep top 50 unique servers
        def get_unique_servers(chunks, max_unique=50):
            unique = []
            seen = set()
            for c in chunks:
                sid = c['server_id']
                if sid not in seen:
                    seen.add(sid)
                    unique.append(sid)
                    if len(unique) >= max_unique:
                        break
            return unique
            
        vector_servers = get_unique_servers(chunks_vector)
        bm25_servers = get_unique_servers(chunks_bm25)
        
        # 3. RRF Fusion
        scores = {}
        for i, sid in enumerate(vector_servers):
            scores[sid] = scores.get(sid, 0) + 1.0 / (k_rrf + i + 1)
        for i, sid in enumerate(bm25_servers):
            scores[sid] = scores.get(sid, 0) + 1.0 / (k_rrf + i + 1)
            
        # Sort by RRF score
        sorted_sids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_k]
        
        if not sorted_sids:
            return []
            
        # We need text and source_url for the chosen servers.
        # We can query ES for these server_ids and aggregate their chunks.
        terms_query = {"terms": {"server_id": sorted_sids}}
        res_docs = self.es.search(index=self.index_name, query=terms_query, size=1000)
        
        server_groups = defaultdict(list)
        for hit in res_docs['hits']['hits']:
            source = hit['_source']
            server_groups[source.get("server_id")].append(source)
            
        final_candidates = []
        for sid in sorted_sids:
            group = server_groups.get(sid, [])
            if not group:
                continue
            aggregated_text = "\\n\\n".join([f"[{c.get('heading', '')}]\\n{c.get('text', '')}" for c in group])
            source_url = group[0].get('source_url', f"https://github.com/{sid}")
            final_candidates.append({
                "server_id": sid,
                "text": aggregated_text,
                "source_url": source_url,
                "score": scores[sid]
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
    
    print(f"\\n=== Query: '{query}' ===")
        
    print("\\n--- RRF Search (Unique Servers) ---")
    start = time.time()
    res = engine.search_rrf(query, top_k=3)
    print(f"Time: {time.time()-start:.3f}s")
    for r in res:
        print(f"[{r['server_id']}] (Score: {r['score']:.3f}): {r['text'][:150]}...\\nSource: {r['source_url']}\\n")
