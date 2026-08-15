# 💊 Anesthesiology PubMed Q&A — a RAG application

Ask clinical anesthesiology questions and get **answers grounded in PubMed literature,
with citations**. The system retrieves the most relevant passages from a knowledge base of
anesthesiology papers, assembles a prompt, and asks an LLM to answer *only* from that
evidence — every answer links back to the source articles (PMID).

> ⚕️ **This is a literature-retrieval assistant, not a medical decision tool.** Answers
> summarize published research and are not medical advice.

This is an end-to-end capstone project: **data ingestion → retrieval → generation →
evaluation → interface → monitoring**, fully containerized.

---

## The problem

Anesthesiologists and researchers answer specific questions ("What antiemetic is most
effective for high-risk PONV?", "Does sugammadex reduce residual neuromuscular blockade vs
neostigmine?") from the primary literature. Doing this by hand means searching PubMed and
skimming dozens of abstracts. This app does the retrieval and synthesis, and keeps the
clinician one click from the source paper — while refusing to answer when the evidence
isn't there, to limit hallucination.

- **Data source:** [NCBI PubMed / Entrez](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
  (title + abstract + metadata) enriched with **PubMed Central Open Access** full text
  where available.
- **Corpus:** ~5,000 anesthesiology articles (2015–2026), ~55% with full text →
  **47,934 embedded chunks**.

## How it works

```
                     ┌──────────────────────────────────────────────┐
   PubMed (Entrez) ─▶│  dlt ingestion:  fetch → normalize → chunk    │
   PMC Open Access ─▶│  → embed (OpenAI)                             │
                     └───────────────────────┬──────────────────────┘
                                              ▼
                          ┌───────────────────────────────────┐
                          │ PostgreSQL + pgvector               │
                          │  articles · chunks(+embeddings,FTS) │
                          │  query_logs · feedback              │
                          └───────┬───────────────────┬─────────┘
        rewrite→retrieve→rerank→answer│               │ metrics
                                      ▼               ▼
   User ─▶ Streamlit UI ─▶ RAG (rag.py) ─▶ OpenAI      Grafana dashboard
              ▲   👍/👎 feedback     │                  (feedback + health)
              └─────────────────────┘
```

**Query flow** (`rag.py`): rewrite the question → **hybrid retrieval** (keyword + vector) →
**cross-encoder rerank** + dedupe → assemble a grounded prompt → LLM answer with `[n]`
citations → log the query, latency, tokens, and cost.

## Tech stack

| Concern | Choice |
|---------|--------|
| LLM + embeddings | OpenAI `gpt-4o-mini` + `text-embedding-3-small` |
| Knowledge base | PostgreSQL + `pgvector` (vectors, keyword FTS, logs, feedback) |
| Ingestion | [dlt](https://dlthub.com/) (Entrez + PMC REST sources) |
| Retrieval | keyword (Postgres FTS) · vector (pgvector) · hybrid (RRF) · cross-encoder rerank ([fastembed](https://github.com/qdrant/fastembed), ONNX) |
| Interface | Streamlit |
| Monitoring | Grafana (auto-provisioned dashboard over Postgres) |
| Packaging | Docker Compose |

## Quick start

**Prerequisites:** [Docker](https://docs.docker.com/get-docker/),
[uv](https://docs.astral.sh/uv/), and an [OpenAI API key](https://platform.openai.com/).
(NCBI works without a key; adding `NCBI_API_KEY` speeds ingestion.)

```bash
# 1. configure
cp .env.example .env
# edit .env and set OPENAI_API_KEY=sk-...

# 2. start the stores (Postgres + Grafana; schema auto-applied)
make up            # or: docker compose up -d

# 3. install Python deps (Python 3.12 via uv)
make install       # or: uv sync

# 4. build the knowledge base — pick ONE:
make restore-data          # FAST: use the shipped ~5k-article corpus (data/kb.duckdb.gz)
# make build-kb MAX=2000   # or fetch fresh from NCBI (~2k here; MAX=5000 for full, ~80 min)

# 5. add embeddings (needs OPENAI_API_KEY; ~$0.38 for the full corpus)
make embed

# 6. run the app
make ui            # or: uv run streamlit run app.py  → http://localhost:8501
```

> **Shipped data:** the repo includes the built corpus at `data/kb.duckdb.gz` (~54 MB), so
> reviewers can skip the slow NCBI fetch — `make restore-data` decompresses and loads it.
> Embeddings are *not* shipped (they'd be ~300 MB); `make embed` regenerates them.

Then open:
- **App:** http://localhost:8501
- **Monitoring:** http://localhost:3000 (`make seed` first to populate demo data)

> **Ports:** Postgres is published on **5433** (host 5432 is often taken), Grafana on
> **3000**, Streamlit on **8501** — all configurable in `.env`.

## Usage

**In the UI:** type a question, pick a retrieval strategy (default `hybrid_rerank`), read the
cited answer, expand the source cards, and leave 👍/👎 feedback.

**From the CLI:**
```bash
uv run python -m pubmed_rag.rag "Does sugammadex reduce residual neuromuscular blockade compared to neostigmine?"
```
```
Sugammadex significantly reduces residual neuromuscular blockade compared to neostigmine.
- Sugammadex reverses moderate-to-deep block in <5 min vs >15 min for neostigmine [1][4][5].
- It encapsulates the blocking agent, avoiding cholinergic side effects [3][4].
- Associated with fewer postoperative respiratory complications from residual paralysis [4][8].
This is a summary of published literature, not medical advice.

Sources:
  [1] ... PMID:40186115  https://pubmed.ncbi.nlm.nih.gov/40186115/
  ...
```

## Evaluation

Both retrieval and answer quality are evaluated with multiple approaches; the winners are
what the app ships. Full method + results: **[docs/evaluation.md](docs/evaluation.md)**.

**Retrieval** (50 labeled question→PMID pairs, Hit Rate / MRR@10):

| Strategy | Hit Rate | MRR |
|----------|:--------:|:---:|
| keyword | 0.760 | 0.532 |
| vector | 0.920 | 0.867 |
| hybrid | 0.920 | 0.799 |
| **hybrid_rerank** | **0.940** | **0.882** |

With **query rewriting** (the production path), `hybrid_rerank` reaches **MRR 0.93** — the
best configuration, and the one the app ships. The docs also explain the keyword AND→OR fix
that this table reflects.

**Answer quality** (LLM-as-a-judge, 1–5): the `structured` prompt won (**4.956** overall)
and is the production prompt. Reproduce with `make eval`.

## Monitoring

Grafana dashboard (auto-provisioned) with 8 panels over the live Postgres logs: total
queries, avg latency, cost, satisfaction rate, query volume, latency p50/p95, token usage,
strategy mix, feedback over time, and recent questions. Feedback is collected via the UI's
👍/👎 buttons. Seed demo data with `make seed`, then open http://localhost:3000.

## Screenshots

_Add your own captures to `docs/images/` (the app menu can also record a short demo video)._

| Streamlit answer | Grafana dashboard |
|---|---|
| ![UI](docs/images/ui.png) | ![Dashboard](docs/images/dashboard.png) |

## Project structure

```
src/pubmed_rag/
  config.py            # env-driven configuration
  entrez.py            # NCBI Entrez + PMC BioC fetch/parse
  pipeline.py          # dlt ingestion (two-pass broad+deep corpus)
  load_to_postgres.py  # DuckDB → Postgres loader (no re-fetch)
  chunk.py             # token-based chunking (tiktoken)
  embed.py             # chunks → pgvector embeddings
  retrieval.py         # keyword / vector / hybrid (RRF)
  rerank.py            # cross-encoder rerank + dedupe
  rag.py               # rewrite → retrieve → answer → log
  llm.py               # OpenAI wrapper + cost tracking
  seed_monitoring.py   # demo data for the dashboard
  evaluation/          # ground truth, retrieval eval, answer eval
app.py                 # Streamlit UI
sql/schema.sql         # Postgres schema (articles, chunks, logs, feedback)
grafana/               # datasource + dashboard provisioning
docs/                  # product requirements, evaluation, coverage
```

## How this maps to the evaluation criteria

| Criterion | Where |
|-----------|-------|
| Problem description | This README (top) + [docs/product_requirements.md](docs/product_requirements.md) |
| Retrieval flow (KB + LLM) | `retrieval.py` + `rag.py` |
| Retrieval evaluation (multiple approaches) | `evaluation/retrieval_eval.py`, [docs/evaluation.md](docs/evaluation.md) |
| LLM evaluation (multiple prompts) | `evaluation/answer_eval.py`, [docs/evaluation.md](docs/evaluation.md) |
| Interface | Streamlit `app.py` |
| Ingestion pipeline (automated tool) | dlt in `pipeline.py` |
| Monitoring (feedback + dashboard ≥5 charts) | `feedback` table + Grafana (8 panels) |
| Containerization | `docker-compose.yml` (app deps + monitoring) |
| Reproducibility | this section + pinned versions (`pyproject.toml` / `uv.lock`) + `.env.example` |
| Best practices | hybrid search + query rewriting + document reranking |

## Reproducibility notes

- Python pinned to **3.12** (`uv` manages it); all deps pinned in `pyproject.toml` /
  `uv.lock`.
- The dataset is rebuildable from public APIs via `make build-kb` — no private data.
- `make test` runs the unit tests.

## License / data

Article text and metadata come from NCBI PubMed and PubMed Central Open Access. Respect
[NCBI's usage policies](https://www.ncbi.nlm.nih.gov/home/about/policies/). This project is
for educational use.
