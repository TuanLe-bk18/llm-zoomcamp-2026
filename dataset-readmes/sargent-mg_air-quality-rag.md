# Air Quality RAG Assistant

An LLM-powered RAG (Retrieval-Augmented Generation) assistant for querying air quality data across Mexican cities. Built as the capstone project for the [DataTalks LLM Zoomcamp 2026](https://github.com/DataTalksClub/llm-zoomcamp).

> **This repo is the RAG/LLM serving layer only.** It does not ingest or transform any air quality data itself — it *reads* pre-built BigQuery mart tables (`air_quality_marts.fct_city_daily_aqi`, `dim_stations`). All extraction (dlt) and transformation (dbt) happens in a separate, upstream repo: **[air-quality-dlt-dbt-dagster](https://github.com/sargent-mg/air-quality-dlt-dbt-dagster)**. You need that pipeline populating BigQuery before anything here will have data to summarize/embed.

---

## Demo

![Chat demo](docs/images/chat_demo.gif)

---

## Architecture

```
[air-quality-dlt-dbt-dagster — separate repo]
  dlt extract → dbt transform → BigQuery: air_quality_marts
                                        │
════════════════════════════════════════│═══ this repo starts here (read-only) ═══
                                         ▼
                    BigQuery (fct_city_daily_aqi + dim_stations)
                                         │
                                         ▼ Dagster: generate_summaries
                          6,596 natural language summaries
                                         │
                                         ▼ Dagster: embed_chunks (OpenAI text-embedding-3-small)
                                 pgvector (PostgreSQL)
                                         │
                                  ┌──────┴──────┐
                              Semantic       Hybrid (vector + BM25 RRF)
                                  └──────┬──────┘
                                         │
                                         ▼
                                   GPT-4o-mini
                                         │
                                         ▼
                          FastAPI ──► Next.js chat UI
                                         │
                                         ▼
                    PostgreSQL (query logs + feedback) ──► Grafana
```

---

## Stack

| Layer | Tool |
|---|---|
| Data source | BigQuery (`air_quality_marts`, populated by the [upstream ETL repo](https://github.com/sargent-mg/air-quality-dlt-dbt-dagster)) |
| Orchestration | Dagster (monthly schedule) |
| Summarization | Python — daily + monthly text chunks |
| Embedding | OpenAI `text-embedding-3-small` (1536 dims) |
| Vector store | pgvector (PostgreSQL) |
| Retrieval | Semantic + Hybrid (vector + BM25 via RRF) |
| LLM | OpenAI `gpt-4o-mini` |
| API | FastAPI |
| Frontend | Next.js + Tailwind CSS |
| Monitoring | Grafana + PostgreSQL |
| Containerization | Docker Compose |

---

## Data

6,596 text chunks generated from BigQuery mart tables (produced by the [upstream ETL repo](https://github.com/sargent-mg/air-quality-dlt-dbt-dagster), not by this one):
- **6,097 daily summaries** — one per city × parameter × date
- **499 monthly summaries** — one per city × parameter × month

Example chunk:
> "In 2024-01, Metepec recorded monthly PM25 levels averaging 30.3 µg/m³ (peak: 77.0, low: 10.0). There were 16 active monitoring days with 340 total readings and 88.5% average coverage. WHO guidelines were exceeded on 16 of 16 days (100.0% of the month)."

---

## Project Structure

```
air-quality-rag/
├── backend/            # FastAPI
│   ├── main.py          # App entrypoint + CORS
│   ├── config.py        # Settings
│   ├── database.py      # PostgreSQL connection
│   ├── models.py        # Pydantic models
│   └── routers/
│       ├── chat.py       # RAG endpoint
│       └── feedback.py   # Feedback endpoint
├── embeddings/
│   ├── summarizer.py    # BigQuery → text chunks
│   ├── embedder.py      # Chunks → pgvector
│   └── indexer.py       # Semantic + hybrid retrieval
├── evaluation/
│   ├── retrieval_eval.py # Semantic vs hybrid comparison
│   └── llm_eval.py       # LLM-as-judge evaluation
├── orchestration/       # Dagster
│   ├── assets.py         # generate_summaries + embed_chunks
│   └── definitions.py    # Job + monthly schedule
├── frontend/            # Next.js chat UI
├── infrastructure/
│   ├── docker-compose.yml # pgvector + Grafana + API
│   ├── init.sql           # Schema
│   └── grafana/           # Dashboard provisioning
├── Dockerfile           # FastAPI container
└── pyproject.toml
```

---

## Setup

### Prerequisites

- Python 3.11 + [uv](https://docs.astral.sh/uv/)
- Docker
- Node.js 18+
- OpenAI API key
- GCP service account with BigQuery read access
- **Air quality data already loaded into BigQuery** (`air_quality_marts` dataset). This repo does not populate that dataset — run the [air-quality-dlt-dbt-dagster](https://github.com/sargent-mg/air-quality-dlt-dbt-dagster) pipeline first.

### 1. Clone and install

```bash
git clone https://github.com/sargent-mg/air-quality-rag
cd air-quality-rag
uv sync
```

### 2. Configure environment

```bash
cp infrastructure/.env.example infrastructure/.env
# Fill in: OPENAI_API_KEY, GOOGLE_APPLICATION_CREDENTIALS, GCP_PROJECT_ID
```

### 3. Start infrastructure

```bash
cd infrastructure
docker compose up -d
cd ..
```

### 4. Run the embedding pipeline (Dagster)

Requires the BigQuery marts from the [upstream ETL repo](https://github.com/sargent-mg/air-quality-dlt-dbt-dagster) to already exist.

```bash
GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json" \
uv run dagster dev -m orchestration.definitions --port 3002
```

Open `http://localhost:3002` → **Materialize all**

Or run via CLI:

```bash
GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json" \
uv run dagster asset materialize -m orchestration.definitions --select "*"
```

### 5. Start the API

```bash
# Via Docker (recommended)
cd infrastructure && docker compose up -d api

# Or local development
uv run uvicorn backend.main:app --reload --port 8000
```

### 6. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`

### 7. Grafana monitoring

Open `http://localhost:3001` (admin/admin)

![Grafana dashboard](docs/images/grafana_dashboard.jpg)

---

## Evaluation

### Retrieval evaluation (semantic vs hybrid)

```bash
uv run python -m evaluation.retrieval_eval
```

| Metric | Semantic | Hybrid |
|---|---|---|
| Hit@1 | 50% | 75% |
| Hit@3 | 50% | 75% |
| Hit@5 | 50% | 75% |
| Avg latency | 565ms | 776ms |

### LLM-as-judge evaluation

```bash
uv run python -m evaluation.llm_eval
```

| Metric | Score |
|---|---|
| Avg Overall | 4.0 / 5 |
| Avg Relevance | 4.0 / 5 |
| Avg Accuracy | 4.8 / 5 |

---

## Example queries

- "Which cities had the worst PM2.5 in January 2024?"
- "How does Guadalajara's ozone compare to WHO guidelines?"
- "What is the air quality situation in Aguascalientes?"
- "Which pollutant had the most WHO exceedances?"
- "Is it safe to exercise outdoors in Monterrey?"

---

## Related repos

- **[air-quality-dlt-dbt-dagster](https://github.com/sargent-mg/air-quality-dlt-dbt-dagster)** — upstream ETL: dlt extraction + dbt transforms + Dagster orchestration, producing the `air_quality_marts` BigQuery dataset this repo reads from.