# MLOps Docs Agent

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Qdrant](https://img.shields.io/badge/Qdrant-vector%20search-DC244C?logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-gpt--5.4--mini-412991?logo=openai&logoColor=white)](https://openai.com/)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-tracing-425CC7?logo=opentelemetry&logoColor=white)](https://opentelemetry.io/)
[![Kestra](https://img.shields.io/badge/Kestra-orchestration-8405FF)](https://kestra.io/)
[![dlt](https://img.shields.io/badge/dlt-ingestion-1BA1E2)](https://dlthub.com/)
[![Arize Phoenix](https://img.shields.io/badge/Arize%20Phoenix-observability-6B4FBB)](https://arize.com/docs/phoenix)

An agent that answers questions about **MLflow** (experiment tracking, model registry, deployment) and **Feast** (feature store, feature engineering) by retrieving from their real, official documentation — not from the model's own (possibly outdated) training data.

Built as the capstone project for [LLM Zoomcamp 2026](https://github.com/DataTalksClub/llm-zoomcamp) by DataTalksClub.

> **Status**: the full pipeline (ingestion → indexing → agent → UI → monitoring) is built, running, and verified live in the browser, including both the retrieval evaluation and the LLM-as-judge prompt evaluation.

## Demo

<video src="assets/demo.mp4" controls width="700"></video>

## Problem

Engineers using MLflow or Feast often ask an LLM chat assistant general questions about these tools. A generic assistant either hallucinates plausible-but-wrong API details, or its training data is stale relative to the current docs. This project builds a small agent that always grounds its answers in the current MLflow/Feast documentation, retrieved live from each source rather than relying on the model's memory.

## Dataset

Scraped directly from the projects' own GitHub repos (not the DataTalksClub course FAQ):

| Source | Repo | Paths included | Docs | Chunks |
|---|---|---|---|---|
| MLflow | [`mlflow/mlflow`](https://github.com/mlflow/mlflow) | `docs/docs/classic-ml/` | 63 | 1002 |
| Feast | [`feast-dev/feast`](https://github.com/feast-dev/feast) | `docs/getting-started/`, `docs/how-to-guides/`, `docs/reference/`, `docs/specs/` | 188 | 1703 |

Both repos have far more docs than this (562 files combined across all subfolders); the paths above were deliberately scoped to the "MLOps / feature engineering" subset relevant to this project (excluding e.g. MLflow's `genai/`/`prompts/` sections and Feast's `blog/`/`roadmap.md`/`community.md`).

## Architecture

```
GitHub (mlflow/mlflow, feast-dev/feast)
        │  dlt resource (incremental by file SHA)
        ▼
   DuckDB (raw docs + section-aware chunks)
        │  orchestrated by a Kestra flow
        ▼
  FastEmbed (dense: all-MiniLM-L6-v2, sparse: Qdrant/bm25)
        │
        ▼
   Qdrant (2 collections: mlflow_docs, feast_docs)
        │  hybrid search (native RRF fusion) + cross-encoder reranking
        ▼
pydantic-ai Agent (gpt-5.4-mini)
  ├─ tool: search_mlflow_docs
  └─ tool: search_feast_docs
        │  OpenTelemetry spans (agent run / tool calls / LLM calls)
        ├──────────────────────────────┐
        ▼                              ▼
   Postgres (schema `app`:       Arize Phoenix (bonus, self-hosted;
   spans + user feedback;        OpenInference-enriched trace view)
   schema `kestra`: state)
        │                              │
        └──────────────┬───────────────┘
                        ▼
   Streamlit (Chat tab + Monitoring tab, 5 charts —
   backend picked by config/observability.toml)
```

**How data flows through the system, stage by stage:**

1. **Ingestion** (`ingestion/github_docs.py`) — a `dlt` resource lists every file in the MLflow and Feast doc repos via GitHub's Git Trees API (one call per repo), then fetches only the files whose content hash (blob SHA) changed since the last run. Unchanged files are skipped entirely — not re-downloaded, not re-diffed locally.
2. **Chunking** (`ingestion/chunking.py`) — each fetched page is split on Markdown `##`/`###` headings rather than a blind fixed-size window, so each chunk is a complete section with its own heading and context. A 2000-character sliding-window fallback only kicks in for unusually long sections.
3. **Orchestration** (`kestra/flows/ingest-docs.yml`) — a Kestra flow wraps the dlt script as a scheduled, observable task instead of reimplementing the fetch logic as native Kestra tasks.
4. **Embedding & indexing** (`search/qdrant_index.py`, `search/embeddings.py`) — every chunk gets two vector representations via FastEmbed: a dense embedding (`all-MiniLM-L6-v2`, captures meaning/paraphrase) and a sparse BM25 vector (`Qdrant/bm25`, captures exact keyword/term matches). Both live on the same Qdrant point, in one of two collections (`mlflow_docs`, `feast_docs`) — one per source, so a query can never accidentally surface results from the other.
5. **Retrieval** (`search/retrieval.py`) — a query can run in three modes: text-only (sparse), vector-only (dense), or hybrid (Qdrant's native Reciprocal Rank Fusion, combining both rankings in one request). The agent uses hybrid — see [Retrieval evaluation results](#retrieval-evaluation-results) for the measured comparison. A cross-encoder reranker (`Xenova/ms-marco-MiniLM-L-6-v2`) then re-scores the top candidates for extra precision.
6. **The agent** (`agent/build.py`, `agent/tools.py`) — a `pydantic-ai` agent (`gpt-5.4-mini`) exposes two tools, `search_mlflow_docs` and `search_feast_docs`. It decides on its own, per question, which tool(s) to call — there is no manual keyword-based routing. Each tool's results (source paths and URLs included) become the context the final answer is grounded in.
7. **Observability** (`observability/tracing.py`) — `pydantic-ai`'s native OpenTelemetry instrumentation emits spans for the agent run, each tool call, and each underlying LLM call automatically, with no function-by-function hand-wrapping. Every span dual-exports: synchronously to a Postgres `app` schema (sharing the same database instance as Kestra's own `kestra` schema — this is the required, always-on path the Monitoring tab defaults to), and asynchronously (batched, non-blocking) to a self-hosted [Arize Phoenix](https://arize.com/docs/phoenix) instance, enriched with [OpenInference](https://github.com/Arize-ai/openinference) semantic conventions for a richer per-trace view (structured input/output messages, retrieved-document detail) than the hand-rolled Postgres charts attempt to show. Phoenix is additive — a bonus layer, not a replacement.
8. **Interface** (`app/chat_tab.py`, `app/monitoring_tab.py`) — a Streamlit app with a Chat tab (question → answer → which tool(s) were consulted → 👍/👎 feedback, duplicated to both Postgres and Phoenix) and a Monitoring tab (the same 5 charts, rebuilt against either backend — chosen by `config/observability.toml`, not an env var or in-app toggle — plus a link to Phoenix's own trace-exploration UI).

**Key design decisions and alternatives considered:**

- **Qdrant over Chroma/Elasticsearch**: Qdrant's Query API supports native sparse (BM25) + dense vectors with built-in RRF fusion in a single call — no need to bolt a separate keyword-search engine (like minsearch or Elasticsearch) onto a vector-only store like Chroma.
- **dlt + Kestra together**: dlt handles incremental fetch/state (by GitHub file SHA) directly in Python; Kestra wraps it as a scheduled, observable flow rather than a bare cron job, without reimplementing the fetch logic as native Kestra tasks.
- **Postgres over a dedicated tracing SaaS** (e.g. Logfire): self-hosted Logfire is Enterprise-only and requires Kubernetes; a locally-owned Postgres instance (already needed for Kestra's own state) keeps monitoring fully reproducible via `docker-compose up`, no external account required. This remains the required, always-on export path.
- **FastEmbed for embeddings/reranking**: keeps dense, sparse, and cross-encoder reranking all local and free — no per-query embedding API cost or added external dependency.
- **Arize Phoenix added as a bonus second backend, not a replacement**: self-hosted (one more `docker-compose` service, no account — same reproducibility bar as the Postgres decision above), so it doesn't reintroduce the account/infra problems that ruled out Logfire/SigNoz/Grafana in the first place. It's additive because it demonstrates a purpose-built LLM-observability tool and gives a richer per-trace view (OpenInference-enriched input/output messages, retrieved-document detail) that the hand-rolled Postgres charts don't attempt — while Postgres stays the required path the Monitoring tab defaults to if Phoenix isn't reachable.

## Evaluation criteria — where to look

| Criterion | Where |
|---|---|
| Problem description | This README, [Problem](#problem) |
| Retrieval flow | `agent/tools.py`, `search/retrieval.py` — knowledge base (Qdrant) + LLM (gpt-5.4-mini), verified live in the browser |
| Retrieval evaluation | `evaluation/run_retrieval_eval.py`, hit_rate/mrr across text/vector/hybrid × 2 sources on 240 generated ground-truth questions — done, see [Retrieval evaluation results](#retrieval-evaluation-results) |
| LLM evaluation | `agent/prompts.py` (2 variants) + LLM-as-judge — done, see [LLM evaluation results](#llm-evaluation-results) |
| Interface | `app/streamlit_app.py` — Streamlit chat + monitoring dashboard, verified live |
| Ingestion pipeline | `ingestion/` (dlt, incremental) + `kestra/flows/ingest-docs.yml` (orchestration) — automated, verified |
| Monitoring | `observability/` (OTel → Postgres, required) + `app/monitoring_tab.py` (5 charts) + feedback capture |
| Containerization | `docker-compose.yml` — app, qdrant, kestra, postgres, phoenix, all one file |
| Bonus | Arize Phoenix as a second, richer observability backend — self-hosted, additive, not required for the Monitoring criterion above (see [Architecture](#architecture) and `design.md`) |
| Reproducibility | See [Setup and running](#setup-and-running) |
| Best practices | Hybrid search (native, evaluated), reranking (cross-encoder, evaluated, on by default), query rewriting (evaluated, off by default — see [Retrieval evaluation results](#retrieval-evaluation-results)) |

## Retrieval evaluation results

240 ground-truth questions generated via structured LLM output (`evaluation/ground_truth.py`, 3 questions per sampled chunk, 40 chunks per source — same pattern as the `llm-zoomcamp-2026` homework repo's HW4). Full numbers in `evaluation/results_retrieval.json`.

**Text vs. vector vs. hybrid** (hit_rate / mrr, 120 questions per source):

| Source | text | vector | hybrid |
|---|---|---|---|
| MLflow | 0.758 / 0.535 | 0.608 / 0.437 | **0.792 / 0.597** |
| Feast | 0.767 / 0.541 | 0.717 / 0.523 | **0.800 / 0.653** |

Hybrid won on both sources — `agent/tools.py:RETRIEVAL_MODE` is set to `hybrid` for both.

**Reranking and query rewriting on/off** (mrr, sample of 30 per source, hybrid mode):

| Config | MLflow mrr | Feast mrr |
|---|---|---|
| baseline | 0.623 | 0.617 |
| + rerank | **0.661** | 0.579 |
| + rewrite | 0.437 | 0.548 |
| + rerank + rewrite | 0.488 | 0.523 |

Reranking is a net win on MLflow and roughly neutral on Feast (hit_rate actually improved there, 0.733 → 0.800), so it's **on by default**. Query rewriting made retrieval *worse* on both sources in every combination — the rewrite prompt is generic across both products, so it tends to inject the wrong product's terminology into the query (e.g. a Feast question getting "MLflow" mixed in), diluting both the sparse (BM25 term-weight dilution) and dense (off-centroid embedding) signals. It also added ~1.3s of extra LLM latency per tool call. It's implemented and evaluated (`search/query_rewrite.py`, togglable via `ENABLE_QUERY_REWRITE=true`) but **off by default**.

## LLM evaluation results

Both system-prompt variants (`agent/prompts.py`) were run against the same 20 sampled questions (10 per source) and scored 1-5 by an LLM judge (`evaluation/run_agent_eval.py`, results in `evaluation/results_agent.json`):

| Variant | Average score | Won / tied |
|---|---|---|
| `concise` | 3.75 | 5/20 |
| **`explicit_citation`** | **4.4** | **15/20** |

`explicit_citation` won decisively and is the shipped default (`agent/prompts.py:DEFAULT_VARIANT`). It also happens to structurally satisfy the `mlops-docs-agent` spec's source-attribution requirement, so this result reinforces rather than overrides that design choice.

## Status / known gaps

**Reproducibility was tested directly**: a clean copy of exactly the files this repo's `.gitignore` would let into a real `git clone` was run through the full documented setup in an isolated Docker project (its own volumes, no reuse of this machine's existing data) — `uv sync` → `docker compose up` → ingestion → indexing → a live agent query — and it worked end to end. That test caught a real bug: dlt's default DuckDB destination path was resolving against the *first-ever* working directory a same-named pipeline had run from (cached outside the repo, in `~/.dlt/pipelines/`), so a second checkout on the same machine would have silently written into the first checkout's database. Fixed in `ingestion/pipeline.py` by pinning both the destination path and `pipelines_dir` to the repo root.

Everything else — ingestion, chunking, embedding, indexing, retrieval (all 3 modes, evaluated), reranking, query rewriting (evaluated, disabled by default), the agent (verified live with real single-source, single-source, and cross-source questions, evaluated prompt), tracing, feedback storage, and the full Streamlit UI — is implemented, evaluated, and verified against the real running stack.

**Performance note**: the first agent question after a fresh container start takes ~25-30s (FastEmbed downloading/verifying its dense/sparse/reranker models from Hugging Face Hub). This is a one-time cost per Docker volume — `docker-compose.yml` mounts a persistent `fastembed_cache` volume so it only happens once, not on every container restart. Warm-cache questions take ~8-9s end-to-end (routing LLM call ~1.3s, Qdrant search ~0.5s, reranking ~3.3s, answer-synthesis LLM call ~2.5s — see the Monitoring tab for live numbers).

## Setup and running

Requirements: Docker, [uv](https://docs.astral.sh/uv/), and an OpenAI API key.

The project has two phases that have to happen in order: **start the infrastructure** (Postgres, Qdrant, Kestra, the Streamlit app container), then **populate it with data** (fetch the docs, embed them, index them into Qdrant). The Streamlit app never fetches or embeds anything itself — it only ever reads from Qdrant and Postgres — so it will start fine but have nothing to answer with until step 5 finishes.

1. **Clone the repo and provide your OpenAI key.** Either export it directly:
   ```bash
   export OPENAI_API_KEY=sk-...
   ```
   or, if you use 1Password, adapt `.envrc`/`scripts/start-stack.sh` (they currently read from `op://Personal/OpenAIDataTalk/credential`) and run `direnv allow`.

2. **Install Python dependencies.**
   ```bash
   uv sync
   ```
   Creates a local `.venv` with everything needed to run the ingestion/indexing scripts from your machine. Not strictly required just to chat with the app once it's populated (the `app` container installs its own copy at build time) — but needed for steps 4 and 5 below.

3. **Start the infrastructure.**
   ```bash
   ./scripts/start-stack.sh
   ```
   This script resolves your OpenAI key, base64-encodes it into Kestra's secret store (Kestra requires base64-encoded secrets), and runs `docker compose up -d --build`. Five services come up: `postgres` (with two schemas already created — `kestra` for orchestration state, `app` for traces/feedback), `qdrant` (empty, no collections yet), `kestra` (with the ingestion flow auto-loaded from `kestra/flows/`), `phoenix` (self-hosted Arize Phoenix, empty until you ask a question — see [Architecture](#architecture)), and `app` (Streamlit — reachable, but with nothing to answer yet). Streamlit: http://localhost:8501. Kestra UI: http://localhost:8080 (`admin@kestra.io` / `Admin1234!`). Phoenix UI: http://localhost:6006 (also linked from the Monitoring tab).

4. **Fetch and chunk the documentation.**
   ```bash
   uv run python -m ingestion.pipeline
   ```
   Lists every file in the MLflow/Feast doc repos, fetches only the ones that changed (by GitHub blob SHA), splits them into section-aware chunks, and writes everything to a local `mlops_docs_ingest.duckdb` file. A first run fetches ~250 files and takes a few minutes; later runs only re-fetch files that actually changed upstream. Alternative: trigger the same script from Kestra instead of your terminal — the flow `kestra/flows/ingest-docs.yml` runs it inside a container; either use the Kestra UI or `POST /api/v1/executions/mlops-docs-agent/ingest-docs`, after setting its `repo_host_path` input to wherever you cloned this repo.

5. **Embed and index into Qdrant.**
   ```bash
   uv run python -m search.load_index
   ```
   Reads the chunks from the DuckDB file, computes dense + sparse embeddings for each with FastEmbed, and upserts them into two Qdrant collections (`mlflow_docs`, `feast_docs`). The first run downloads the embedding models (a few minutes, ~25-30s added to your first chat question too); a Docker volume caches them afterward so this cost isn't paid again on container restarts.

6. **Chat.** Open http://localhost:8501 — the Chat tab works as soon as indexing finishes, and the Monitoring tab fills in live as you ask questions. By default it reads from Phoenix (http://localhost:6006, also linked from the tab); switch `monitoring_backend` in `config/observability.toml` to `"postgres"` and restart the `app` container to see the same 5 charts built from the required Postgres path instead.

## Repository structure

```
ingestion/      dlt resource (GitHub → DuckDB) + section-aware chunking
search/         Qdrant collections, hybrid retrieval, reranking, query rewriting
agent/          pydantic-ai agent, tools, system prompts
observability/  OpenTelemetry → Postgres + Phoenix dual export, feedback storage
app/            Streamlit chat + monitoring UI (Postgres- and Phoenix-backed views)
evaluation/     ground-truth generation + retrieval/LLM evaluation (see Status)
kestra/flows/   ingestion orchestration flow
infra/          Postgres init (kestra/app schema separation)
config/         observability.toml — Monitoring tab backend selection
```

## Best practices implemented

- **Hybrid search**: Qdrant's native `Fusion.RRF` combining dense (FastEmbed `all-MiniLM-L6-v2`) and sparse/BM25 (FastEmbed `Qdrant/bm25`) vectors — evaluated against text-only and vector-only per source, hybrid won on both (see [Retrieval evaluation results](#retrieval-evaluation-results)).
- **Reranking**: FastEmbed cross-encoder (`Xenova/ms-marco-MiniLM-L-6-v2`) reorders the top-K hybrid results before they reach the agent — evaluated, on by default.
- **Query rewriting**: implemented and evaluated (`search/query_rewrite.py`), but **disabled by default** — the evaluation showed it regresses retrieval quality on both sources. Togglable via `ENABLE_QUERY_REWRITE=true` for inspection. See [Retrieval evaluation results](#retrieval-evaluation-results).
- **Strict out-of-scope refusal**: manual testing found the agent answering trivia (e.g. "what's the capital of France?") directly from its own knowledge while correctly refusing a technical question about an unrelated tool — an inconsistency, since the original prompt only constrained answers *after* a tool was called. Both system-prompt variants (`agent/prompts.py`) now explicitly require a refusal whenever neither `search_mlflow_docs` nor `search_feast_docs` is called, with no exception for trivia.
- **Post-rerank confidence threshold**: reranked results were previously always forced into an answer regardless of relevance. `agent/tools.py:RERANK_CONFIDENCE_THRESHOLD` (calibrated empirically — in-corpus questions scored 6.17-9.41, clearly out-of-corpus questions scored -9.66 to 3.31) now returns a "no sufficiently relevant results" response below the cutoff instead.
- **Groundedness regression testing**: a custom LLM-as-judge groundedness evaluator (`evaluation/groundedness_eval.py`, same pattern as the prompt-variant judge) plus a 15-question behavioral regression set, run as a native Arize Phoenix Dataset + Experiment (`evaluation/run_regression_eval.py`) rather than a local file — specifically so it populates Phoenix's own Datasets & Experiments UI and future prompt changes can be compared there. Confirmed live: 15/15 refusal-behavior checks passed; 6/9 in-domain answers scored fully grounded (the LLM judge is strict about exact wording, not just topical correctness) — this is the baseline future runs are compared against.

## Known limitations

- The Kestra ingestion flow uses Docker-outside-of-Docker (bind-mounting the repo from the host), so its `repo_host_path` input is machine-specific — see the flow's own description in `kestra/flows/ingest-docs.yml`.
- Chunk text occasionally retains MDX import statements (e.g. `import { APILink } from ...`) at the top of a section; minor noise, not filtered out.
- The shipped system prompt (`agent/prompts.py:DEFAULT_VARIANT`) is the evaluated winner of the LLM-as-judge comparison — see [LLM evaluation results](#llm-evaluation-results).
