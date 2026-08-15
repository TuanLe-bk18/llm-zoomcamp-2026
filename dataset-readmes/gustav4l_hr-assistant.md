# HR Assistant - AI-Powered RAG & Evaluation System

<p align="center">
  <img src="images/uncanny_hr.webp" alt="HR Meme" width="500"/>
</p>

An end-to-end, production-ready Human Resource Assistant powered by Retrieval-Augmented Generation (RAG) and Hybrid Search. It provides factual, policy-grounded answers to employee questions with zero hallucination, complete OpenTelemetry observability, user feedback collection, operational metric alerts, and an offline evaluation pipeline.

---

## Problem Statement

Employees often struggle to quickly find accurate information buried across lengthy company HR policy documents (annual leave rules, sick leave, remote work policies, travel expense limits, code of conduct, etc.).

HR Assistant addresses this challenge by providing:
- Strict Factual Grounding: Answers questions using only retrieved company policy documents.
- Out-of-Domain Refusal: Rules to politely decline non-HR questions (e.g., general trivia, software code).
- Hybrid Search Retrieval: Combines vector similarity (pgvector) and PostgreSQL Full-Text Search (tsvector) via Reciprocal Rank Fusion (RRF).
- Full Observability & Evaluation: OpenTelemetry tracing, user feedback metrics, operational metric alerts, and LLM-as-a-Judge offline evaluation.

---

## System Architecture

```text
                                ┌──────────────────────────┐
                                │      Streamlit UI        │
                                │ (app.py / dashboard.py)  │
                                └────────────┬─────────────┘
                                             │ User Question
                                             ▼
                                ┌──────────────────────────┐
                                │     PydanticAI Agent     │
                                │   (hr_assistant/agent)   │
                                └────────────┬─────────────┘
                                             │ Search Query
                                             ▼
                                ┌─────────────────────────────────┐
                                │       Hybrid Searcher           │
                                │  (hr_assistant/hybrid_search)   │
                                └───────────────┬─────────────────┘
                                                │
                        ┌───────────────────────┴───────────────────────┐
                        ▼                                               ▼
          ┌───────────────────────────┐                   ┌───────────────────────────┐
          │       Vector Search       │                   │     Full-Text Search      │
          │ (hr_assistant/vector_search)                 │ (hr_assistant/text_search)│
          └─────────────┬─────────────┘                   └─────────────┬─────────────┘
                        │ pgvector                                      │ tsvector GIN
                        └───────────────────────┬───────────────────────┘
                                                │ Reciprocal Rank Fusion (RRF)
                                                ▼
                                    ┌──────────────────────┐
                                    │ PostgreSQL Database  │
                                    │  (documents / traces │
                                    │  / feedback / otel_  │
                                    │        spans)        │
                                    └──────────────────────┘
```

---

## Key Features

- Hybrid Search Engine: Merges pgvector cosine similarity and PostgreSQL GIN Full-Text Search using Reciprocal Rank Fusion (RRF).
- User Query Rewriting: Automatically expands HR acronyms (e.g., WFH, PTO, HMO) and cleans noise in search queries.
- Auto-Loaded Optimal Parameters: Loads tuned search weights (vector_weight, text_weight, rrf_k, top_k) directly from data/best_config.json.
- Multi-Turn Chat Interface: Interactive Streamlit application with message memory, expandable source citations, trace badges, and in-app feedback forms.
- Operational Metric Alerts: Real-time alert notifications for operational metrics (high latency, error rate, negative feedback, retrieval hit rate drops).
- Deep RAG Trace Inspector: Interactive trace explorer in the dashboard allowing deep inspection of raw vector distance scores, full-text ts_rank scores, RRF ranking matrix, system prompts, and LLM completions.
- Observability & Telemetry: Custom OpenTelemetry exporter persisting spans directly to PostgreSQL, with latency, token usage, and cost tracking.
- Monitoring Dashboard: 4-tab Streamlit dashboard covering Telemetry KPIs, Retrieval Performance, Agent Evaluation, and User Feedback with interactive charts.
- Complete Evaluation Pipeline: Ground truth generator, Hit Rate & MRR benchmark, Grid Search hyperparameter tuner, and LLM-as-a-Judge pipeline.
- Containerized Setup: Single Docker Compose stack orchestrating PostgreSQL+pgvector, Streamlit Chat App, and Monitoring Dashboard.

---

## Directory Structure

```text
hr-assistant/
├── Makefile                    # Task automation (init_db, ingest, evaluate, start)
├── Dockerfile                  # Application container setup
├── Dockerfile.dashboard        # Dashboard container setup
├── docker-compose.yml          # Docker Compose multi-service orchestration
├── pyproject.toml              # Project dependencies (UV package manager)
│
├── hr_assistant/               # Core Python package & Streamlit UIs
│   ├── __init__.py             # Package marker
│   ├── app.py                  # Streamlit conversational chat application
│   ├── dashboard.py            # Telemetry, evaluation, alerts & feedback dashboard
│   ├── agent.py                # PydanticAI agent workflow & tools
│   ├── chat_service.py         # Streamlit chat application service module
│   ├── metrics_service.py      # Dashboard telemetry & metric alert service module
│   ├── db.py                   # PostgreSQL connection manager
│   ├── embedder.py             # LightEmbed embedding model wrapper
│   ├── text_search.py          # PostgreSQL Full-Text Search retrieval
│   ├── vector_search.py        # pgvector cosine similarity retrieval
│   ├── hybrid_search.py        # Hybrid Searcher with RRF & query rewriting
│   ├── feedbacks.py            # User feedback persistence & stats
│   ├── judge.py                # Online LLM relevance evaluator module
│   └── tracer.py               # OpenTelemetry PostgreSQL span exporter
│
├── scripts/                    # Database & Ingestion utilities
│   ├── db_init.py              # PostgreSQL schema & pgvector index initializer
│   ├── ingest.py               # Document embedding & database ingestion
│   └── policy.py               # Synthetic policy dataset generator
│
├── evaluation/                 # Offline Evaluation Pipeline
│   ├── generate_ground_truth.py# Ground truth Q&A dataset generator
│   ├── retrieval_eval.py       # Hit Rate & MRR evaluation
│   ├── tune_retrieval.py       # Grid Search hyperparameter optimizer
│   ├── agent_eval.py           # Agent execution & trajectory recorder
│   └── llm_judge.py            # LLM-as-a-Judge answer & trajectory evaluator
│
├── images/                     # Media & assets
│   └── uncanny_hr.webp
│
└── data/                       # Evaluation artifacts & dataset storage
    ├── policies.csv            # HR policy corpus (40 documents)
    ├── ground_truth.csv        # 200 evaluation Q&A pairs
    ├── retrieval_results.csv   # Detailed retrieval evaluation metrics
    ├── tuning_results.csv      # Hyperparameter tuning evaluation log
    ├── best_config.json        # Production retrieval configuration
    ├── predictions.csv         # Agent outputs & search trajectories
    └── judge_results.csv       # LLM judge scores & reasoning
```

---

## Quick Start (Docker Compose)

Running via Docker Compose launches PostgreSQL with `pgvector`, the Chat Application, and the Monitoring Dashboard automatically.

1. Clone Repository & Setup Environment Variables:

```bash
git clone https://github.com/gustav4l/hr-assistant.git
cd hr-assistant
cp .env.example .env
```

Set your `OPENAI_API_KEY` in `.env` (use `POSTGRES_HOST=localhost` for running scripts locally on host, or `POSTGRES_HOST=postgres` inside containers):

```env
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
```

2. Start the Docker Stack:

```bash
docker compose up -d --build
```

3. Initialize Database & Ingest Documents:

```bash
make init_db
make ingest
```

4. Open Applications in Browser:

- HR Assistant Chat App: http://localhost:8501
- Observability & Evaluation Dashboard: http://localhost:8502

---

## Offline Evaluation Pipeline

Run the complete 5-stage evaluation pipeline:

```bash
make evaluate
```

Or run each evaluation script individually:

```bash
uv run python -m evaluation.generate_ground_truth
uv run python -m evaluation.retrieval_eval
uv run python -m evaluation.tune_retrieval
uv run python -m evaluation.agent_eval
uv run python -m evaluation.llm_judge
```

---

## Benchmark Results

Evaluation results across 200 ground-truth questions (5 Qs x 40 Policies):

### Retrieval Strategy Comparison

| Retrieval Method | Hit Rate | MRR | Analysis / Notes |
| :--- | :---: | :---: | :--- |
| **Full-Text Search** (`tsvector` GIN) | **93.50%** | 0.8183 | Weighted field boosting (title > category > department > policy) with OR-based matching |
| **Vector Search** (`pgvector` cosine) | **98.00%** | 0.8962 | High semantic matching capability for natural language queries |
| **Hybrid Search** (RRF Vector + Text) | **99.00%** | **0.9464** | Best overall performance, combining semantic depth with exact keyword fallback |

### End-to-End System Benchmark

| Metric | Benchmark Result |
| :--- | :---: |
| Ground Truth Dataset | 200 samples (5 Qs x 40 Policies) |
| Selected Retriever | Hybrid Search (RRF) |
| Optimal Retriever Hit Rate | 99.00% (198 / 200 Hits) |
| Optimal Retriever MRR | 0.9464 |
| LLM Judge Answer Accuracy | 84.0% (168 / 200 Good) |
| LLM Judge Trajectory Quality | 86.0% (172 / 200 Good) |

---

## Tech Stack

- Framework: PydanticAI
- Database: PostgreSQL 17 + pgvector
- Embedding Model: LightEmbed (all-MiniLM-L6-v2, 384 dimensions)
- Web UI & Dashboard: Streamlit
- Observability: OpenTelemetry API/SDK
- LLM: OpenAI gpt-4o-mini
- Dependency Management: uv

---

## License

This project is licensed under the MIT License.
