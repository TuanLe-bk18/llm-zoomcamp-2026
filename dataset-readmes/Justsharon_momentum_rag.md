# MomentumRAG

A personal memory RAG system: a retrieval-augmented generation application whose knowledge base is one person's own goals, projects, reflections, and daily check-ins — built to help answer questions like *"what should I focus on today?"* or *"what usually happens after I finish a big goal?"* using your own history instead of generic advice.

**Live demo:** `https://momentum-rag.vercel.app/`
<!-- **Video walkthrough:** `` -->

---

## Problem description

People often lose momentum on long-term goals because the context that would help them get back on track — past plans, blockers, what worked last time — is scattered across notebooks, apps, and memory rather than in one searchable place. This is a common pattern: a period of high output ends, motivation drops, and there's no easy way to look back and ask *"what happened last time I felt like this, and what got me moving again?"*

MomentumRAG addresses this directly. It's a structured personal knowledge base (goals, projects, reflections, daily check-ins) with a retrieval-augmented chat interface on top, so questions about your own history get answered using your own actual notes rather than generic productivity advice. It also tracks two things that motivated this project specifically: daily motivation level and social media relapse — both queryable through the same interface.

This isn't a general-purpose productivity app. It's deliberately scoped as a retrieval system: the value is in retrieval quality, grounded answers, and being able to see patterns across entries — not task management for its own sake.

---

## Evaluation criteria — where to find each one

| Criterion | Where | Notes |
|---|---|---|
| Problem description | This section | — |
| Retrieval flow | [`retrieval.py`](retrieval.py), [`llm.py`](llm.py), [`api.py`](api.py) `/ask` | Vector search (Qdrant) → prompt construction → Groq LLM |
| Retrieval evaluation | [`retrieval_eval.py`](retrieval_eval.py), [`bm25_retrieval.py`](bm25_retrieval.py), [`hybrid_retrieval.py`](hybrid_retrieval.py) | Compares vector-only, BM25-only, and hybrid (RRF) retrieval on Recall@5 / MRR / Precision@5. Hybrid is used in production. |
| LLM evaluation | [`llm_eval.py`](llm_eval.py), [`prompts.py`](prompts.py) | Compares 3 prompt variants (basic / structured / reasoning) using an LLM-as-judge on groundedness, relevance, helpfulness |
| Interface | [`frontend/`](frontend/) + [`api.py`](api.py) | Full web UI (SvelteKit) backed by a FastAPI API |
| Ingestion pipeline | [`ingest.py`](ingest.py) (full batch), [`indexing.py`](indexing.py) (automated incremental) | Every create/edit/delete in the UI triggers automatic background re-indexing — see [Ingestion](#ingestion) below |
| Monitoring | [`api.py`](api.py) `query_logs` + `/feedback`, [`grafana/`](grafana/) | 5-panel Grafana dashboard + thumbs up/down feedback on every answer |
| Containerization | [`docker-compose.yml`](docker-compose.yml), [`Dockerfile.api`](Dockerfile.api), [`frontend/Dockerfile`](frontend/Dockerfile) | Entire stack (Postgres, Qdrant, Grafana, API, frontend) runs via `docker compose up` |
| Reproducibility | [Setup](#setup) below | Pinned dependencies in `requirements.txt`, all config via environment variables, sample seed data included |
| **Best practices** | | |
| — Hybrid search | [`hybrid_retrieval.py`](hybrid_retrieval.py) | Reciprocal Rank Fusion of vector + BM25, evaluated against both individually |
| — Document re-ranking | *Not implemented* | Noted honestly rather than claimed — see [Limitations](#known-limitations--honest-gaps) |
| — Query rewriting | *Not implemented* | Same as above |
| **Bonus** | | |
| — Cloud deployment | Frontend on Vercel, API on Render, Postgres on Neon, vectors on Qdrant Cloud, monitoring on Grafana Cloud | Entirely on free tiers — see [Deployment](#deployment) |

---

## Architecture

```text
User
  │
  ▼
SvelteKit frontend (Vercel)
  │  REST calls
  ▼
FastAPI backend (Render)
  │
  ├──► Postgres / Neon         (goals, projects, reflections, check-ins, query_logs)
  ├──► Qdrant Cloud            (vector search over embedded knowledge-base entries)
  └──► Groq (llama-3.3-70b)    (answer generation)

Grafana Cloud reads query_logs directly from Postgres for monitoring.
```

**Retrieval-augmented flow (`/ask`):**
question → embed query (fastembed, `BAAI/bge-small-en-v1.5`) → vector search in Qdrant → build prompt from retrieved entries → Groq LLM → answer + sources, logged to `query_logs` for monitoring.

---

## Data model

Six knowledge types, each with its own Postgres table, all flattened into a shared `Document` representation for retrieval (see [`model.py`](model.py) and [`documents.py`](documents.py)):

- **Goals** — title, description, why it matters, status, priority, deadline
- **Projects** — objective, current focus, next step, status
- **Reflections** — accomplishments, blockers, lessons, mood/energy (1-10), social media minutes
- **Check-ins** — daily low-friction entry: did-planned-task, motivation level, social media opens, app-reinstall flag
- **Tasks**, **Weekly plans** — modeled, not yet exposed in the UI (see [Limitations](#known-limitations--honest-gaps))

---

## Ingestion

Two paths, both automated (no manual dataset assembly required):

1. **Full batch** (`ingest.py`) — reads every row across all tables, embeds, and rebuilds the entire Qdrant collection. Used for initial setup and bulk changes (e.g. after `seed.py`).
2. **Incremental** (`indexing.py`) — every create/edit/delete of a check-in, goal, or project through the UI automatically triggers a background re-index of just that one item, via FastAPI's `BackgroundTasks`. This keeps the knowledge base current without any manual step, while staying cheap enough to run on a memory-constrained free-tier host (embeds one item, not the whole corpus, and reuses the already-loaded embedding model rather than reloading it per write).

---

## Retrieval evaluation
 
`retrieval_eval.py` runs a fixed set of evaluation questions (`eval_questions.py`) through three retrieval methods and reports Recall@5, MRR, and Precision@5 for each (averaged across 7 evaluation questions):
 
| Method | Recall@5 | MRR | Precision@5 |
|---|---|---|---|
| BM25 | 0.857 | 0.529 | 0.257 |
| Vector | 0.857 | 0.600 | 0.457 |
| Hybrid (RRF) | **1.000** | **0.714** | 0.457 |
 
Hybrid retrieval is used in production based on these results — it matched or beat both individual methods on every metric, and was the only method to achieve perfect recall across all test questions. The clearest case: "What are my main goals right now?" scored 0.0 recall on vector search alone (the query's phrasing didn't embed close enough to the goal entries) but 1.0 on both BM25 and hybrid, showing the two methods catch different failure modes.

## LLM evaluation
 
`llm_eval.py` compares three system prompts (`prompts.py`) — a minimal baseline, a structured/grounded version, and a reasoning-chain version — using an LLM-as-judge to score groundedness, relevance, and helpfulness on each answer (averaged across 8 evaluation questions):
 
| Prompt | Groundedness | Relevance | Helpfulness |
|---|---|---|---|
| A — Basic | 5.00 | 5.00 | 5.00 |
| B — Structured | 5.00 | 5.00 | 5.00 |
| C — Reasoning | 5.00 | 4.75 | 4.12 |
 
Prompt B (structured) is used in production. A and B scored identically on this evaluation set — retrieval was strong enough on these questions that both had sufficient grounded context to answer well, so B's extra instructions (explicitly refuse to guess when context is insufficient, surface patterns across entries) didn't get a chance to differentiate itself here. B is kept in production anyway, since that grounding behavior is a safety property that matters most exactly when it *isn't* triggered by an eval set built from well-covered questions — a larger eval set including deliberately under-covered questions would be the natural next step to actually test it. Prompt C (reasoning/chain-of-steps) scored measurably lower on helpfulness, likely because its rigid 4-part format sometimes produced a less direct answer than the question called for.
 
---

## Monitoring

Every `/ask` call logs question, retrieved document IDs, retrieval/LLM latency, token usage, and the answer to a `query_logs` table. A `/feedback` endpoint records thumbs up/down against a specific answer.

The Grafana dashboard (`grafana/dashboards/momentum_rag.json`) has 5 panels reading directly from that table:

1. Requests over time
2. Average response latency
3. Retrieval latency vs. LLM latency (split)
4. Token usage over time
5. Positive vs. negative feedback

![Grafana](images/grafana.png)

---

## Setup

### Option A — Docker Compose (local, full stack)

```bash
git clone <your-repo-url>
cd momentum-rag
cp .env.example .env   # fill in GROQ_API_KEY at minimum or any provider that you are using
docker compose up -d --build
```

This starts Postgres, Qdrant, Grafana, the API, and the frontend together. Then seed and index your first data:

```bash
docker compose exec api python seed.py
docker compose exec api python ingest.py
```

Frontend: `http://localhost:5173` · API: `http://localhost:8000` · Grafana: `http://localhost:3000` (`admin`/`admin`)

### Option B — Free-tier cloud (matches the live demo)

| Component | Service | Free tier |
|---|---|---|
| Postgres | [Neon](https://neon.com) | Yes, no card required |
| Vector DB | [Qdrant Cloud](https://cloud.qdrant.io) | 1GB cluster, no card required |
| LLM | [Groq](https://console.groq.com) | Yes |
| API hosting | [Render](https://render.com) | Yes (cold starts after 15 min idle) |
| Frontend hosting | [Vercel](https://vercel.com) | Yes |
| Monitoring | [Grafana Cloud](https://grafana.com) | Yes |

Environment variables needed (see `.env.example`):

```bash
DATABASE_URL=postgresql://...neon.tech/momentum?sslmode=require
QDRANT_URL=https://...cloud.qdrant.io:6333
QDRANT_API_KEY=...
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile   # optional, this is the default
```

### Dependencies

All pinned in [`requirements.txt`](requirements.txt) (full dev/eval environment) and [`requirements-api.txt`](requirements-api.txt) (minimal set actually shipped in the deployed API image). Frontend dependencies in [`frontend/package.json`](frontend/package.json).

---

## Usage walkthrough

![Momentum](images/momentum_a.png)
![Momentum](images/momentum_b.png)

1. **Check in daily** — a 30-second form (did you do your planned task, motivation 1-10, social media opens, reinstalled-app flag)
2. **Track goals and projects** — create, update status, mark complete, or delete — every change is immediately searchable
3. **Ask questions** — e.g. *"What should I focus on today?"*, *"What usually happens after I finish a big goal?"* — answers are grounded only in your own retrieved entries, with sources shown
4. **Give feedback** — thumbs up/down on any answer, feeds the monitoring dashboard

---

## Project structure

```text
momentum-rag/
├── model.py, documents.py          # data model + flattening to embeddable Documents
├── seed.py                         # initial sample data
├── ingest.py, indexing.py          # full batch + incremental embedding pipelines
├── embeddings.py, chunking.py      # shared embedding/chunking used across the above
├── retrieval.py, bm25_retrieval.py,
│   hybrid_retrieval.py             # three retrieval methods, compared in eval
├── llm.py, prompts.py              # LLM calls + the 3 compared prompt variants
├── api.py                          # FastAPI app - all endpoints
├── eval_questions.py, retrieval_eval.py,
│   llm_eval.py                     # evaluation harnesses
├── frontend/                       # SvelteKit + Tailwind UI
├── grafana/                        # dashboard + datasource provisioning
├── docker-compose.yml,
│   Dockerfile.api,
│   frontend/Dockerfile             # containerization
└── schema.sql                      # Postgres schema
```

---

## Known limitations / honest gaps

Documenting these directly rather than glossing over them:

- **No re-ranking or query rewriting** — hybrid search (vector + BM25 via RRF) is implemented and evaluated, but a cross-encoder re-ranking step and LLM-based query rewriting are not. Given more time, re-ranking would likely give the larger accuracy improvement of the two.
- **Tasks and weekly plans are modeled but not exposed in the UI** — `model.py` and `documents.py` both support them, and they'd be picked up automatically by ingestion if added to the database, but there's no form to create them yet.
- **Render's free tier cold-starts** — the API sleeps after 15 minutes of inactivity; the first request after a gap takes 30-50 seconds. Acceptable for a personal tool, worth knowing before judging response times.
- **No reflections UI yet** — reflections can be added via `seed.py` or directly via SQL, but there's no form in the app itself.

---

## Course

Built for the [DataTalks.Club LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp) final project.
