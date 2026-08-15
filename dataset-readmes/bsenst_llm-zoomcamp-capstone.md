# EBM Expert AI Assistant

## Problem Description

German physicians, medical coders, and practice staff use the **Einheitlicher Bewertungsmaßstab (EBM)** to determine billing codes and reimbursement rules for outpatient medical services. The official EBM documentation exceeds hundreds of pages, is constantly updated, and is extremely difficult to search efficiently.

**EBM Expert AI** is a production-grade Retrieval-Augmented Generation (RAG) + Agent application that enables users to ask natural language questions about the EBM and receive accurate, cited answers grounded exclusively in the official KBV document.

### Key Requirements
- No hallucinations - every answer must cite the original EBM source
- Natural language understanding of German medical terminology
- Conversation memory and follow-up question handling
- Full evaluation, monitoring, and observability

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Streamlit UI                                 │
│  ┌───────────┐ ┌────────────┐ ┌────────────┐ ┌───────────────────┐ │
│  │   Chat    │ │ Monitoring │ │ Evaluation │ │    Settings       │ │
│  └─────┬─────┘ └─────┬──────┘ └─────┬──────┘ └───────┬───────────┘ │
└────────┼────────────┼─────────────┼───────────────┼──────────────┘
         │            │             │               │
         ▼            ▼             ▼               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      LangGraph Agent                                 │
│  ┌──────────┐  ┌─────────────┐  ┌──────────┐  ┌─────────────────┐  │
│  │ Query    │  │ Retrieval   │  │ Context  │  │ Answer          │  │
│  │ Rewrite  │► │ (Hybrid)    │► │ Assess   │► │ Generation      │  │
│  └──────────┘  └──────┬──────┘  └──────────┘  └────────┬────────┘  │
│                       │                                  │           │
└───────────────────────┼──────────────────────────────────┼───────────┘
                        │                                  │
          ┌─────────────▼────────────┐       ┌─────────────▼───────────┐
          │   Hybrid Retriever       │       │   OpenRouter LLM        │
          │  ┌─────────┐ ┌────────┐ │       │  (GPT-4.1, Claude, ...) │
          │  │ Dense   │ │ BM25   │ │       └─────────────────────────┘
          │  └────┬────┘ └───┬────┘ │
          │       │          │       │
          │       ▼          ▼       │
          │  ┌─────────────────┐    │
          │  │ RRF Fusion      │    │
          │  └────────┬────────┘    │
          │           │             │
          │           ▼             │
          │  ┌─────────────────┐    │
          │  │ Reranker        │    │
          │  │ BAAI/bge        │    │
          │  └────────┬────────┘    │
          └───────────┼────────────┘
                      │
                      ▼
          ┌───────────────────────┐
          │      Qdrant           │
          │   (Vector DB)         │
          └───────────────────────┘
                      ▲
                      │
          ┌───────────────────────────┐
           │  dltHub Ingestion Pipeline │
           │  ┌──────────┐ ┌─────────┐  │
           │  │ XML ZIP  │ │ Chunk   │  │
           │  │ Download │ │+Embed   │  │
           │  └──────────┘ └─────────┘  │
           └───────────────────────────┘
```

---

## Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **LLM** | OpenRouter (GPT-4.1, Claude, Gemini, etc.) | Multi-model support, unified API, cost transparency |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) | Local, fast, high quality for German text |
| **Vector DB** | Qdrant | High performance, filtering, scalable |
| **Orchestration** | LangGraph | Stateful agent workflows, memory, tool integration |
| **Ingestion** | dltHub | Reproducible pipelines, incremental loading, observability |
| **Data Source** | KBV SDEBM XML | Structured EBM data, higher accuracy than PDF |
| **Retrieval** | Dense + BM25 + RRF | Hybrid search maximizes recall and precision |
| **Reranking** | BAAI/bge-reranker-v2-m3 | Cross-encoder reranking for top-5 precision |
| **UI** | Streamlit | Rapid development, modern chat interface |
| **Monitoring** | Logfire | LLM observability, latency, cost tracking |
| **Evaluation** | RAGAS | Faithfulness, relevancy, precision, recall |
| **Containerization** | Docker Compose | One-command deployment, persistent storage |

---

## Why dltHub?

**dltHub** provides:
- **Reproducibility**: Pipeline definitions as code with version control
- **Incremental Loading**: Automatic detection of new/changed content
- **Schema Evolution**: Handles document version changes gracefully
- **Observability**: Built-in pipeline metrics and logging
- **Extensibility**: Easy to add new data sources or destinations

---

## Why OpenRouter?

**OpenRouter** provides:
- **Unified API**: Single endpoint for OpenAI, Anthropic, Google, Meta, Mistral, DeepSeek
- **Cost Transparency**: Clear pricing per provider and model
- **Fallback Support**: Automatic failover between providers
- **No Vendor Lock-in**: Switch models via environment variable
- **Latest Models**: Access to cutting-edge models immediately

---

## Why Logfire?

**Logfire** provides:
- **LLM Tracing**: Every LLM call with prompt, completion, latency, tokens
- **Cost Tracking**: Automatic cost calculation per request
- **Error Monitoring**: Real-time error alerting
- **Performance Insights**: Latency breakdowns for retrieval, reranking, generation
- **Zero Config**: Auto-instrumentation for LangChain, OpenAI, requests

---

## Data Ingestion

The ingestion pipeline (`ingest.py`) uses the official KBV SDEBM structured data instead of the PDF:

1. **Download** the KBV EBM ZIP archive (`SDEBM_V1.61.zip`) from the KBV update server
2. **Extract** the ZIP archive to access the structured XML data
3. **Parse XML** using `xml.etree.ElementTree` with namespace-aware extraction
4. **Detect Structure** (chapters, sections, headings) from XML element metadata
5. **Chunk** with tiktoken tokenizer, configurable size and overlap
6. **Embed** using sentence-transformers
7. **Load** into Qdrant with metadata (element_id, chapter, section, heading, page, version)

### Why XML Instead of PDF?

- **Structured data**: Preserves the document hierarchy and element relationships
- **Higher accuracy**: No OCR errors or text extraction artifacts
- **Faster processing**: No need for complex PDF parsing
- **Official source**: Direct from KBV's structured data distribution
- **Reproducible**: Deterministic parsing with no layout-dependent extraction

### Metadata Schema
```json
{
  "chunk_id": "05195fb2-76e0-57f5-9c54-583e0a913b99",
  "text": "chunk content...",
  "page": 42,
  "chapter": "Kapitel 2 Allgemeine Bestimmungen",
  "section": "§ 12",
  "heading": "Leistungsausschluss",
  "document_version": "2026-3",
  "token_count": 1234,
  "element_id": "L001",
  "tag": "Leistung"
}
```

---

## Retrieval Flow

1. **Query Rewriting**: German medical terminology normalization, abbreviation expansion
2. **Hybrid Search**:
   - Dense: Semantic similarity via embeddings
   - Sparse: BM25 keyword matching
3. **Reciprocal Rank Fusion**: Combine dense and sparse results with RRF(k=60)
4. **Reranking**: Cross-encoder (BAAI/bge-reranker-v2-m3) scores top-20 → top-5
5. **Context Assessment**: Average score threshold for sufficient context
6. **Generation**: Structured prompt with citations
7. **Citation**: Every claim linked to page number and heading

---

## Evaluation Methodology

### Retrieval Metrics
- **Recall@K**: Fraction of relevant documents in top-K
- **Precision@K**: Fraction of top-K that are relevant
- **MRR**: Mean Reciprocal Rank of first relevant result

### LLM Metrics (RAGAS)
- **Faithfulness**: Answer grounded in provided context
- **Answer Relevancy**: Answer addresses the question
- **Context Precision**: Relevant context ranked higher
- **Context Recall**: All relevant info present in context

### Prompt Evaluation
Four prompt strategies compared automatically:
1. Simple RAG
2. Citation-first
3. Medical expert persona
4. Structured answer format

---

## Monitoring

### Metrics Captured
- Daily request count
- LLM latency (p50, p95, p99)
- Retrieval latency
- Model usage distribution
- Token consumption (prompt + completion)
- Cost estimation per request
- Feedback distribution (thumbs up/down)
- Error rates and types
- Conversation traces

### Dashboard
Access via Streamlit sidebar: **Monitoring** page

---

## Docker Setup

### Prerequisites
- Docker Engine 24+
- Docker Compose v2+
- OpenRouter API key

### Quick Start
```bash
# Clone repository
git clone <repo-url>
cd llm-zoomcamp-capstone

# Configure environment
cp .env.example .env
# Edit .env with your OPENROUTER_API_KEY

# Start all services
docker compose up -d

# Ingest the EBM document
docker compose exec ingest python ingest.py

# Access the UI
open http://localhost:8501
```

### Services
| Service | Port | Description |
|---------|------|-------------|
| qdrant | 6333, 6334 | Vector database |
| streamlit | 8501 | Web UI |
| ingest | - | One-shot ingestion worker |

### Lean packaging notes
- **CPU-only torch**: the image installs `torch`/`torchvision` from the PyTorch CPU
  index so `sentence-transformers` never pulls multi-GB `nvidia-*` CUDA wheels.
- **Optional Logfire**: observability is excluded from the base image. Set
  `OBSERVABILITY=true` (in `.env` or as a build arg) to also install
  `requirements-observability.txt` when you need Logfire tracing. The code
  degrades gracefully (no-op) when the package or token is absent.
- **Small build context**: a `.dockerignore` excludes `data/`, `.venv/`,
  `__pycache__`, and model caches so the context stays a few hundred KB.

---

## Running Locally

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
# Note: OpenRouter requires credits for LLM calls. Adjust MAX_TOKENS if needed.

# Start Qdrant
docker run -d -p 6333:6333 qdrant/qdrant:v1.12.0

# Ingest data
python ingest.py

# Run tests
pytest tests/ -v

# Start UI
streamlit run app.py
```

---

## Project Structure

```
llm-zoomcamp-capstone/
├── app.py                     # Streamlit application entry point
├── ingest.py                  # dltHub ingestion pipeline
├── evaluate.py                # RAGAS evaluation runner
├── pyproject.toml             # Project metadata and dependencies
├── requirements.txt           # pip requirements
├── Dockerfile                 # Container image definition
├── docker-compose.yml         # Multi-service orchestration
├── .env.example               # Environment variable template
├── .dockerignore
├── README.md
├── data/
│   ├── SDEBM.zip              # Downloaded KBV ZIP archive
│   ├── ebm.xml                # Extracted XML for ingestion
│   ├── test_queries.json      # Evaluation test set
│   └── evaluation_report.json
├── src/
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py       # Pydantic settings
│   ├── ingestion/
│   │   ├── __init__.py
│   │   └── pipeline.py       # XML → Qdrant pipeline
│   ├── retrieval/
│   │   ├── __init__.py
│   │   └── retriever.py      # Dense, BM25, Hybrid, RRF
│   ├── reranking/
│   │   ├── __init__.py
│   │   └── reranker.py       # BGE cross-encoder reranker
│   ├── agent/
│   │   ├── __init__.py
│   │   └── ebm_agent.py      # LangGraph agent
│   ├── evaluation/
│   │   ├── __init__.py
│   │   └── evaluator.py      # RAGAS metrics
│   ├── monitoring/
│   │   ├── __init__.py
│   │   └── monitoring.py     # Logfire metrics
│   ├── ui/
│   │   ├── __init__.py
│   │   └── streamlit_app.py  # Streamlit interface
│   └── utils/
│       ├── __init__.py
│       └── helpers.py        # Shared utilities
├── tests/
│   ├── __init__.py
│   ├── test_ingestion.py
│   ├── test_retrieval.py
│   └── test_utils.py
└── docs/
    └── architecture.md
```

---

## Screenshots

<img width="1366" height="768" alt="Screenshot 2026-07-19 111902" src="https://github.com/user-attachments/assets/ecc1f4b5-8379-45ab-a981-d5a2d10c6010" />

1. Chat interface with citations

<img width="1366" height="768" alt="Screenshot 2026-07-19 112012" src="https://github.com/user-attachments/assets/f3e14cf9-4b04-4310-a80f-7536321bcf78" />

2. Settings panel

<img width="1366" height="768" alt="Screenshot 2026-07-19 112122" src="https://github.com/user-attachments/assets/f0bba5e1-6c28-49e2-856e-394c4d9dec43" />

3. Logfire monitoring dashboard

---

## Future Improvements

- Semantic cache for repeated queries
- Response streaming for faster UX
- Multi-document support (other KBV guidelines)
- Voice input for mobile use
- Multi-language support
- Fine-tuned EBM-specific embeddings
- A/B testing framework for prompts
- Automated nightly ingestion pipeline
- Kubernetes Helm charts
- API server (FastAPI) for programmatic access

---

## License

MIT

---

## Contact

Built for the DataTalks.Club LLM Zoomcamp Capstone Project.
