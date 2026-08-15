# DevPulse 🔔

> Ask natural-language questions about software release notes — and get grounded,
> version-cited answers.

DevPulse is an agentic RAG application built for the
[LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp) capstone. It ingests
the GitHub release notes of 10 popular open-source tools, indexes them for hybrid
search, and answers questions through a Pydantic AI agent with full observability.

## Problem

Developers depend on dozens of open-source tools that ship updates weekly. Nobody
reads every changelog, but missing a breaking change causes production incidents.
DevPulse turns ~1,800 release notes into a queryable knowledge base:

- *"What breaking changes were in React 19?"*
- *"What did uv improve about lockfile resolution recently?"*
- *"What's new in Docker Compose that affects networking?"*

Unlike a basic FAQ bot, the agent **decides which project to search**, runs
**multiple targeted searches** when needed, and **cites the exact release version**
for every fact. A Kestra flow refreshes the knowledge base weekly, so answers track
the latest releases.

## Screenshots

| Chat | Monitoring dashboard |
|---|---|
| ![Chat](images/chat.png) | ![Dashboard](images/dashboard.png) |

## Architecture

```
GitHub Releases API  (10 repos: Node.js, React, Next.js, Docker Compose, uv,
        │             Prisma, Supabase, Vite, TypeScript, Deno)
        ▼
ingestion/fetch_releases.py ──► data/raw_releases.json
        ▼
ingestion/pipeline.py (dlt) ──► data/devpulse.duckdb
        ▼
indexing/build_index.py
    ├── chunking: gitsource.chunk_documents (1500 chars, 750 overlap) → 13.6k chunks
    ├── minsearch text index (content + version, keyword filter on project)
    └── vector index: ONNX all-MiniLM-L6-v2 embeddings
        ▼
Pydantic AI agent (agent/agent.py, LLM: Ollama gemma4:31b-cloud)
    ├── tool: search_releases
    │     1. LLM query rewriting  → keyword-rich search query
    │     2. hybrid search        → text + vector fused with RRF (top 10)
    │     3. reranking            → ONNX cross-encoder ms-marco-MiniLM (top 5)
    └── tool: list_projects
        ▼
Streamlit app (app/streamlit_app.py)
    ├── 💬 Ask        — chat with citations, 👍/👎 feedback per answer
    └── 📊 Monitoring — 6 charts + metrics over OpenTelemetry spans
        ▼
OpenTelemetry ──► SQLite (monitoring/traces.db: spans + feedback)

Kestra (kestra/weekly_refresh.yaml, every Monday 00:00 UTC)
    └── fetch → dlt pipeline → rebuild indexes   (Docker task runner,
        runs in the dev-pulse-app image with host-mounted data dirs)
```

## Dataset

Fetched live from the public
[GitHub Releases API](https://docs.github.com/en/rest/releases/releases)
(no auth required; a `GITHUB_TOKEN` raises the rate limit). ~1,844 releases with
non-empty bodies across 10 repos; drafts and pre-releases are skipped.
`postgres/postgres`, `golang/go`, and `python/cpython` were considered but
excluded — they tag releases without publishing release-note bodies.

## Evaluation

Full details, methodology, and commentary: [evaluation/results.md](evaluation/results.md).
Ground truth: 153 LLM-generated Q&A pairs, stratified across projects
(committed as [ground_truth.json](evaluation/ground_truth.json)).

**Retrieval** (hit rate / MRR @5, unfiltered — best method is used in production):

| Method | Hit Rate | MRR |
|---|---|---|
| Text (minsearch) | 0.621 | 0.513 |
| Vector (MiniLM) | 0.510 | 0.356 |
| Hybrid (RRF) | 0.706 | 0.575 |
| **Hybrid + rerank** | **0.745** | **0.612** |

**LLM (LLM-as-a-judge, 50 questions × 2 prompt variants):** the basic prompt won
(86% relevant vs 74%) — the "conservative" citation-heavy variant refused to answer
whenever retrieval missed the exact release. The winner is the production prompt;
the surprise and its analysis are written up in results.md.

## Monitoring

Every agent run and search is traced with OpenTelemetry into SQLite
(custom `SpanExporter`). The Streamlit **Monitoring** tab shows: requests/hour,
latency by span type, token usage over time, estimated cost per call, search
result distribution, and 👍/👎 user feedback — collected per answer in the chat
tab and stored alongside the traces.

## Running locally

Prerequisites: [uv](https://docs.astral.sh/uv/),
[Ollama](https://ollama.com) (with a chat model available), and ~2 GB of disk.

```bash
cd dev-pulse
cp .env.example .env                      # adjust model/endpoint if needed

uv sync                                   # install dependencies
uv run python indexing/download.py        # ONNX models (embedder + reranker)

uv run python ingestion/fetch_releases.py # GitHub → data/raw_releases.json (~2 min)
uv run python ingestion/pipeline.py       # dlt → data/devpulse.duckdb
uv run python indexing/build_index.py     # chunk + embed + index (~5 min, CPU)

uv run streamlit run app/streamlit_app.py # http://localhost:8501
```

Environment variables (`.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible LLM endpoint (Ollama) |
| `OPENAI_API_KEY` | `ollama` | API key (any value for local Ollama) |
| `OLLAMA_MODEL` | `gemma4:31b-cloud` | Chat model for agent, rewriting, judging |
| `GITHUB_TOKEN` | *(unset)* | Optional: raises GitHub rate limit to 5000/hr |

Evaluation (optional, reproduces results.md):

```bash
uv run python evaluation/generate_ground_truth.py   # ~5 min
uv run python evaluation/evaluate_retrieval.py      # ~3 min
uv run python evaluation/evaluate_rag.py            # ~25 min
```

## Running with Docker Compose

```bash
cd dev-pulse
uv run python indexing/download.py   # models are volume-mounted, not baked in
docker compose up -d --build
```

- **App**: http://localhost:8501 (reaches the host's Ollama via `host.docker.internal`)
- **Kestra**: http://localhost:8080 (login `admin@kestra.io` / `Admin1234!`)

Generated state (`data/`, `indexing/saved/`, `indexing/models/`, `monitoring/`)
is bind-mounted, so the app, ad-hoc local runs, and Kestra executions all share it.
If you haven't run the local pipeline yet, trigger the ingestion once (see below)
or run the three ingestion/indexing commands locally first.

### Weekly refresh (Kestra)

Register and trigger the flow (it also runs automatically every Monday 00:00 UTC):

```bash
curl -u "admin@kestra.io:Admin1234!" -X POST \
  -H "Content-Type: application/x-yaml" \
  --data-binary @kestra/weekly_refresh.yaml \
  http://localhost:8080/api/v1/main/flows

curl -u "admin@kestra.io:Admin1234!" -X POST \
  http://localhost:8080/api/v1/main/executions/devpulse/devpulse_weekly_refresh
```

> Note: set `variables.project_dir` in `kestra/weekly_refresh.yaml` to your
> absolute path of `dev-pulse/` — the Docker task runner mounts host paths.

## Project structure

```
dev-pulse/
├── ingestion/        fetch_releases.py (GitHub API), pipeline.py (dlt → DuckDB)
├── indexing/         build_index.py, embedder.py (ONNX), download.py, rerank models
├── agent/            agent.py (Pydantic AI), search.py (hybrid+RRF), rerank.py
├── evaluation/       ground truth, retrieval eval, LLM-as-a-judge, results.md
├── monitoring/       otel_setup.py (OTel → SQLite + feedback store)
├── app/              streamlit_app.py (chat + dashboard)
├── kestra/           weekly_refresh.yaml
├── docker-compose.yml, Dockerfile
└── data/, indexing/saved/, indexing/models/   (generated, gitignored)
```

## Technologies

Ollama (gemma4:31b-cloud) · Pydantic AI · minsearch · ONNX Runtime
(all-MiniLM-L6-v2 embeddings, ms-marco-MiniLM cross-encoder) · dlt · DuckDB ·
Kestra · OpenTelemetry · SQLite · Streamlit · Plotly · Docker Compose · uv

## Evaluation criteria checklist

| Criterion | Where |
|---|---|
| Problem description | This README (Problem section) |
| Retrieval flow | Knowledge base (minsearch + vector) + LLM agent (`agent/`) |
| Retrieval evaluation | 4 methods compared, best (hybrid+rerank) used — `evaluation/results.md` |
| LLM evaluation | 2 prompts, LLM-as-a-judge, best used — `evaluation/results.md` |
| Interface | Streamlit UI (`app/streamlit_app.py`) |
| Ingestion pipeline | Automated: dlt (`ingestion/pipeline.py`) + Kestra schedule |
| Monitoring | 👍/👎 feedback collected + 6-chart OTel dashboard |
| Containerization | `docker-compose.yml`: app + Kestra + Postgres |
| Reproducibility | This README, `.env.example`, `uv.lock`, committed ground truth, model download script |
| Hybrid search (bonus) | Text + vector fused with RRF (`agent/search.py`) |
| Document re-ranking (bonus) | ONNX cross-encoder (`agent/rerank.py`) |
| Query rewriting (bonus) | LLM rewrite before search (`agent/search.py`) |
