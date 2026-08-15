# 🥗 NutriChat — Nutrition & Health-Facts Assistant

A retrieval-augmented (RAG) chat application that answers questions about
**nutrition, foods, vitamins, minerals, diets, and diet-related health
conditions**, grounded in a knowledge base built from Wikipedia.

Ask *"How much vitamin D do adults need?"*, *"Is the Mediterranean diet good for
the heart?"*, or *"What foods are high in iron?"* — NutriChat retrieves the most
relevant passages from its knowledge base and asks an LLM to answer **using only
that context**, with source citations.

Everything runs **inside a single Python virtual environment** — no database
server, no Docker required. Storage is embedded (SQLite), and monitoring is a
built-in Streamlit dashboard.

> This is my capstone project for the **DataTalksClub LLM Zoomcamp 2026**.

![NutriChat chat interface](docs/chat.png)

*The chat UI answering "how much protein do adults need?" — a grounded answer
with the health-safety note and the retrieved sources (with relevance scores).*

## 🎥 Demo video

<video controls src="docs/demo.mp4" title="Title"></video>
https://github.com/PrajwalSridhar28/nutrichat/blob/main/docs/demo.mp4
---

## Problem statement

Reliable nutrition information is scattered across long encyclopedic articles.
People asking simple questions ("does coffee count as water?", "what causes iron
deficiency?") either wade through walls of text or turn to an ungrounded chatbot
that may hallucinate. NutriChat solves this by combining a curated nutrition
**knowledge base** with an **LLM**: answers are concise, cite their sources, and
refuse to answer when the knowledge base doesn't cover the question — reducing
hallucination. A health-safety disclaimer is added for medical-adjacent questions.

**Who it's for:** anyone who wants quick, sourced answers to everyday nutrition
questions without reading full Wikipedia articles.

---

## What it does (the flow)

```
                 ┌──────────────────────────────────────────────────────────┐
   Wikipedia ───►│ dlt → DuckDB staging → chunk → embed (ONNX MiniLM) → SQLite│
  (~160 topics)  └──────────────────────────────────────────────────────────┘
                                        │  (FTS5 text index + float32 vectors)
                                        ▼
 User question ─► query rewrite ─► HYBRID retrieval ─► cross-encoder ─► prompt ─► OpenAI ─► answer
   (Streamlit)      (LLM)         (text ⊕ vector RRF)   re-rank                  (gpt-4o-mini)  + sources
        ▲                                                                                 │
        └──────────── thumbs up/down feedback ─────► SQLite ─────► Streamlit monitoring page ◄┘
```

1. **Ingestion** — a [dlt](https://dlthub.com) pipeline pulls ~160 nutrition
   articles from the Wikipedia API into an embedded DuckDB staging file; they are
   then section-chunked, embedded, and loaded into SQLite.
2. **Retrieval** — hybrid search (SQLite full-text ⊕ NumPy vector, fused with
   Reciprocal Rank Fusion), followed by cross-encoder re-ranking of the top
   candidates.
3. **Generation** — the user question + retrieved context go to OpenAI, using a
   grounded prompt that cites sources and refuses when the answer isn't present.
4. **Interface** — a Streamlit chat UI with source citations and feedback buttons.
5. **Monitoring** — every answer and every 👍/👎 is logged to SQLite and
   visualized in a Streamlit monitoring page.

---

## Tech stack

| Layer | Choice |
|---|---|
| LLM | **OpenAI** (`gpt-4o-mini`, Responses API) |
| Knowledge base | **SQLite** — FTS5 full-text search + float32 embedding blobs |
| Vector search | **NumPy** cosine over an in-memory matrix (corpus is small) |
| Embeddings | `all-MiniLM-L6-v2` via **ONNX Runtime** (no PyTorch → tiny footprint) |
| Re-ranker | `ms-marco-MiniLM-L-6-v2` cross-encoder (ONNX) |
| Ingestion | **dlt** (data load tool) → embedded **DuckDB** staging |
| Interface | **Streamlit** |
| Monitoring | **Streamlit** dashboard page (reads SQLite) |
| Env / packaging | **uv** (Python 3.12, `uv.lock`) |

### What is dlt? (tool not covered in the course)

[**dlt**](https://dlthub.com) ("data load tool") is a lightweight Python library
for building data pipelines. You write a `@dlt.resource` generator that yields
records; dlt handles schema inference, typing, incremental loading (state), and
loading into a destination. Here it extracts Wikipedia articles into an embedded
DuckDB file with `write_disposition="merge"`, so re-running ingestion **upserts**
changed articles and adds new ones without duplicating — a real incremental
pipeline. See `ingest/wiki_source.py` and `ingest/run_ingest.py`.

### Why SQLite + NumPy instead of a vector database?

The knowledge base is only a few thousand chunks, so the entire embedding matrix
fits in memory and a NumPy dot-product search returns in well under a millisecond
— no external vector DB needed. SQLite (built into Python) stores the chunks,
their embeddings (as float32 blobs), and the monitoring logs, and provides
BM25-ranked full-text search via its FTS5 extension. The result: the whole
application runs inside one virtual environment with **zero services to start**.

---

## Quick start (uv — recommended)

**Prerequisites:** [uv](https://docs.astral.sh/uv/) and an OpenAI API key.

```bash
# 1. Install Python 3.12 + all locked dependencies into the venv
uv sync

# 2. Configure your OpenAI key
cp .env.example .env          # then edit .env: OPENAI_API_KEY=sk-...

# 3. Download the ONNX embedding + reranker models (into ./models)
uv run python scripts/download_model.py

# 4. Ingest the knowledge base (Wikipedia -> DuckDB -> embeddings -> SQLite)
uv run python -m ingest.run_ingest        # ~2-4 minutes

# 5. Launch the app
uv run streamlit run app/app.py           # http://localhost:8501
```

Open **http://localhost:8501** for the chat, and the **📊 Monitoring** page (in
the Streamlit sidebar) for the dashboard.

Prefer an activated shell? `source .venv/bin/activate` (Windows PowerShell:
`.venv\Scripts\Activate.ps1`), then drop the `uv run` prefix.

### Command reference

| Task | Command |
|---|---|
| Install env | `uv sync` |
| Download models | `uv run python scripts/download_model.py` |
| Ingest data | `uv run python -m ingest.run_ingest` |
| Run app | `uv run streamlit run app/app.py` |
| Generate eval questions | `uv run python -m eval.ground_truth 60` |
| Evaluate retrieval | `uv run python -m eval.eval_retrieval` |
| Evaluate prompts | `uv run python -m eval.eval_rag 25` |
| Faithfulness corruption benchmark (+ DeLong/Holm) | `uv run python -m eval.corruption_bench --limit 300` |
| Build blind rater pool | `uv run python -m eval.build_pool --mode demo --n 40` |
| Generate the blind labelling tool | `uv run python -m eval.label_tool` |
| Ingest rater labels → per-arm acceptance + kappa | `uv run python -m eval.ingest_labels` |

> Tip: set `INGEST_LIMIT=10` in `.env` to ingest just 10 topics for a fast trial.

---

## Optional: run in Docker

The project also ships a `Dockerfile` + `docker-compose.yml` (embedded SQLite,
models baked into the image — no other services). Requires only Docker:

```bash
cp .env.example .env                  # set OPENAI_API_KEY
docker compose run --rm ingest        # one-shot ingestion into the shared volume
docker compose up -d app              # http://localhost:8501
```

---

## Evaluation

### Retrieval evaluation (multiple approaches compared)

We generate a ground-truth set (LLM writes questions for a random sample of
chunks; the source chunk is the gold answer), then measure **Hit Rate (recall@5)**
and **MRR@5** for four retrieval strategies:

```bash
uv run python -m eval.ground_truth 60     # generate ground_truth.csv (~120 questions)
uv run python -m eval.eval_retrieval      # compare text / vector / hybrid / hybrid+rerank
```

Results are written to `eval/results/retrieval_metrics.csv`. Our run (120
ground-truth questions, k=5):

| method | hit_rate@5 | mrr@5 |
|---|---|---|
| text | 0.9333 | 0.7963 |
| vector | 0.9000 | 0.7360 |
| hybrid | 0.9583 | 0.8269 |
| **hybrid_rerank** | **0.9583** | **0.8511** |

> `hybrid_rerank` has the best **MRR@5 (0.8511)** and ties `hybrid` on hit rate —
> re-ranking reorders the same candidates to put the gold chunk higher. This is why
> it is the default used by the app.

### LLM evaluation (multiple prompts compared)

Three answer prompts (`baseline`, `grounded`, `structured` — see
`nutrichat/prompts.py`) are compared with an **LLM-as-judge** that rates each
answer RELEVANT / PARTLY_RELEVANT / NON_RELEVANT:

```bash
uv run python -m eval.eval_rag 25         # scores each prompt over 25 questions
```

Results → `eval/results/rag_metrics.csv`. Our run (60 questions; score: RELEVANT=1,
PARTLY=0.5, NON=0):

| prompt | avg_score | pct_relevant |
|---|---|---|
| baseline | 0.9333 | 0.9333 |
| grounded | 0.9250 | 0.9167 |
| structured | 0.9167 | 0.9167 |

> Over 60 questions the three prompts are effectively tied (0.917–0.933; a
> 0.017 spread). The app defaults to `structured` (`DEFAULT_PROMPT` in
> `nutrichat/prompts.py`): since raw judged relevance is indistinguishable, the
> tie-breaker is its grounding and safety behaviour — source citations, a
> refuse-when-unknown rule, and a health-safety disclaimer — which a relevance-only
> judge does not reward but which matter for a health-adjacent assistant. Set
> `DEFAULT_PROMPT` to `baseline` if you prefer to optimise judged relevance alone.

---

## Monitoring

Every answered question is logged to the SQLite `conversations` table (latency,
tokens, cost, retrieval method, sources) and every 👍/👎 to the `feedback` table.
The **📊 Monitoring** page (in the Streamlit sidebar) shows 4 KPIs + 6 charts:

1. Total questions · 2. Thumbs-up rate · 3. Avg response time · 4. Total cost
(USD) · 5. Questions over time · 6. Avg response time over time · 7. Retrieval-
method distribution · 8. Feedback (👍 vs 👎) · 9. Token usage over time · 10. Top
cited articles, plus a recent-questions table.

![NutriChat monitoring dashboard](docs/monitoring.png)

*The monitoring page — KPI tiles (questions, thumbs-up rate, latency, cost) above
the time-series and distribution charts.*

---

## Best practices implemented

- **Hybrid search** — text (SQLite FTS5) ⊕ vector (NumPy cosine), fused with
  Reciprocal Rank Fusion (`nutrichat/search.py`), and evaluated against each
  single method.
- **Document re-ranking** — an ONNX cross-encoder re-ranks the top-30 hybrid
  candidates down to the top-5 (`nutrichat/reranker.py`).
- **Query rewriting** — the LLM rewrites the user's chat message into a focused
  search query before retrieval (`RAGPipeline.rewrite_query`).

All three are toggleable in the Streamlit sidebar so you can see their effect live.

---

##Demo video
https://github.com/PrajwalSridhar28/nutrichat/blob/main/docs/demo.mp4


## Extended evaluation (bonus)

Beyond the required rubric, the project adds a **pre-registered**, statistically
grounded evaluation of answer *faithfulness* — the core risk of any RAG system —
all runnable offline against the knowledge base (stdlib only, no API key):

- **Pre-registration** — RQs, hypotheses, metrics, and decision thresholds are
  frozen in [`PRE_REGISTRATION.md`](PRE_REGISTRATION.md) before results are seen.
- **Corruption benchmark** (`eval/corruption_bench.py`) — an objective, label-free
  faithfulness test: real chunks become *grounded* claims, five seeded defect types
  (wrong identifier, fabricated quantity, dropped condition, over-claim, scope
  inflation) are injected into the claim text while the context is unchanged, and
  lexical detectors (`support`, `structured`, `fusion` — `nutrichat/faithfulness.py`)
  must score the clean claim above its corrupted twin. Reports paired concordance
  per defect and AUROC per detector.
- **DeLong + Holm statistics** (`nutrichat/stats.py`) — detectors are compared
  head-to-head with **DeLong's test** for correlated AUROCs, **Holm–Bonferroni**
  corrected across the family (plus Spearman, ECE, Cohen's/Fleiss' kappa).

  Our run (300 grounded claims → 300 clean + 1,010 corrupted items):

  | detector | AUROC (clean vs corrupted) | overall concordance |
  |---|---|---|
  | support (token overlap) | 0.9624 | 0.9624 |
  | **structured (bigram overlap)** | **0.9985** | **0.9985** |
  | fusion (mean) | 0.9985 | 0.9985 |

  `structured` significantly beats plain token-overlap `support` — DeLong
  z = −8.87, p ≈ 0, still rejected after Holm correction — mirroring the thesis
  finding that a claim-decomposed signal catches identifier/quantity swaps that a
  bag-of-words overlap misses. (`fusion` ties `structured`, p = 1.0.)
- **Blind rater study** (`eval/build_pool.py` → `label_tool.py` → `ingest_labels.py`)
  — a self-contained HTML tool where raters score answers **blind** (Accept / Edit /
  Reject + Relevant / Grounded / Complete), never seeing how each was produced.
  Ingestion re-pairs by a hidden tag and reports per-arm acceptance + inter-rater
  kappa, written to a `rater_labels` table. This is a *formal* study on top of the
  app's lightweight 👍/👎 feedback.

```bash
uv run python -m eval.corruption_bench --limit 300     # benchmark + DeLong/Holm → eval/results/corruption_*
uv run python -m eval.build_pool --mode demo --n 40    # blind pool  → eval/results/pool.json
uv run python -m eval.label_tool                       # → eval/results/label_tool.html (open, rate, download labels_*.json)
uv run python -m eval.ingest_labels                    # labels_*.json → per-arm acceptance + kappa
```

---

## Project structure

```
project/
├── pyproject.toml / uv.lock   # uv-managed env (Python 3.12, pinned deps)
├── requirements.txt           # same pins, for the optional Docker image
├── Dockerfile / docker-compose.yml   # optional containerized run
├── .env.example               # configuration template
├── Makefile
├── nutrichat/                 # shared library
│   ├── config.py              # env-driven configuration + pricing
│   ├── db.py                  # SQLite schema, connections, monitoring logging
│   ├── embeddings.py          # ONNX MiniLM embedder (reused from course)
│   ├── reranker.py            # ONNX cross-encoder re-ranker
│   ├── search.py              # text (FTS5) / vector (NumPy) / hybrid (RRF)
│   ├── prompts.py             # prompt variants + query-rewrite prompt
│   └── rag.py                 # RAGPipeline (rewrite → retrieve → rerank → LLM)
├── ingest/
│   ├── topics.py              # curated Wikipedia nutrition topics
│   ├── wiki_source.py         # dlt resource (Wikipedia API)
│   ├── build_index.py         # chunk + embed + populate SQLite knowledge base
│   └── run_ingest.py          # end-to-end ingestion entrypoint
├── app/
│   ├── app.py                 # Streamlit chat UI
│   └── pages/1_Monitoring.py  # Streamlit monitoring dashboard
├── eval/
│   ├── ground_truth.py        # generate evaluation Q&A
│   ├── eval_retrieval.py      # hit-rate / MRR across retrieval methods
│   └── eval_rag.py            # LLM-as-judge across prompts
├── scripts/download_model.py  # fetch ONNX models from Hugging Face
└── data/                      # SQLite DB + DuckDB staging (git-ignored)
```

---

## How the rubric is covered

| Criterion | Where |
|---|---|
| Problem description | This README (top) |
| Retrieval flow (KB + LLM) | `nutrichat/rag.py`, `nutrichat/search.py` |
| Retrieval evaluation (multiple) | `eval/eval_retrieval.py` — 4 methods |
| LLM evaluation (multiple) | `eval/eval_rag.py` — 3 prompts, LLM judge |
| Interface | `app/app.py` (Streamlit UI) |
| Ingestion pipeline (automated) | `ingest/` (dlt, incremental) |
| Monitoring (feedback + dashboard) | Streamlit feedback + monitoring page (10 panels) |
| Containerization | `docker-compose.yml` (app + ingest) |
| Reproducibility | `pyproject.toml` + `uv.lock` (+ pinned `requirements.txt`), `.env.example` |
| Hybrid search | `nutrichat/search.py` (RRF) |
| Re-ranking | `nutrichat/reranker.py` |
| Query rewriting | `RAGPipeline.rewrite_query` |
| _Bonus_ — pre-registration | `PRE_REGISTRATION.md` |
| _Bonus_ — objective faithfulness benchmark | `eval/corruption_bench.py`, `nutrichat/faithfulness.py` |
| _Bonus_ — significance testing (DeLong + Holm) | `nutrichat/stats.py` |
| _Bonus_ — blind rater study | `eval/build_pool.py`, `eval/label_tool.py`, `eval/ingest_labels.py` |

---

## Data & attribution

The knowledge base is built from **English Wikipedia** articles (see
`ingest/topics.py`), retrieved via the public MediaWiki API. Wikipedia content is
licensed under [CC BY-SA](https://creativecommons.org/licenses/by-sa/4.0/). The
DataTalksClub course FAQ is **not** used (per project rules).

## License

MIT (project code). Wikipedia-derived content retains its CC BY-SA license.
