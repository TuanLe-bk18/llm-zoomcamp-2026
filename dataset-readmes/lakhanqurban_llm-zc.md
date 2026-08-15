# LLM Zoomcamp Cohort 2026

This repo contains coursework and final project for the [LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp) by [DataTalks.Club](https://datatalks.club/) (Cohort 2026).

## About the Course

The LLM Zoomcamp is a free course covering the fundamentals of building LLM applications — from Retrieval-Augmented Generation and vector search to AI agents, evaluation, and monitoring. It is taught by [Alexey Grigorev](https://linkedin.com/in/agrigorev) and the DataTalks.Club team.

## Technologies & Tools

| Area | Tools |
|------|-------|
| RAG & Search | Keyword search, vector search (PGVector, SQLite), hybrid search, reranking |
| Embeddings | OpenAI, sentence-transformers |
| LLMs | OpenAI GPT, Claude, function calling |
| Orchestration | Kestra |
| Data Ingestion | dlt (data load tool) |
| Vector Databases | PGVector, SQLite |
| Evaluation | LLM-as-a-Judge, retrieval metrics |
| Monitoring | Pydantic Logfire, dashboards |
| Language | Python, SQL |

## Homework

All homework solutions for each module are in the [`cohorts/2026/`](cohorts/2026/) directory:

| Module | Topic | Homework |
|--------|-------|----------|
| 1 | Agentic RAG | [homework.md](cohorts/2026/01-agentic-rag/homework.md) |
| 2 | Vector Search | [homework.md](cohorts/2026/02-vector-search/homework.md) |
| 3 | Orchestration (Kestra) | [homework.md](cohorts/2026/03-orchestration/homework.md) |
| 4 | Evaluation | [homework.md](cohorts/2026/04-evaluation/homework.md) |
| 5 | Monitoring | [homework.md](cohorts/2026/05-monitoring/homework.md) |
| 6 | Best Practices | — |
| 7 | End-to-End Project | — |
| Workshop 1 | Data Ingestion with dlt | [homework.md](cohorts/2026/workshops/dlt/homework.md) |

## Final Project — 🚗 AD-Assist

A Retrieval-Augmented Generation system for autonomous driving researchers, enabling fast, accurate answers across research papers, CARLA docs, bug reports, traffic rules, safety standards, and simulation scenarios.

**[Full Project README →](ad-assist/README.md)**

### Pipeline Architecture

```
User Question ──► Query Rewriting (LLM) ──► Hybrid Search (Vector + BM25) ──► Cross-Encoder Re-rank ──► LLM ──► Answer + Citations
```

### Key Features

- **Hybrid Search** — Combines dense vector search (BGE-small embeddings) with BM25 keyword retrieval
- **Query Rewriting** — LLM-powered rephrasing for ambiguous or short questions
- **Cross-Encoder Re-ranking** — Boosts precision on top results
- **Multi-Provider LLM** — OpenAI GPT-4o-mini and Google Gemini 2.0 Flash Lite
- **Streamlit UI** — Chat interface with source citations, feedback buttons, and live stats
- **FastAPI Backend** — REST API for programmatic access
- **Monitoring** — SQLite logging + Prometheus + Grafana dashboards
- **Evaluation Suite** — Hit-rate, MRR, nDCG, and LLM-as-a-Judge scoring
- **Docker Deployment** — One-command full-stack setup with Qdrant

### Data Sources

37 files across 7 categories (~903 KB, 262 documents → 373 chunks): research papers (arXiv), CARLA documentation, bug reports (CARLA/Autoware/Apollo), traffic rules (German/Italian), safety standards (ISO 21448/26262), driving scenarios (XML), and OpenDRIVE road geometry.

### Quick Start

```bash
cd ad-assist
pip install -r requirements.txt
python -m src.ingestion.data_downloader
streamlit run ui/streamlit_app.py
# Or: docker compose up (full stack with Qdrant, Grafana, Prometheus)
```

## Repository Structure

```
.
├── ad-assist/                # Final project — AD-Assist RAG system
│   ├── src/                  #   Ingestion, retrieval, RAG pipeline, API, evaluation
│   ├── ui/                   #   Streamlit frontend
│   ├── data/                 #   Source documents (7 categories)
│   ├── notebooks/            #   Evaluation notebook
│   ├── scripts/              #   Utility scripts
│   └── docker-compose.yml    #   Full-stack deployment
├── cohorts/2026/             # Homework solutions by module
│   ├── 01-agentic-rag/
│   ├── 02-vector-search/
│   ├── 03-orchestration/
│   ├── 04-evaluation/
│   ├── 05-monitoring/
│   └── workshops/dlt/
├── 01-agentic-rag/           # Course material (modules 1–7)
├── 02-vector-search/
├── 03-orchestration/
├── 04-evaluation/
├── 05-monitoring/
├── 06-best-practices/
├── 07-project-example/
├── images/
├── project.md                # Capstone project guidelines
└── README.md
```

## Acknowledgements

Thanks to [Alexey Grigorev](https://linkedin.com/in/agrigorev) and the entire [DataTalks.Club](https://datatalks.club/) team for offering this incredible course for free. Special thanks to all the instructors and the community on Slack for their support throughout the cohort.
