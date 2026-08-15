# XAI Daily Digest

A RAG application that gives you a daily digest of advancements in **explainable / interpretable AI (XAI)** (mechanistic interpretability, feature attribution, model transparency, and related alignment-adjacent research), sourced from **arXiv** and the research publications of **Anthropic** and **OpenAI**.

Built as the capstone project for [DataTalksClub's LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp/blob/main/project.md).

## Demo

![Demo of the XAI Daily Digest app](assets/XAI_research_assistant.gif)

## Problem

Explainability research moves fast and is scattered across arXiv preprints and individual lab blogs (Anthropic Research, OpenAI Research/News), with no single place to track it. This project:

1. **Ingests** new XAI-relevant content daily from three sources: the arXiv API (filtered to interpretability/explainability papers in cs.AI/cs.LG/cs.CL/cs.CV), Anthropic's research index page, and OpenAI's research RSS feed.
2. **Indexes** it into a hybrid (dense + sparse) vector store so it can be searched semantically or by keyword.
3. Lets you **ask questions** about the corpus (RAG, with citations) or **generate a digest** of everything ingested in the last 24 hours.
4. **Evaluates** multiple retrieval strategies and multiple prompt/model variants so the RAG design choices are backed by numbers, not vibes.
5. **Monitors** usage (feedback, latency, ingestion volume) via a Grafana dashboard.

You do not need any LLM Zoomcamp course material to run or evaluate this: it's a standalone app.

## Architecture

```
                     ┌──────────────┐
   arXiv API ───────▶│              │
   Anthropic (HTML) ─▶│  ingestion   │──▶ Postgres (metadata, dedup, logs)
   OpenAI (RSS) ─────▶│  (Prefect)   │──▶ Qdrant (dense + sparse hybrid vectors)
                     └──────────────┘
                                              │
                                              ▼
                                     ┌─────────────────┐
                                     │   rag/ module    │
                                     │ query rewrite →   │
                                     │ hybrid search →   │
                                     │ FlashRank rerank →│
                                     │ OpenAI chat       │
                                     └─────────────────┘
                                              │
                              ┌───────────────┼───────────────┐
                              ▼                                ▼
                    Streamlit app (UI)                 Grafana (monitoring)
                    Digest tab + Ask tab                reads Postgres logs
                    👍/👎 feedback
```

**Ingestion** runs as a [Prefect](https://www.prefect.io/) flow (`ingestion/flow.py`), served on a daily cron schedule (`ingestion/schedule.py`) inside its own container: this is the "orchestration tool" path in the rubric rather than a bare script.

**Retrieval** combines a dense vector (OpenAI `text-embedding-3-small`) and a sparse BM25 vector (via `fastembed`) in a single Qdrant collection, fused with Reciprocal Rank Fusion (**hybrid search**, bonus point), then re-ranked with a local cross-encoder via [FlashRank](https://github.com/PrithivirajDamodaran/FlashRank) (**re-ranking**, bonus point). User questions are also rewritten by the LLM before retrieval to broaden recall (**query rewriting**, bonus point).

## Tech stack

| Concern | Choice |
|---|---|
| LLM | OpenAI (`gpt-4o-mini` default, configurable) |
| Vector DB | Qdrant (hybrid dense+sparse) |
| Metadata / logs | Postgres |
| Orchestration | Prefect (`flow.serve(cron=...)`) |
| Interface | Streamlit |
| Monitoring | Grafana (Postgres datasource, provisioned dashboard) |
| Containerization | Docker Compose |

## Repository layout

```
common/            shared config + Postgres helpers
ingestion/          source fetchers (arXiv/Anthropic/OpenAI), chunking, Prefect flow
rag/                hybrid retrieval, rerank, query rewrite, prompts, digest + QA flows
eval/               golden-set generation, retrieval eval, RAG (LLM-as-judge) eval
app/                Streamlit UI
monitoring/         Postgres schema, Grafana provisioning + dashboard
data/               golden_set.json (generated)
eval/results/       eval output tables (generated)
```

## Setup

### Prerequisites
- Docker + Docker Compose
- An OpenAI API key

### 1. Configure environment

```bash
cp .env.example .env
# edit .env and set OPENAI_API_KEY
```

### 2. Start the infrastructure

```bash
docker compose up -d postgres qdrant grafana
```

Postgres auto-runs `monitoring/db_init.sql` on first start. Wait ~10s for the healthcheck, then confirm:

```bash
docker compose ps
```

### 3. Run ingestion once to populate the corpus

```bash
docker compose run --rm ingestion python -m ingestion.flow
```

This fetches recent XAI-relevant items (last 3 days by default; widen with `ingestion.flow.ingest_xai_content(days_back=30)` for a bigger initial corpus), chunks them, embeds them (dense + sparse), and writes to Postgres + Qdrant. To keep it running on a daily schedule instead:

```bash
docker compose up -d ingestion
```

(it will serve the flow on the cron in `INGESTION_CRON`, default `0 7 * * *` UTC)

### 4. Start the app

```bash
docker compose up -d app
```

Open **http://localhost:8501**. Use the **Ask** tab to query the corpus, or **Daily Digest** to summarize the last 24h of ingestion.

### 5. Monitoring

Open **http://localhost:3000** (login `admin` / value of `GRAFANA_ADMIN_PASSWORD`, default `admin`). The "XAI Daily Digest: Monitoring" dashboard is pre-provisioned and shows ingestion volume by source, feedback over time, answer latency, and retrieval-strategy usage, all populated automatically as you use the app.

> If you change `POSTGRES_PASSWORD`/`POSTGRES_USER`/`POSTGRES_DB` from the `.env.example` defaults, also update `monitoring/grafana/provisioning/datasources/postgres.yml` to match, since Grafana's datasource is provisioned with those defaults baked in.

### Running things locally (without Docker) for development

```bash
python -m venv .venv && source .venv/Scripts/activate  # or .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
# point POSTGRES_HOST/QDRANT_HOST at localhost in .env if running the DBs via
# `docker compose up -d postgres qdrant` but the app/ingestion locally
```

## Evaluation

### Retrieval evaluation

```bash
python -m eval.generate_golden_set     # LLM writes ~60 questions, one per sampled chunk
python -m eval.evaluate_retrieval      # compares vector / hybrid / hybrid+rerank
```

Compares three strategies by Hit Rate@5 and MRR@5 against the golden set: `vector` (dense only), `hybrid` (dense+sparse RRF), `hybrid_rerank` (hybrid + FlashRank cross-encoder rerank). Results are written to [`eval/results/retrieval_eval.md`](eval/results/retrieval_eval.md).

### LLM / prompt evaluation

```bash
python -m eval.evaluate_rag
```

Compares three variants: baseline prompt on `gpt-4o-mini`, a citation-enforcing prompt on `gpt-4o-mini`, and the baseline prompt on `gpt-4o`, using LLM-as-judge scoring (relevance, faithfulness) over a subset of the golden set. Results are written to [`eval/results/rag_eval.md`](eval/results/rag_eval.md).

Both eval scripts require the corpus to already be populated (step 3 above) since the golden set is sampled from ingested chunks.

## Example walkthrough

**Ask tab**, example question: *"What is mechanistic interpretability and how does it differ from feature attribution methods?"*
The app rewrites the query, retrieves the top-k hybrid+reranked chunks from arXiv/Anthropic/OpenAI content, and answers with inline `[1] [2]` citations linking back to the source papers/posts, shown in a "Sources" expander below the answer. Thumbs up/down feedback is logged to Postgres and shows up in Grafana immediately.

**Digest tab**: click "Generate today's digest" to get a themed summary of everything ingested in the last 24 hours, with the same citation + sources treatment.

*(Add screenshots here after your first local run: `docker compose up`, populate data, then capture the Ask tab, Digest tab, and Grafana dashboard.)*

## Known limitations

- **arXiv relevance filtering**: arXiv's search API doesn't reliably AND/OR-group compound field queries, so `ingestion/sources/arxiv_source.py` re-filters every candidate with a keyword relevance check (`ingestion/relevance.py`), the same check used for the Anthropic/OpenAI sources. This is a lightweight heuristic (substring match on interpretability-related terms), so it will occasionally admit a paper that mentions "interpretable" only in passing, or (more rarely) miss one that's on-topic but phrased differently. An LLM-based relevance classifier would be a natural follow-up.
- **Anthropic ingestion** scrapes the public `/research` index page (no RSS is published); if Anthropic changes that page's markup, `ingestion/sources/anthropic_source.py` will need its CSS-class matching updated.
- Only paper/post **abstracts and blog summaries** are ingested, not full PDF/article text: enough for a daily-digest use case, but deep questions about a specific paper's methodology will be limited by what's in the abstract.

## Rubric self-check

| Criterion | Where |
|---|---|
| Problem description | This README, "Problem" section |
| Retrieval flow (KB + LLM) | `rag/qa.py`, `rag/digest.py` |
| Retrieval evaluation (multiple approaches) | `eval/evaluate_retrieval.py` → `eval/results/retrieval_eval.md` |
| LLM evaluation (multiple approaches) | `eval/evaluate_rag.py` → `eval/results/rag_eval.md` |
| Interface | Streamlit app (`app/streamlit_app.py`) |
| Ingestion pipeline (orchestrated) | Prefect flow, `ingestion/flow.py` + `ingestion/schedule.py` |
| Monitoring (feedback + dashboard) | 👍/👎 in app → Postgres → Grafana dashboard |
| Containerization | `docker-compose.yml`, `Dockerfile.app`, `Dockerfile.ingestion` |
| Reproducibility | This README, pinned `requirements.txt`, `.env.example` |
| Hybrid search (bonus) | `rag/retrieval.py::hybrid_search` |
| Re-ranking (bonus) | `rag/retrieval.py::rerank` (FlashRank) |
| Query rewriting (bonus) | `rag/query_rewrite.py` |
