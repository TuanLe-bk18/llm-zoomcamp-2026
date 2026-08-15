## Executive Summary
### Project Title:
Query-Knowledge Data Science Book Assistant (RAG)

### Project Goal:
Develop an AI-powered Q&A assistant that ingests book content from DataTalks.Club, indexes it for fast search, and provides accurate, context-aware answers using a hybrid retrieval-augmented generation (RAG) pipeline while taking care of governance guidelines.

It is **model agnostic** and **framework agnostic** is not dependent on any third party rigid rules. Completely **modular** appraoch to develop a rag pipeline that
1. **scans for data**, 
2. **ingests it**, 
3. **cleans it**, 
4. **stores**, 
5. **indexes**, 
6. provides responses while **filtering out profanity** and other toxic inputs at both input and output stage and 
7. **generates answers with cost tracking**.

### Key Features:
Hybrid Search:
 Combines lexical search (SQLite FTS5 BM25) with vector search (FAISS) using Reciprocal Rank Fusion (RRF) for optimal retrieval.

LLM Integration:
 Utilizes Google Gemini for query rewriting, text generation, and semantic caching.

Guardrails:
 Implements input moderation (ToxiGuardrail) and output safety checks to prevent toxic content.

Observability:
 Tracks query telemetry, operational costs, semantic drift, and user feedback.

Evaluation Framework:
 Includes offline benchmarks and synthetic QA generation for measuring performance.

### Technical Summary:
Technologies Used:
LLM: Google Gemini (gemini-2.5-flash)
Embedding Model: Sentence-BERT (cross-encoder/ms-marco-MiniLM-L-6-v2)
Vector Search: FAISS (CPU)
Lexical Search: SQLite FTS5 (BM25)
Orchestration: LangChain patterns (but not dependent), DLT (Data Loading Tool)
Web Framework: Streamlit

### Data Pipeline:
Ingestion: Scrapes ~35 data science book pages from DataTalks.Club
Chunking: Token-based chunking (1024 tokens with 128-token overlap)
Storage: SQLite database with separate tables for book metadata, scraped content, search indexes, and telemetry

### RAG Pipeline:
Query Processing: Input guardrail check → Query rewriting (LLM or local) → Embedding → Vector similarity search → Hybrid scoring (RRF) → Candidate reranking (cross-encoder)
Generation: Context retrieval from top-ranked chunks → Prompt engineering → Answer generation → Cost/token tracking
Evaluation: Offline synthetic QA evaluation, semantic drift detection, user feedback loop

### Observability:
Telemetry logging: Stores all queries, interactions, and costs in metrics.db
User feedback: Thumbs up/down for answer quality
Drift detection: Compares new queries to existing cache to identify shifting user interests

### Key Metrics:
Hybrid Search Recall: >90% on test queries
Latency: ~3-5 seconds per query (70% semantic, 30% lexical)
Cost: ~$0.0004 per query (estimated)
Accuracy: High satisfaction on internal benchmarks

### Impact:
Provides context-aware, accurate answers to data science book questions
Reduces hallucinations through grounded retrieval
Enables scalable knowledge management for book review content
offers operational transparency with cost and usage tracking


## How to read documentation to understand better

1. **spec-document.md** gives u a high level overview of the project.  
2. **implementation_plan.md** gives u a detailed plan of how to implement the project.  
3. **review_comments.md** gives u review comments on the implementation_plan.md  
4. **project_checklist.md** gives u checklist for cross checking what is part of the project compared to implementation_plan.md   
5. **requirement.txt** gives the project requirements w/ specific version.
6. **architecture.md** explains the architecture. Start with this to understand data flow. 

---

## Understanding the Project Architecture:

The project uses **Hexagonal Architecture** (Ports & Adapters) with **Domain-Driven Design**.
Details with architecture diagram and DDD elaboration on Architecture.md file. 

---

## 🚀 How to Run the Project

Since this project uses **`uv`** for dependency and environment management, everything can be run cleanly and fast.

### Step 1: Install Dependencies
Make sure you have `uv` installed, then synchronize/install the requirements into your local virtual environment (`.venv`):
```bash
uv pip install -r requirements.txt
```

### Step 2: Set Up Environment Variables
Verify that the `.env` file in the root directory contains your Google Gemini API Key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Step 3: Run Data Ingestion
Run the scraping crawler to fetch book pages from DataTalks.Club, chunk the reviews using token-based boundaries (1024-token chunks with a 128-token overlap), and save them into the SQLite database:
```bash
uv run app/ingestion.py
```

### Step 4: Rebuild Search Indices & Verify
Before launching, you need to build the search indices (SQLite FTS5 lexical index and FAISS vector index). You can do this by running the verification script:
```bash
uv run verify_pipeline.py
```
This script will:
1. Verify the ingestion database content.
2. Build/Rebuild the lexical and vector search indices.
3. Test input guardrails.
4. Execute test queries to verify search and generation.

### Step 5: Start the Streamlit Dashboard UI
Launch the interactive dashboard, containing the Chat Assistant, Operational/Cost Analytics, Semantic Drift tracking, and Benchmark Leaderboard:
```bash
uv run streamlit run dashboard.py
```


---

## 📁 Project Structure

* `app/ingestion.py` - Web crawler, HTML parsing scraper, chunker, and `dlt` pipeline loading into SQLite.
* `app/database.py` - SQLite FTS5 lexical search, FAISS vector search, and semantic cache implementation.
* `app/rag.py` - Guardrails (ToxiGuardrail), query rewriter, reranking (ms-marco CrossEncoder), and Gemini generative orchestration.
* `app/metrics.py` - Obeservability schema, SQL telemetry logger, feedback endpoints, and semantic drift calculations.
* `app/eval.py` - Synthetic ground-truth QA dataset generator and offline evaluation pipeline benchmarks.
* `dashboard.py` - Streamlit multi-tab user interface.
* `verify_pipeline.py` - Command-line sanity check testing harness.
