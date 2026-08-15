# SAP Asset Accounting RAG (LLM Bootcamp Capstone)

A Retrieval-Augmented Generation (RAG) system that answers questions about **SAP S/4HANA Asset Accounting (FI-AA)** from the official SAP Help Portal PDF. It guards against off-topic questions, retrieves the most relevant passages via vector search, and uses an LLM to produce concise, source-grounded answers.

---

## Problem

SAP's asset accounting documentation is large, fragmented across the Help Portal, and difficult for non-experts to query precisely. Accountants, auditors, and project teams need fast, citation-grounded answers to questions such as:

- *"What depreciation methods does FI-AA support?"*
- *"How does an asset retirement by scrapping get posted?"*
- *"What is the difference between AUC and a regular fixed asset?"*

Generic LLMs hallucinate SAP-specific answers. A RAG pipeline over the official SAP PDF solves this by grounding generation in the actual document.

---

## Architecture

```
            ┌─────────────────────────────────────────────────┐
            │              data/sap_asset_pdfdownload.pdf     │
            └─────────────────────┬───────────────────────────┘
                                  │ offline (ingest)
                                  ▼
            ┌─────────────────────────────────────────────────┐
            │  Load → Chunk → Embed (OpenAI text-emb-3-small) │
            └─────────────────────┬───────────────────────────┘
                                  ▼
            ┌─────────────────────────────────────────────────┐
            │     output/asset_index.faiss                    │
            │     output/chunk_metadata.json                 │
            │     output/bm25_index.pkl   (sparse, BM25)      │
            └─────────────────────┬───────────────────────────┘
                                  │ online (query)
                                  ▼
   query ─► RewriteQuery ─► VerifyQuery ─► EmbedQuery ─► RetrieveHybrid ─► Synthesize ─► answer
            (multi-query       (asset-acct       (cosine,    (dense + BM25 +           (LLM
             or HyDE)           gate)             FAISS)      RRF + cross-encoder      call)
                                                            re-rank)
```

The flow is orchestrated by [PocketFlow](https://github.com/The-Pocket/PocketFlow) (`src/flow.py`):
- **Offline nodes**: `LoadDocumentNode → ChunkTextNode → GenerateEmbeddingsNode → StoreIndexNode → StoreMetadataNode` (+ BM25 index build at the script level)
- **Online nodes (hybrid, default)**: `VerifyQueryNode → RewriteQueryNode → ProcessQueryNode → RetrieveHybridNode → SynthesizeResponseNode`
- **Online nodes (legacy dense-only)**: `VerifyQueryNode → ProcessQueryNode → RetrieveChunksNode → SynthesizeResponseNode`

---

## Project Structure

```
llm_bootcamp_capstone/
├── data/                          # source PDFs (kept in repo; small fixtures)
│   ├── sap_asset_pdfdownload.pdf  # main knowledge base
│   └── simple.pdf                 # unit-test fixture
├── output/                        # generated FAISS index + chunk metadata + feedback.db
├── scripts/
│   ├── ingest.py                  # offline: PDF → FAISS + metadata + BM25
│   ├── eval_retrieval.py          # retrieval eval harness
│   ├── eval_llm.py                # LLM eval harness (LLM-as-judge)
│   └── query.py                   # online: interactive REPL
├── src/
│   ├── flow.py                    # PocketFlow node graph (dense + hybrid)
│   ├── loader.py                  # document loader façade
│   ├── text_chunker.py            # overlap-aware splitter
│   ├── embedding.py               # OpenAI embeddings (cached)
│   ├── vector_search.py           # FAISS cosine-similarity search
│   ├── bm25_search.py             # BM25 sparse retriever
│   ├── hybrid_search.py           # Reciprocal-Rank Fusion combiner
│   ├── reranker.py                # cross-encoder re-ranker
│   ├── query_rewrite.py           # multi-query + HyDE rewrites
│   ├── feedback_store.py          # SQLite-backed interaction log
│   ├── call_llm.py                # OpenAI chat (cached)
│   ├── eval_set.py                # hand-curated retrieval Q&A set
│   ├── core/types.py              # Document / Chunk / ChunkRecord contracts
│   ├── libs/loader/               # pluggable loaders (PDF + base)
│   └── api/
│       ├── app.py                 # FastAPI service (UI + endpoints)
│       └── static/index.html      # chat front-end
├── dashboard.py                   # Streamlit monitoring dashboard
├── notebooks/                     # Jupyter eval notebooks
├── tests/                         # pytest unit + integration suites
├── pyproject.toml                 # uv-managed dependencies
├── uv.lock                        # exact pinned versions (reproducible)
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Requirements

- **Python** ≥ 3.12 (see `.python-version`)
- **uv** (recommended) — fast Python package manager: https://docs.astral.sh/uv/
- **OpenAI API key** with access to `gpt-4o-mini` and `text-embedding-3-small`
- (Optional) **Docker** + **Docker Compose** for containerised runs

All Python dependencies are pinned in `uv.lock` — every transitive version is reproducible byte-for-byte.

---

## Setup

### Option A — Local (uv)

```bash
# 1. Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Sync dependencies into .venv (uses uv.lock for pinned versions)
uv sync

# 3. Set your OpenAI key
export OPENAI_API_KEY="sk-..."

# 4. (Optional) dev tools
uv sync --extra dev
```

### Option B — Docker Compose (one command)

```bash
export OPENAI_API_KEY="sk-..."
docker compose run --rm app python scripts/ingest.py   # build the index
docker compose run --rm app python scripts/query.py   # ask questions
```

---

## How to Run

### 1. Ingest the PDF into the vector store

```bash
uv run python scripts/ingest.py \
    --file-path data/sap_asset_pdfdownload.pdf \
    --output-dir output
```

Produces:
- `output/asset_index.faiss` — FAISS dense index (cosine similarity, normalised vectors)
- `output/chunk_metadata.json` — per-chunk text + metadata
- `output/bm25_index.pkl` — BM25 sparse index over the same chunks (built by default)

You can swap in a different PDF without code changes:

```bash
uv run python scripts/ingest.py --file-path path/to/your.pdf --output-dir output
```

### 2. Ask questions

Hybrid (default — dense + BM25 + RRF + cross-encoder re-rank):

```bash
uv run python scripts/query.py --output-dir output
```

Dense-only legacy baseline:

```bash
uv run python scripts/query.py --mode dense
```

Disable the re-ranker (faster, slightly less accurate):

```bash
uv run python scripts/query.py --no-rerank
```

Then type questions in the REPL:

```
Ask a question about asset accounting (or type 'exit' to quit): What depreciation methods does FI-AA support?
Agent response:
  content: "FI-AA supports straight-line, declining-balance, and..."
```

Off-topic questions are rejected with an explanation (see `VerifyQueryNode`).

### 3. Evaluate retrieval quality

Compares dense / BM25 / hybrid / hybrid+rerank on a 15-query hand-curated set and
writes a JSON + CSV report + bar-chart PNG:

```bash
uv run python scripts/eval_retrieval.py
# or with the notebook for the chart:
uv run jupyter lab notebooks/eval_retrieval.ipynb
```

### 4. Evaluate answer-generation prompts (LLM-as-judge)

Requires `OPENAI_API_KEY`. Compares 3 prompt strategies (concise / detailed /
structured) and reports judge scores (0–3) for correctness, groundedness, conciseness:

```bash
export OPENAI_API_KEY=sk-...
uv run python scripts/eval_llm.py
```

### 5. Web UI + monitoring dashboard

A FastAPI service exposes the hybrid retrieval pipeline over HTTP and serves a
minimal HTML chat UI. Every query is logged to a SQLite store; the Streamlit
dashboard reads that store and renders 5+ charts.

```bash
# Terminal 1: FastAPI chat UI  → http://localhost:8000
uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000

# Terminal 2: Streamlit dashboard → http://localhost:8501
uv run streamlit run dashboard.py
```

Or via docker-compose (both services share one image):

```bash
docker compose up -d api dashboard
```

Endpoints exposed by the API:

| Method | Path           | Purpose                                |
|--------|----------------|----------------------------------------|
| GET    | `/`            | HTML chat UI                           |
| GET    | `/health`      | Liveness + index stats                 |
| POST   | `/query`       | Run the RAG pipeline, log interaction  |
| POST   | `/feedback`    | Attach a 1-5 rating + optional comment |
| GET    | `/interactions`| Recent interactions (debug)           |
| GET    | `/docs`        | Auto-generated OpenAPI docs            |

Dashboard charts (7 total, ≥5 required by rubric):

1. Query volume over time (daily)
2. Retrieval top-1 score distribution
3. Latency P50 / P95 trend
4. Rating distribution (1–5)
5. 👍 vs 👎 share of rated responses
6. Top 20 most-asked queries
7. Retrieval mode breakdown

---

## Running Tests

```bash
uv run pytest                              # all tests
uv run pytest tests/unit -v                # unit tests only
uv run pytest --cov=src                    # with coverage
```

---

## Configuration

| Env var            | Purpose                              | Required |
|--------------------|--------------------------------------|----------|
| `OPENAI_API_KEY`   | OpenAI embeddings + chat completions | Yes      |
| `KMP_DUPLICATE_LIB_OK` | Set automatically to `TRUE` to silence the macOS OMP clash between PyTorch (re-ranker) and FAISS | No |
| `OMP_NUM_THREADS`  | Set automatically to `1` on macOS for the same reason | No |
| `RERANK_MODEL`     | Override the cross-encoder model id (default `cross-encoder/ms-marco-MiniLM-L-6-v2`) | No |

Defaults (edit `src/flow.py` / `src/text_chunker.py` if you want different behaviour):
- Embedding model: `text-embedding-3-small` (1536-dim)
- Chat model: `gpt-4o-mini`
- Chunk size: 2000 chars, 500 char overlap
- Retrieval top-k: 5 (hybrid: 20 first-stage → RRF → cross-encoder)
- LLM max tokens: 1024

### macOS / Apple Silicon note

PyTorch (loaded by the cross-encoder) and FAISS both bundle their own copy of
the OpenMP runtime. Both `src/reranker.py` and the CLI scripts set
`KMP_DUPLICATE_LIB_OK=TRUE` and `OMP_NUM_THREADS=1` automatically so the
process starts cleanly. If you ever see `OMP: Error #15: Initializing
libomp.dylib, but found libomp.dylib already initialized.`, export the var
manually before running.

---

## Tech Stack

| Layer            | Choice                                                       |
|------------------|--------------------------------------------------------------|
| LLM              | OpenAI `gpt-4o-mini`                                         |
| Embeddings       | OpenAI `text-embedding-3-small` (1536-dim)                   |
| Vector DB        | FAISS (`IndexFlatIP` + L2 normalisation)                     |
| Sparse retriever | `rank-bm25` + Reciprocal-Rank Fusion                         |
| Re-ranker        | `cross-encoder/ms-marco-MiniLM-L-6-v2`                       |
| Query rewriting  | Multi-query expansion (LLM) + HyDE (LLM)                     |
| Orchestration    | PocketFlow (lightweight DAG framework)                       |
| PDF parsing      | MarkItDown + PyMuPDF (image extraction)                      |
| Packaging        | `uv` + `uv.lock`                                             |
| Containers       | Docker + docker-compose                                      |

---

## License

Educational project — no warranty. The SAP PDF remains © SAP SE and is referenced under fair use for the purpose of this coursework.