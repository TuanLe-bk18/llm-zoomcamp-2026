import json
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, CrossEncoder

class MCPSearchEngine:
    def __init__(self, data_path=None):
        if data_path is None:
            self.data_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "documents.json")
        else:
            self.data_path = data_path
        self.documents = []
        self.chunks = []
        
        # Load embedding model
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Load cross encoder for reranking
        print("Loading cross encoder...")
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=10000)
        
        self.tfidf_matrix = None
        self.dense_matrix = None

    def load_and_chunk(self):
        print(f"Loading data from {self.data_path}...")
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.documents = json.load(f)
            
        print(f"Loaded {len(self.documents)} servers.")
        
        # Simple chunking: chunk by paragraphs (split by double newline)
        for doc_id, doc in enumerate(self.documents):
            readme_text = doc.get('readme', '')
            paragraphs = [p.strip() for p in readme_text.split('\n\n') if len(p.strip()) > 50]
            
            # If no paragraphs > 50 chars, just take the whole thing as one chunk
            if not paragraphs:
                if readme_text.strip():
                    paragraphs = [readme_text.strip()[:1000]] # Limit huge chunks
                else:
                    paragraphs = [doc.get('description', '')]
            
            # Limit to top 10 chunks per server to avoid massive memory usage for giant readmes
            for chunk_id, p in enumerate(paragraphs[:10]):
                self.chunks.append({
                    "doc_id": doc_id,
                    "owner": doc.get('owner'),
                    "repo": doc.get('repo'),
                    "text": p
                })
        print(f"Created {len(self.chunks)} text chunks.")

    def build_index(self):
        texts = [c['text'] for c in self.chunks]
        print("Building TF-IDF matrix...")
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        
        print("Building dense embeddings...")
        self.dense_matrix = self.embedding_model.encode(texts, show_progress_bar=True)
        
        print("Indexing complete.")

    def search_keyword(self, query, top_k=5):
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        return self._get_top_results(scores, top_k)

    def search_vector(self, query, top_k=5):
        query_vec = self.embedding_model.encode([query])
        scores = cosine_similarity(query_vec, self.dense_matrix).flatten()
        return self._get_top_results(scores, top_k)

    def search_hybrid(self, query, top_k=5, alpha=0.5):
        # alpha = 1 means 100% vector, alpha = 0 means 100% keyword
        query_vec_kw = self.vectorizer.transform([query])
        scores_kw = cosine_similarity(query_vec_kw, self.tfidf_matrix).flatten()
        
        query_vec_dense = self.embedding_model.encode([query])
        scores_dense = cosine_similarity(query_vec_dense, self.dense_matrix).flatten()
        
        # MinMax scale the scores so they are comparable
        if scores_kw.max() > 0:
            scores_kw = scores_kw / scores_kw.max()
        if scores_dense.max() > 0:
            scores_dense = scores_dense / scores_dense.max()
            
        combined_scores = alpha * scores_dense + (1 - alpha) * scores_kw
        return self._get_top_results(combined_scores, top_k)

    def search_hybrid_rerank(self, query, top_k=5):
        # Fetch top 20 candidates using hybrid
        candidates = self.search_hybrid(query, top_k=20)
        
        # Prepare pairs for cross encoder
        pairs = [[query, c['text']] for c in candidates]
        
        # Score pairs
        rerank_scores = self.cross_encoder.predict(pairs)
        
        # Sort by rerank score
        for i, score in enumerate(rerank_scores):
            candidates[i]['score'] = float(score)
            
        candidates = sorted(candidates, key=lambda x: x['score'], reverse=True)
        return candidates[:top_k]

    def _get_top_results(self, scores, top_k):
        top_indices = scores.argsort()[-top_k:][::-1]
        results = []
        for idx in top_indices:
            chunk = self.chunks[idx].copy()
            chunk['score'] = float(scores[idx])
            results.append(chunk)
        return results

if __name__ == "__main__":
    import time
    engine = MCPSearchEngine()
    engine.load_and_chunk()
    engine.build_index()
    
    query = "local filesystem access on Mac"
    
    print("\n--- Keyword Search ---")
    start = time.time()
    res = engine.search_keyword(query, top_k=3)
    print(f"Time: {time.time()-start:.3f}s")
    for r in res:
        print(f"[{r['owner']}/{r['repo']}] (Score: {r['score']:.3f}): {r['text'][:100]}...")
        
    print("\n--- Vector Search ---")
    start = time.time()
    res = engine.search_vector(query, top_k=3)
    print(f"Time: {time.time()-start:.3f}s")
    for r in res:
        print(f"[{r['owner']}/{r['repo']}] (Score: {r['score']:.3f}): {r['text'][:100]}...")
        
    print("\n--- Hybrid + Reranking ---")
    start = time.time()
    res = engine.search_hybrid_rerank(query, top_k=3)
    print(f"Time: {time.time()-start:.3f}s")
    for r in res:
        print(f"[{r['owner']}/{r['repo']}] (Score: {r['score']:.3f}): {r['text'][:100]}...")
