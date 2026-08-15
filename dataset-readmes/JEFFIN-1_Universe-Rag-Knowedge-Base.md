# 🌌 Universe Knowledge RAG

Retrieval-Augmented Generation (RAG) for questions about cosmology, astronomy, astrophysics, and the origin and evolution of the Universe.

The application turns local PDFs into searchable text chunks, retrieves the most relevant evidence for a question, and asks an LLM to produce a grounded answer.

## What it does today

- Extracts text page by page from PDFs with `pypdf`.
- Normalizes text, creates overlapping chunks, and generates local ONNX embeddings with `Xenova/all-MiniLM-L6-v2`.
- Stores chunks and vectors in Elasticsearch for dense-vector retrieval.
- Includes BM25, vector-search, and reciprocal-rank-fusion modules for hybrid retrieval.
- Serves chat through FastAPI and provides a Streamlit interface.
- Records chat metrics in PostgreSQL when the monitoring database/table is available.

The knowledge base can contain scientific papers, NASA/ESA publications, educational texts, and other curated material about topics such as the Big Bang, inflation, galaxy formation, dark matter and energy, the CMB, black holes, exoplanets, relativity, and the James Webb Space Telescope.

## Architecture

```text
PDFs → extraction → cleaning → chunking → embeddings → Elasticsearch
                                                     ↓
Streamlit UI → FastAPI → hybrid retrieval (vector + BM25) → RRF
                                                     ↓
                                              prompt builder → LLM → answer
```

The target production architecture described for this project also includes pgvector alongside Elasticsearch, richer `POST /ask` and `POST /search` APIs, and Grafana dashboards. Those parts are planned; the checked-in application currently exposes `POST /chat`, `GET /`, and `GET /health`.

## Quick start

Requirements: Python 3.12, Docker, and a Groq API key. The current chat service uses Groq's `llama-3.3-70b-versatile` model.

```bash
uv sync
docker compose up -d elasticsearch
cp .env.example .env
# Add GROQ_API_KEY to .env
python -m ingestion.register storage/raw/your-document.pdf
uv run uvicorn app.main:app --reload
```

In another terminal, launch the UI:

```bash
cd streamlit_app
uv run streamlit run app.py
```

Open the API documentation at `http://localhost:8000/docs` or the Streamlit URL printed by Streamlit.

## API

Ask a question with the currently implemented endpoint:

```bash
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"What does the supplied material say about cosmic inflation?"}'
```

## Project layout

| Path | Purpose |
| --- | --- |
| [`app/`](app/README.md) | FastAPI service, retrieval, prompts, LLM client, and monitoring. |
| [`ingestion/`](ingestion/README.md) | PDF-to-index pipeline. |
| [`embedder/`](embedder/README.md) | Local ONNX embedding model integration. |
| [`models/`](models/README.md) | Downloaded local model artifacts. |
| [`streamlit_app/`](streamlit_app/README.md) | Interactive browser interface. |
| [`storage/`](storage/README.md) | Raw PDFs and derived ingestion artifacts. |
| [`database/`](database/README.md) | Reserved database assets and schema files. |
| [`workflows/`](workflows/README.md) | Repeatable workflow definitions. |
| [`Notebooks/`](Notebooks/README.md) | Exploration notebooks for the pipeline. |
| [`tests/`](tests/README.md) | Automated tests. |

## Environment variables

| Variable | Used for | Default |
| --- | --- | --- |
| `GROQ_API_KEY` | LLM generation | Required for chat |
| `ELASTICSEARCH_URL` | Elasticsearch connection used by ingestion/search | `http://localhost:9200` |
| `ELASTICSEARCH_INDEX` | Index created by the ingestion store | `rag-documents` |
| `RAG_API_URL` | Streamlit-to-API connection | `http://localhost:8000` |
