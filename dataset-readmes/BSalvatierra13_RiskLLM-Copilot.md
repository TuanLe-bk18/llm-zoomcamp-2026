# Credit Risk Copitlot

A RAG-based onboarding assistant for credit risk scoring, concepts, and regulation.


A RAG-based assistant that answers questions about credit risk scoring:
what the model variables mean, core risk concepts (PD, LGD, EAD), general
scoring rules, and the regulatory frameworks behind them (Basel, IFRS 9).

## Problem description

Analysts joining a credit risk team need to quickly get up to speed on a
lot of scattered knowledge: what each scoring variable means, the core
risk metrics used across the industry, informal rules of thumb for
evaluating risk, and the regulatory frameworks that shape how credit
decisions are made. Today this knowledge typically lives in long manuals,
regulatory text, and the heads of senior team members — there's no single
place a new analyst can go to ask a specific question and get a clear,
sourced answer without reading entire documents or interrupting a
colleague.

This project builds a conversational assistant that answers these
questions in natural language, grounded in a curated knowledge base, so
that onboarding a new risk analyst (or just looking something up quickly)
doesn't require digging through documentation from scratch.

## Dataset

The knowledge base is a small curated corpus of Markdown documents
(`data/corpus/`), written to cover the topics a new credit risk analyst
needs to understand:

| File | Covers |
|---|---|
| `dataset_variables.md` | The 20 variables of the [German Credit (Statlog) dataset](https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data) — what each one means and why it matters for risk |
| `risk_concepts.md` | Core risk concepts: PD, LGD, EAD, expected loss, scoring vs. rating, cutoff, AUC/Gini |
| `scoring_rules.md` | General heuristics for evaluating credit risk based on applicant profile |
| `basel_regulation.md` | Regulatory context: Basel II/III and IFRS 9 |

The German Credit dataset (`data/raw/`) is used as the reference for the
variable descriptions, but is not directly queried by the RAG pipeline —
the assistant answers conceptual questions from the text corpus, not
row-level lookups on the dataset.

`data/ground_truth/ground-truth-retrieval.csv` has the auto-generated
evaluation questions used for retrieval and LLM evaluation (see
[Evaluation](#evaluation) below).

Everything above is committed to this repo — no external download is
required to run the project. `data/raw/` can also be regenerated from
scratch with `uv run python ingestion/ingest_credit_data.py` if needed,
since it pulls straight from the public UCI source.

## Tech stack

- **Python** with [`uv`](https://docs.astral.sh/uv/) for dependency management
- **minsearch** for keyword-based retrieval, boosted (see [Evaluation](#evaluation))
- **OpenAI API** (`gpt-4o-mini`) for answer generation and as an LLM-as-a-judge evaluator
- **Flask** for the web API that serves the assistant
- **PostgreSQL** to log every conversation and user feedback
- **Grafana** for the monitoring dashboard
- **Docker Compose** to run the whole stack (API + Postgres + Grafana) with one command
- **Jupyter notebooks** for exploration

## Project structure

```
project-llm/
├── data/
│   ├── raw/                      # german_credit_raw.csv, german_credit_readable.csv (reference, not indexed)
│   ├── corpus/                   # the 4 .md files — the RAG's actual knowledge base
│   └── ground_truth/
│       └── ground-truth-retrieval.csv
│
├── ingestion/
│   ├── ingest_credit_data.py     # downloads and cleans the German Credit CSV
│   └── chunking.py               # load_corpus() — loads and chunks the corpus by section
│
├── rag/
│   └── rag_helper.py             # RAGBase class: search (boosted), prompt building, LLM call, rag()
│
├── eval/
│   ├── judge.py                  # LLM-as-a-judge: evaluate_relevance(), calculate_openai_cost()
│   ├── generate_ground_truth.py  # builds data/ground_truth/ground-truth-retrieval.csv
│   ├── metrics.py                # hit_rate(), mrr(), evaluate()
│   ├── eval_retrival.py          # retrieval evaluation: default vs. boosted search
│   └── eval_llm.py               # LLM evaluation: compares two answer-generation prompts
│
├── notebooks/                    # exploration notebooks
│   ├── 01_ingest_and_rag.ipynb
│   ├── 02_ground_truth.ipynb
│   └── 03_evaluating_RAG.ipynb
│
├── grafana/
│   └── provisioning/
│       ├── datasources/datasource.yml   # auto-connects Grafana to Postgres
│       └── dashboards/                  # dashboard provider + the dashboard JSON itself
│
├── app.py                        # Flask API — POST /question, POST /feedback
├── db.py                         # Postgres storage: conversations + feedback tables
├── Dockerfile                    # builds the API image
├── docker-compose.yml            # postgres + app + grafana, all wired together
├── .dockerignore
├── pyproject.toml / uv.lock / .python-version
├── .env.example                  # template — copy to .env and fill in
└── README.md
```

## Setup

Requires [`uv`](https://docs.astral.sh/uv/) and [Docker Desktop](https://www.docker.com/products/docker-desktop/).

1. Install dependencies (exact versions are pinned in `uv.lock`):

   ```bash
   uv sync
   ```

2. Copy the env template and fill in your OpenAI key:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set `OPENAI_API_KEY`. The Postgres values already
   match what `docker-compose.yml` uses, so you normally don't need to
   touch those.

## Running everything with Docker Compose (recommended)

This runs the API, Postgres, and Grafana together, each in its own
container, wired to talk to each other:

```bash
docker-compose up -d --build
```

The first time only, create the database tables (run once, against the
host-exposed Postgres port):

```bash
uv run python -c "import db; db.init_db()"
```

Now:
- The API is at `http://localhost:5000`
- Grafana is at `http://localhost:3000` (user `admin`, password `admin`) — the Postgres datasource and the monitoring dashboard are provisioned automatically, no manual setup needed

Check logs any time with `docker-compose logs -f app`.

### Using the API

```bash
curl -X POST http://localhost:5000/question \
  -H "Content-Type: application/json" \
  -d '{"question": "What is PD in credit risk scoring?"}'
```

Response:

```json
{
  "conversation_id": "3f2a1b90-...",
  "question": "What is PD in credit risk scoring?",
  "answer": "PD (Probability of Default) is ..."
}
```

Send feedback on that answer with the returned `conversation_id`:

```bash
curl -X POST http://localhost:5000/feedback \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "3f2a1b90-...", "feedback": 1}'
```

`feedback` is `1` (👍) or `-1` (👎). Both endpoints write to Postgres,
which feeds the Grafana dashboard.

(On Windows PowerShell, `curl` is aliased to `Invoke-WebRequest` and
doesn't take `-X`/`-H`/`-d`. Use `curl.exe` instead, or the native
`Invoke-RestMethod` — see comments in `app.py` for an example.)

## Running locally, without Docker (alternative)

Only Postgres needs Docker in this mode; the API runs directly on your
machine.

```bash
docker-compose up -d postgres
uv run python -c "import db; db.init_db()"
uv run python app.py
```

Because Postgres is still reached from *outside* its container here,
`.env` must use the host-exposed port: `POSTGRES_PORT=5433` (already the
default in `.env.example`). If you instead run the API inside Docker
too (previous section), it talks to Postgres over the internal Docker
network on port 5432 — that's handled by `docker-compose.yml`, not `.env`.

## Evaluation

Three scripts under `eval/`, meant to be run in this order:

1. **Generate ground truth** (LLM-generated questions per corpus chunk, only needed once or after editing `data/corpus/`):

   ```bash
   uv run python eval/generate_ground_truth.py
   ```

2. **Retrieval evaluation** — compares plain vs. boosted `minsearch` search (hit rate / MRR) and reports the best:

   ```bash
   uv run python eval/eval_retrival.py
   ```

3. **LLM evaluation** — compares two system-prompt variants for answer generation, judging each with the same LLM-as-a-judge (`eval/judge.py`), and reports which produces a higher rate of `RELEVANT` answers:

   ```bash
   uv run python eval/eval_llm.py
   ```

Both scripts isolate one variable at a time (retrieval approach, or
prompt) while keeping everything else fixed, so the comparison is fair.

### Results

Retrieval evaluation, run on 200 ground truth questions:

| Approach | Hit rate | MRR |
|---|---|---|
| Default (no boost) | **0.89** | **0.688** |
| Boosted (`section` x2) | 0.79 | 0.596 |

Plain, unboosted search won clearly — boosting `section` actually hurt
both metrics on this corpus. `RAGBase.search()` in `rag/rag_helper.py`
uses plain search in production, no `boost_dict`.

LLM evaluation, run on a sample of 20 questions:

| Variant | RELEVANT rate |
|---|---|
| Current production default (context + general-knowledge fallback) | **0.95** |
| Strict, context-only | 0.90 |

Letting the model fill small context gaps with general credit-risk
knowledge (clearly labeled as such, instead of refusing outright)
produced more relevant answers than the strict variant. Production
already uses this default.

## Monitoring

Every call to `/question` logs to the `conversations` table (answer,
model, response time, token counts, OpenAI cost, and the LLM-judge
relevance score) and every `/feedback` call logs to the `feedback`
table. The Grafana dashboard (auto-provisioned, see above) reads both
tables and shows: total conversations, total OpenAI cost, average
response time, relevance distribution, user feedback distribution,
cumulative conversations over time, and a table of the latest
conversations.

## Running the Jupyter notebooks

```bash
uv run python -m ipykernel install --user --name project-llm --display-name "Python (project-llm)"
uv run jupyter lab
```

Select the **"Python (project-llm)"** kernel and open any notebook in
`notebooks/`.

## Reproducibility notes

- All dependency versions are pinned in `uv.lock` (generated by `uv sync`), and the Python version is pinned in `.python-version`.
- `Dockerfile` builds from that same `uv.lock` (`uv sync --locked`), so the containerized app uses identical versions to local dev.
- The corpus, raw dataset, and ground truth CSV are committed to the repo — nothing needs to be downloaded to run the project end to end.

## Status

Built as part of the [LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp) course. Current state: RAG pipeline, Flask API, retrieval evaluation (boosted vs. default), LLM evaluation (prompt comparison), conversation/feedback logging, Grafana monitoring dashboard, and full Docker Compose containerization are all in place. Pending: automating the ingestion pipeline with a dedicated orchestration tool, and at least one retrieval best practice (hybrid search, re-ranking, or query rewriting).
