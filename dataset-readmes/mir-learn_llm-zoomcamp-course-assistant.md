# LLM Zoomcamp Course Assistant

A Retrieval-Augmented Generation (RAG) application that answers questions about
the **LLM Zoomcamp** course using the **course video transcripts** as its
knowledge base. Ask "What is the difference between keyword and vector search?"
and get an answer grounded in the actual lessons, with citations and deep-links
to the exact moment in the source video.

> Built for the LLM Zoomcamp final project. The corpus is the course
> transcripts (an explicitly allowed dataset) — **not** the banned DataTalks FAQ.

---

## Problem description

Video courses hold a lot of knowledge, but it is locked inside hours of footage.
A student who wants a quick, specific answer ("how do I evaluate retrieval?",
"what does the agentic loop look like?") has to scrub through videos to find it.

This project turns the ~72 lessons of the LLM Zoomcamp into a searchable,
conversational knowledge base. It:

- ingests the lesson prose **and** the spoken transcripts of every video,
- retrieves the most relevant passages for a question,
- asks an LLM to answer **only from that retrieved course context**, with
  citations to the module/lesson and a deep-link to the video timestamp,
- evaluates both retrieval and answer quality, and
- collects user feedback and monitors usage in a live dashboard.

## The data

| Source | What it is | How it's used |
|---|---|---|
| `corpus/course/**/lessons/*.md` | Clean lesson prose + the YouTube link for each video | Discovered for metadata; prose is a KB document and a transcript fallback |
| `corpus/notes/**/*-transcript.md` | Timestamped YouTube transcripts (fetched via `youtube-transcript-api`) | The primary spoken-content KB documents |

Both are **committed to the repo** so the dataset is fully reproducible even if
YouTube changes or blocks access. The ingestion pipeline turns them into
`data/chunks.json` — **551 chunks** (377 from transcripts, 174 from prose),
each with a stable id, module/lesson metadata, and a `&t=<seconds>` deep link.

**Where the data comes from.** The lesson markdown under `corpus/course/` is
mirrored from the public course repository
[DataTalksClub/llm-zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp)
(course material © DataTalks.Club, used here for the course's own final
project). The transcripts under `corpus/notes/` were fetched from the public
YouTube videos those lessons link to, using
[`youtube-transcript-api`](https://pypi.org/project/youtube-transcript-api/) —
`ingest/fetch_transcripts.py` re-fetches them live and falls back to the
committed copies when YouTube is unavailable. Note this is the course
**transcript/lesson corpus**, not the DataTalks.Club FAQ documents, which the
project rules exclude.

## Architecture / flow

```
corpus/ ──▶ discover ──▶ fetch_transcripts ──▶ chunk ──▶ data/chunks.json
                                                              │
                                                   ┌──────────┴──────────┐
                                                   ▼                     ▼
                                           minsearch (text)      Qdrant (vector)
                                                   └──────── hybrid (RRF) ───────┘
                                                              │
   query ─▶ [rewrite?] ─▶ retrieve ─▶ [rerank?] ─▶ prompt ─▶ OpenRouter LLM ─▶ answer
                                                              │
                                      FastAPI /ask ──▶ Postgres (log) ──▶ Grafana
                                            ▲
                                      Streamlit UI (👍/👎 ─▶ /feedback)
```

- **Retrieval:** three backends — text (`minsearch`), vector
  (`sentence-transformers` embeddings in **Qdrant**), and **hybrid** (reciprocal
  rank fusion). Embeddings run locally (free, reproducible); only answering uses
  a remote LLM.
- **LLM:** any model via **OpenRouter** (OpenAI-compatible). Default is a free
  Llama model so reviewers can run it with one key.
- **Best practices:** query rewriting, cross-encoder re-ranking, and hybrid
  search are all implemented and toggleable.

## Repository layout

```
project/
├── corpus/            committed raw data (lesson md + transcript notes)
├── data/              pipeline output (lessons/transcripts/chunks .json) — committed
├── ingest/            discover · fetch_transcripts · chunk · build_index
├── rag/               index (text/vector/hybrid) · rag (flow) · settings
├── eval/              retrieval_eval · chunking_eval · rag_eval
├── api/               FastAPI: /ask /feedback /health /docs
├── app/               streamlit_app · monitoring/ (Postgres + Grafana)
├── dags/              Airflow DAG: discover→fetch→chunk→index
├── docker-compose.yml api·ui·qdrant·postgres·grafana·airflow
├── Dockerfile / Dockerfile.airflow
├── Makefile · .env.example
├── requirements.txt          app + pipeline (pinned)
└── requirements-ingest.txt   pipeline-only subset, used by the Airflow image
```

> Every module's docstring explains what that component does and why, so the
> code is readable top-down. For running, troubleshooting and deploying, see
> [DEPLOY.md](DEPLOY.md).

---

## Quick start (Docker — everything)

```bash
cp .env.example .env          # add your OPENROUTER_API_KEY
docker compose up -d --build
```

> **First build takes a while** — roughly 15–20 minutes and ~20 GB of disk
> (app image ~9.7 GB, Airflow image ~10.5 GB). Both install
> `sentence-transformers`, which pulls in PyTorch and its CUDA wheels, and the
> app image pre-downloads the embedding model so containers start fast and work
> offline afterwards. It is not hung; subsequent builds are cached.

Then open:

| Service | URL |
|---|---|
| Streamlit chat UI | http://localhost:8501 |
| FastAPI + Swagger | http://localhost:8000/docs |
| Grafana dashboard | http://localhost:3000  (admin / admin) |
| Airflow UI | http://localhost:8080  (admin / admin) |
| Qdrant | http://localhost:6333 |

The `data/` cache is committed, so the app answers immediately. To rebuild the
knowledge base, trigger the **`ingest_course_transcripts`** DAG in Airflow (or
run `make ingest`).

## Quick start (local, no Docker)

```bash
pip install -r requirements.txt
cp .env.example .env          # set OPENROUTER_API_KEY (QDRANT_URL can be blank -> in-memory)
make ingest                   # discover → fetch → chunk → index
make api                      # FastAPI on :8000   (separate terminal)
make ui                       # Streamlit on :8501
```

Without `OPENROUTER_API_KEY`, retrieval and evaluation harness still work; only
the final LLM answer step needs the key.

## Usage example

```bash
curl -s http://localhost:8000/ask -H 'content-type: application/json' -d '{
  "question": "What is the difference between keyword and vector search?",
  "retrieval": "hybrid", "top_k": 5, "rerank": true
}' | jq '{answer, sources: [.sources[] | {module, lesson, deep_link}]}'
```

Returns the answer plus the source chunks (with video deep-links) and an
`interaction_id` you can POST to `/feedback`.

---

## Evaluation

**Retrieval** — generate an LLM ground truth, then compare all approaches by
Hit Rate@k and MRR@k; the best is used by the app:

```bash
make gen-ground-truth     # -> data/ground-truth.csv  (needs API key)
make eval-retrieval       # -> eval/retrieval-results.md, data/retrieval-metrics.csv
```

Compares **text vs. vector vs. hybrid vs. hybrid+rerank**. A representative run
(160 ground-truth pairs) — `hybrid+rerank` wins and is what the app uses:

| Approach | Hit Rate@5 | MRR@5 |
|---|---|---|
| **hybrid+rerank** | **0.781** | **0.617** |
| vector | 0.669 | 0.471 |
| hybrid | 0.588 | 0.387 |
| text | 0.312 | 0.213 |

Note the row order: plain `hybrid` scores *below* `vector`. That is expected
here rather than a bug. Reciprocal rank fusion weights both arms equally, and
the keyword arm is weak on this corpus (0.213 MRR — spoken transcripts rarely
repeat the exact wording of a question), so fusing it in dilutes the vector
ranking. Fusion still pulls the *right* passages into the candidate pool; what
it gets wrong is their order. That is precisely the job of the cross-encoder,
and re-ranking the fused pool beats every single-backend approach — which is
why the app runs `hybrid` **and** the re-ranker together.

**Chunking strategies** are also compared (fixed-size vs. section chunking) at
lesson-level retrieval — a second evaluation axis:

```bash
python ingest/chunk.py --strategy section   # build the alternative chunk set
python eval/chunking_eval.py --k 5           # -> eval/chunking-results.md
```

Result: `fixed` chunking wins on MRR@5 (0.768 vs 0.693) and is the default.

**RAG answers** — two prompt styles (`concise` vs. `detailed_cited`) are
compared with a **pairwise LLM-as-judge**. Absolute 1–5 scoring was tried first
and saturated — both prompts scored 5/5 over good context — so it could not
separate them. Asking the judge which of two answers is better does. Every pair
is judged in **both orders** and a win counts only when both orders agree, which
cancels the judge's position bias; disagreements are recorded as inconclusive.
The judge is a different model from the one being judged, so it isn't rating its
own output.

```bash
make eval-rag             # -> eval/rag-results.md
```

Over 20 questions, `detailed_cited` won **19 of 20** decisive comparisons and is
the prompt the app uses.

## Monitoring

Every interaction is logged to Postgres by the API; the Streamlit 👍/👎 buttons
write feedback. After each answer, an **online LLM judge** scores it for
relevance and faithfulness (1–5) in a background task and stores the scores
with the interaction (uses `JUDGE_MODEL`, falls back to the free `LLM_MODEL`;
disable with `ONLINE_JUDGE=false`). The provisioned **Grafana** dashboard has
6 panels: questions over time, feedback ratio, average latency, token usage,
top modules asked about, and the LLM-judge relevance distribution.

## Ingestion automation

The `ingest_course_transcripts` **Airflow DAG** runs
`discover → fetch_transcripts → chunk → index` as ordered `PythonOperator`
tasks — the same callables behind `make ingest`. It is idempotent and reads/
writes the committed `data/` cache, so a full re-ingest can be triggered from
the Airflow UI or scheduled.

## Rubric coverage

| Criterion | Where | Pts |
|---|---|---|
| Problem description | this README | 2 |
| Retrieval flow | KB (`rag/index.py`) + LLM (`rag/rag.py`) | 2 |
| Retrieval evaluation | text/vector/hybrid/+rerank (`eval/retrieval_eval.py`) | 2 |
| LLM evaluation | 2 prompts, LLM-as-judge (`eval/rag_eval.py`) | 2 |
| Interface | FastAPI API + Streamlit UI (`api/`, `app/`) | 2 |
| Ingestion pipeline | Airflow DAG (`dags/ingest_dag.py`) | 2 |
| Monitoring | feedback + Grafana (6 panels) | 2 |
| Containerization | full `docker-compose.yml` | 2 |
| Reproducibility | pinned deps + committed data + this README | 2 |
| Best practices | hybrid + rerank + query rewrite | 3 |
| Bonus — cloud deployment | `docker-compose.prod.yml` + step-by-step VM / Kubernetes guide ([DEPLOY.md](DEPLOY.md)) | see note |

> **Cloud deployment:** the stack is deployment-ready — `docker compose -f
> docker-compose.yml -f docker-compose.prod.yml up -d` (or `make up-prod`) runs
> it on any VM, and [DEPLOY.md](DEPLOY.md) walks through provisioning, firewall
> rules and TLS — but there is no public instance running right now, so treat
> this as a reproducible deployment path rather than a live URL.

## Screenshots

| UI | Monitoring |
|---|---|
| ![Streamlit UI](images/ui.png) | ![Grafana dashboard](images/grafana.png) |

| API (Swagger) | Ingestion DAG |
|---|---|
| ![Swagger](images/swagger.png) | ![Airflow DAG](images/airflow.png) |

## Tech stack

FastAPI · Streamlit · Qdrant · minsearch · sentence-transformers · OpenRouter ·
Postgres · Grafana · Apache Airflow · Docker Compose.
