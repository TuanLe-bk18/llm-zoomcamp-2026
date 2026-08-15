# Le Petit Chat

Le Petit Chat is an Agentic Retrieval-Augmented Generation (Agentic RAG) application designed to answer questions about *The Little Prince* by Antoine de Saint-Exupéry.

The project combines a Large Language Model (LLM), a vector-based knowledge base, and an autonomous retrieval agent to provide accurate, grounded, and context-aware answers about the book.

Unlike a traditional chatbot, Le Petit Chat retrieves relevant passages from the novel before generating a response, ensuring that answers are supported by the original text rather than relying solely on the model's internal knowledge.

Developed as the final project for the **DataTalksClub LLM Zoomcamp**.

---

## Project Goals

The main objective of this project is to build an end-to-end Agentic RAG system following modern LLM application development practices, including:

- Automated data ingestion from the source book
- Document preprocessing and chunking
- Embedding generation and vector indexing
- Tool-based retrieval using a LangChain agent
- Prompt and model evaluation
- Interactive user interface
- Conversation memory
- Monitoring and user feedback collection

## Features

- Agentic RAG architecture built with LangChain — the LLM decides on its own when to query the book, rather than always retrieving on a fixed schedule
- Hybrid retrieval (semantic search + BM25, fused via Reciprocal Rank Fusion) with cross-encoder re-ranking
- Automatic selection of the best-performing chunking strategy, retrieval approach, LLM, and system prompt, based on evaluation results (not manual preference)
- Multi-turn conversations with session-based memory (LangGraph `MemorySaver`)
- Source attribution: each answer shows the retrieved passages used to generate it, in a collapsible panel
- Modular, fully automated ingestion pipeline for rebuilding the knowledge base
- Retrieval and LLM evaluation using a 50-question Golden Dataset (ROUGE metrics + LLM-as-judge with a third, independent judge model)
- User feedback collection (👍/👎) and a monitoring dashboard
- Interactive web interface for end users (Streamlit) and a documented API (FastAPI)

---

## Project Architecture

```
                    ┌─────────────────┐
                    │   Book (PDF)     │
                    └────────┬─────────┘
                             │  Automated Ingestion Pipeline
                             ▼
              Extraction → Cleaning → Chunking → Embeddings
                             │
                             ▼
                    ┌─────────────────┐
                    │  Vector Database │  (ChromaDB, embedded;
                    │                  │   2 chunking strategies compared)
                    └────────┬─────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                 Retrieval                    │
        │   Semantic Search   +   Hybrid (BM25 + RRF)  │
        │                    │                          │
        │                    ▼                          │
        │            Cross-Encoder Re-ranking          │
        └────────────────────┬────────────────────┘
                             │
                    ┌─────────────────┐
                    │  LangGraph Agent │  tool calling +
                    │                  │  session memory
                    └────────┬─────────┘
                             │
                    ┌─────────────────┐
                    │   OpenAI LLM     │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                              ▼
       User Interface                 Monitoring
   (FastAPI + Streamlit)         (feedback DB + dashboard)
```

---

## Technologies

| Component | Technology |
|---|---|
| PDF extraction | pdfplumber |
| Vector database | ChromaDB (embedded, `PersistentClient`) |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Text search | Hybrid retrieval: Semantic + BM25 (via `rank-bm25`, RRF fusion with k=60) |
| Re-ranking | Cross-encoder (`ms-marco-MiniLM-L-6-v2`) |
| Agent orchestration | LangChain + LangGraph (`create_agent`) |
| LLM | OpenAI (model selected automatically via evaluation) |
| Conversation memory | LangGraph `MemorySaver` (per session `thread_id`) |
| Interface | Streamlit (chat) + FastAPI (API) |
| Monitoring | SQLite (feedback) + Streamlit dashboard |
| Containerization | Docker + docker-compose (3 services) |

---

## Evaluation Summary

The project evaluates its own design decisions in three sequential stages, each using a [Golden Dataset](evaluation/golden_dataset.json) of 50 questions about the book:

1. **Chunking strategy**: sentence-based vs. fixed-size → decides which vector collection to use (blended retrieval score: ROUGE-1 + ROUGE-L + semantic similarity, with optional LLM judge)
2. **Retrieval approach**: semantic search vs. hybrid search → decides the retrieval method (same blended retrieval score and optional judge)
3. **LLM configuration**: a grid of models × system prompts → decides the production configuration (LLM-as-judge, scored by a third, independent model to avoid self-preference bias)

Full reports are saved to `evaluation/results/*.json` after running each script. Details in [docs/evaluation.md](docs/evaluation.md).

---

## Repository Structure

```
.
├── agent/            # LangGraph agent, tools and prompts
├── app/              # FastAPI api and streamlit_app
├── chroma_storage/   # Vector DB (generated at runtime)
├── ingestion/        # Automated ingestion pipeline (extraction, chunking and embedding)
├── monitoring/       # Dashboard and feedback DB script
├── retrieval/        # Search logic and vector database access
├── evaluation/       # Retrieval and LLM evaluation
├── data/             # Source documents, chunks and processed data
├── docs/             # Project documentation
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .gitignore
├── .env              # Must be created before running the project
└── README.md
```

---

## Getting Started

Quick start via Docker:
```bash
# edit .env and fill in OPENAI_API_KEY and CHROMA_PERSIST_DIR=./chroma_storage
docker-compose up --build
```
- Chat: http://localhost:8501
- Monitoring dashboard: http://localhost:8502
- API (Swagger docs): http://localhost:8000/docs

Full setup instructions (manual installation, environment variables, running the ingestion pipeline) in [docs/setup.md](docs/setup.md).

---

## Documentation

Detailed documentation for each component is available in the `docs/` directory:

| Document | Content |
|---|---|
| [docs/setup.md](docs/setup.md) | Installation, environment variables, running via Docker or manually |
| [docs/ingestion.md](docs/ingestion.md) | PDF extraction, cleaning, chunking strategies, embeddings, pipeline orchestration |
| [docs/retrieval.md](docs/retrieval.md) | Semantic search, hybrid search (BM25 + RRF), re-ranking |
| [docs/agent.md](docs/agent.md) | LangGraph agent, tool calling, session memory, prompts |
| [docs/evaluation.md](docs/evaluation.md) | Golden dataset, the 3-stage evaluation pipeline |
| [docs/monitoring.md](docs/monitoring.md) | User feedback, dashboard, collected metrics |
| [docs/usage.md](docs/usage.md) | Using the chat, feedback, viewing retrieved passages |

---

This project was developed for educational purposes as part of an LLM Engineering course project.

