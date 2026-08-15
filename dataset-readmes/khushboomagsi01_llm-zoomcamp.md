<div align="center">

# 🧠 LLM Zoomcamp Cohort 2026

📚 Coursework & Final Project for the [LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp) by [DataTalks.Club](https://datatalks.club/) — Cohort 2026

⭐ Star this repo to stay updated

</div>

---

## 📖 About the Course

The LLM Zoomcamp is a free course covering the fundamentals of building LLM applications — from Retrieval-Augmented Generation and vector search to AI agents, evaluation, and monitoring. It is taught by [Alexey Grigorev](https://linkedin.com/in/agrigorev) and the DataTalks.Club team.

## 🛠️ Technologies & Tools

| Area | Tools |
|------|-------|
| 🔍 RAG & Search | Keyword (TF-IDF), dense vector, hybrid search, query rewriting, reranking |
| 🧬 Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| ⚖️ Reranking | Cross-encoder (ms-marco-MiniLM-L-6-v2) |
| 🤖 LLMs | OpenAI GPT, Google Gemini |
| 📥 Data Ingestion | dlt (data load tool) |
| 🗃️ Vector Store | Local indices |
| 🎯 Evaluation | HitRate, MRR, LLM-as-a-Judge |
| 📊 Monitoring | SQLite logging, Grafana |
| 🔌 Interface | FastAPI, Streamlit |
| 🐍 Language | Python |

## 📝 Homework

All homework solutions are at the repository root:

| 📋 Homework | 📌 Topic | 🔗 Solution |
|----------|-------|----------|
| 2 | Vector Search | [HomeW2.md](HomeW2.md) |
| 3 | Orchestration (Kestra) | [HW_3.md](HW_3.md) |
| 4 | Evaluation | [hw_4.md](hw_4.md) |
| 5 | Monitoring | [hw_5.md](hw_5.md) |
| 💡 Workshop | Data Ingestion with dlt | [dlt_workshop.md](dlt_workshop.md) |

## 🎓 Final Project — SlideSense AI

An end-to-end **multimodal RAG** project that lets users ask grounded questions over slide decks and images, with citations, evaluation, and monitoring.

**[📄 Full Project README →](slidesense-ai/README.md)**

### 🔄 Pipeline Architecture

```
🖼️ Slides & Images ──► 📥 Ingestion ──► ✂️ Chunking + Metadata ──► 🗃️ Indexing (TF-IDF + Dense)
       ──► ✍️ Query Rewrite ──► 🔍 Hybrid Retrieval ──► ⚖️ Reranking ──► 🤖 RAG Answer + Citations
       ──► 🔌 FastAPI / Streamlit ──► 📊 Feedback Logging ──► 📈 Evaluation + Dashboard
```

### ✨ Key Features

- 📥 **Multimodal Ingestion** — Downloads slide decks and image assets; dlt-driven pipeline
- 🔍 **Hybrid Retrieval** — Combines TF-IDF and dense vector similarity
- ✍️ **Query Rewriting** — Heuristic or LLM-based rewrite to improve retrieval intent
- ⚖️ **Cross-Encoder Re-ranking** — Improves precision on top candidates (with fallback)
- 🎯 **Grounded Generation** — Answers with source chunk citations
- 🔌 **FastAPI + Streamlit** — REST API for integration and interactive UI for demos
- 📊 **Monitoring** — Logs query/response telemetry and user feedback (SQLite + Grafana)
- 📈 **Evaluation** — HitRate & MRR across retrieval variants; LLM-as-judge for answer quality

### 🏆 Results

- 🥇 **Best retrieval config:** `hybrid_rewrite_rerank` — HitRate@5 = 1.0000, MRR@5 = **0.9815**
- 🥇 **Best LLM prompt strategy:** `default` — Faithfulness 5.0, Relevance 5.0, Completeness 5.0

### 🚀 Quick Start

```bash
cd slidesense-ai
pip install -e .
cp .env.example .env
python -m ingestion.pipeline        # dlt pipeline: download, process, index
uvicorn api.main:app --reload --port 8000     # API
streamlit run src/ui/app.py                    # UI
```

## 📁 Repository Structure

```
.
├── 🎓 slidesense-ai/               # Final project — SlideSense AI multimodal RAG
│   ├── src/                        #   Ingestion, retrieval, RAG, API, UI, eval, monitoring
│   ├── data/                       #   Raw & processed datasets, indices, evaluation outputs
│   ├── 📊 dashboards/              #   Grafana starter dashboard
│   ├── 📚 docs/                    #   Monitoring schema & documentation
│   ├── ⚙️ scripts/                 #   PowerShell pipeline runner
│   └── 🐳 docker-compose.yml       #   Containerized services
├── 📝 HomeW2.md                    # Homework 2 — Vector Search
├── 📝 HW_3.md                      # Homework 3 — Orchestration (Kestra)
├── 📝 hw_4.md                      # Homework 4 — Evaluation
├── 📝 hw_5.md                      # Homework 5 — Monitoring
├── 📝 dlt_workshop.md              # Workshop — Data Ingestion with dlt
└── 📖 README.md
```

## 🙏 Acknowledgements

Thanks to [Alexey Grigorev](https://linkedin.com/in/agrigorev) and the entire [DataTalks.Club](https://datatalks.club/) team for offering this incredible course for free. Special thanks to all the instructors and the community on Slack for their support throughout the cohort. ❤️
