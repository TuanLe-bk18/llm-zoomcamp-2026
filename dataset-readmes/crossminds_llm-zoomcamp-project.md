# ☸️ k8s-api-rag

An AI assistant for the Kubernetes API documentation. Answers questions about
API resources (fields, types, required-ness, descriptions) grounded in the
official Kubernetes OpenAPI v3 specification, via RAG.

## 📋 Rubric coverage

For peer review - where each implemented grading criterion is evidenced in
this repo:

| Criterion | Evidence |
|---|---|
| Problem description | This section - a K8s API doc Q&A assistant grounded via RAG. |
| Retrieval flow | Knowledge base (Elasticsearch, `rag/search.py`) + LLM (`rag/pipeline.py`) - see [How it works](#-how-it-works). |
| Retrieval evaluation | Vector / text (BM25) / hybrid compared, best one (vector) selected - `rag/eval/retrieval_eval.py`, numbers in [Evaluation](#-evaluation). |
| LLM evaluation | Two generation prompts compared via LLM-as-judge, best kept as default - `rag/eval/llm_eval.py`, numbers in [Evaluation](#-evaluation). |
| Interface | CLI, one-shot or interactive - `main.py`, see [Run with Python](#-run-with-python) / [Run with Docker Compose](#-run-with-docker-compose). |
| Ingestion pipeline | Scripted ingestion (`ingest.py`), containerized and runnable via Compose - see [Ingest the knowledge base](#-ingest-the-knowledge-base). |
| Containerization | Elasticsearch + `app` + `ingest` all defined in `docker/docker-compose.yml` - see [Project layout](#-project-layout). |
| Reproducibility | Pinned dependencies (`uv.lock`), data checked into the repo, step-by-step [Setup](#-setup). |
| Monitoring | User feedback collected (`Helpful? [y/n]` prompt -> `rag/logs.py`) + Grafana dashboard with 6 panels, both provisioned via Compose - see [Monitoring](#-monitoring). |
| Best practice: hybrid search | `search_hybrid` in `rag/search.py`, evaluated alongside vector/text in `rag/eval/retrieval_eval.py`. |
| Best practice: document reranking | `rag/rerank.py`, evaluated in `rag/eval/best_practices_eval.py` - see [Query rewriting and reranking](#-query-rewriting-and-reranking). |
| Best practice: query rewriting | `rag/rewrite.py`, evaluated in `rag/eval/best_practices_eval.py` - see [Query rewriting and reranking](#-query-rewriting-and-reranking). |

Not implemented: an orchestrated ingestion tool (Airflow/Prefect/dlt/Kestra),
a UI/API interface, and cloud deployment - see [Status](#-status).

## ⚙️ Setup

Requires [uv](https://docs.astral.sh/uv/) and Docker.

```bash
uv sync
cp .env.example .env                   # non-secret settings (safe to commit)
cp .env.private.example .env.private   # add your OPENAI_API_KEY here
docker compose -f docker/docker-compose.yml up -d   # starts Elasticsearch, ingests the knowledge base, starts Grafana
```

> **You must edit `.env.private` and set `OPENAI_API_KEY=<your key>`** before
> running anything else - every step below (ingestion and asking questions)
> calls the OpenAI API and will fail without it.

Config is split across two files so the secret never ends up in git: `.env`
holds non-secret settings (Elasticsearch URL, model names, etc.) and is
committed; `.env.private` holds only `OPENAI_API_KEY`, is gitignored, and is
loaded second so it overrides `.env` if both define the same variable.

## 📥 Ingest the knowledge base

**This already happened** if you ran `docker compose up -d` in
[Setup](#-setup) - the `ingest` service (`docker/ingest.Dockerfile`) runs
automatically as part of that command, and `app` (`depends_on: ingest:
condition: service_completed_successfully`) won't start querying until it
finishes. Nothing more to do here unless you want to re-run it.

To re-run it manually (e.g. to pick up a newer `K8S_RELEASE`), via Docker
Compose:

```bash
docker compose -f docker/docker-compose.yml run --rm ingest
```

This automatically starts Elasticsearch and waits for it to become
healthy if it isn't running yet (`depends_on: elasticsearch` with a health
check - verified by stopping Elasticsearch first and confirming
`run --rm ingest` brings it up on its own), and it runs against the exact
same Python/dependency versions as the `app` image instead of whatever's
on your host.

Or directly with Python:

```bash
uv run python ingest.py
```

Either way, this fetches the spec for the Kubernetes release set in `.env`
(`K8S_RELEASE`, default `release-1.31`), builds ~470 chunks, and indexes them
into Elasticsearch. Re-run it any time to refresh or switch release versions
- `rag/ingestion/index.py` recreates the index from scratch each time, so
it's always safe to re-run, though each run does re-embed every chunk via
the OpenAI API.

## 🚀 How to run the application

**tl;dr - the two commands to get everything running, including the
interactive prompt:**

```bash
docker compose -f docker/docker-compose.yml up -d       # Elasticsearch + ingest + Grafana
docker compose -f docker/docker-compose.yml run --rm app  # interactive prompt
```

The first is a one-time (or occasional re-run) setup step - see
[Setup](#-setup) and [Ingest the knowledge base](#-ingest-the-knowledge-base).
The second is what you run every time you want to ask a question; it's
covered in detail below, along with the plain-Python alternative and the
one-shot (non-interactive) form.

### 🐳 Run with Docker Compose

> **Your current folder must be the project root** (the folder containing
> this README) - not `docker/`. That's why the command points at the
> compose file with `-f docker/docker-compose.yml` instead of `cd`-ing
> into it. Also note `app` has `profiles: ["cli"]`, so plain
> `docker compose up` never starts it (there'd be no way to type into it
> anyway - only `run`, below, attaches your terminal):

One-time question, passed as an argument:

```bash
docker compose -f docker/docker-compose.yml run --rm app "What fields does a Deployment spec have?"
```

Or drop the question to get the same interactive prompt loop as below,
inside the container - keep asking questions, press ↑ to recall previous
questions, then press Enter on an empty line (or Ctrl+D) to quit:

```bash
docker compose -f docker/docker-compose.yml run --rm app

k8s-api-rag> What fields does a ConfigMap have?

A ConfigMap has the following fields: ...

Sources:
  - ConfigMap (io.k8s.api.core.v1.ConfigMap) score=0.827
  - ...

Helpful? [y/n, Enter to skip]: y

k8s-api-rag>
```

### 🐍 Run with Python

> **Your current folder must be the project root**, same as above.
> `rag/config.py` loads `.env` / `.env.private` via relative paths, so
> running from anywhere else means the config (and `OPENAI_API_KEY`)
> won't load.

```bash
uv run python main.py "What fields does a Deployment spec have?"
```

Or run without arguments for an interactive prompt loop - keep asking
questions, press ↑ to recall previous questions (readline history), then
press Enter on an empty line (or Ctrl+D) to quit:

```bash
uv run python main.py

k8s-api-rag> What fields does a Deployment spec have?

DeploymentSpec has the following fields: ...

Sources:
  - DeploymentSpec (io.k8s.api.apps.v1.DeploymentSpec) score=0.832
  - ...

Helpful? [y/n, Enter to skip]: y

k8s-api-rag> Is the containers field required on a PodSpec?

Yes - containers is a required field on PodSpec...

Sources:
  - PodSpec (io.k8s.api.core.v1.PodSpec) score=0.841
  - ...

Helpful? [y/n, Enter to skip]: y

k8s-api-rag>
```

Notice the `Helpful? [y/n, Enter to skip]:` prompt after each answer - that's
feedback collection, see [Monitoring](#-monitoring) below.

## 📈 Monitoring

Every question asked (via either interface above) is logged to a dedicated
Elasticsearch index (`k8s-rag-logs`, `rag/logs.py`) with the question,
answer, sources, retrieval config, and latency. The `Helpful? [y/n]` prompt
shown after each answer records a thumbs up/down against that log entry
(`logs.record_feedback`) - that's the "user feedback" half of this rubric
criterion.

The other half - a dashboard - is a Grafana instance wired to that index,
provisioned automatically (datasource + dashboard, no manual clicking) via
`docker/grafana/provisioning/`. It comes up as part of the same Compose
stack:

```bash
docker compose -f docker/docker-compose.yml up -d grafana
```

Open [localhost:3000](http://localhost:3000) (login `admin` / `admin`) -
the "k8s-rag monitoring" dashboard has 6 panels: total questions, feedback
breakdown (thumbs up/down), retrieval strategy usage, top source kinds
returned, questions over time, and average answer latency. All were
verified against real logged interactions while building this.

## 🧠 How it works

1. **Ingestion** (`ingest.py`): downloads the OpenAPI v3 spec (one JSON file
   per API group/version) for a pinned Kubernetes release, flattens every
   schema into a self-contained text chunk (kind, group/version, description,
   fields with types and required-ness), embeds each chunk with an OpenAI
   embedding model, and indexes it into Elasticsearch (text + dense vector).
2. **Retrieval** (`rag/search.py`): embeds the user's question and searches
   the indexed chunks. Three strategies are implemented (vector/kNN,
   text/BM25, hybrid/RRF) - vector is the default, see Evaluation below.
3. **Query rewriting and reranking** (`rag/rewrite.py`, `rag/rerank.py`,
   composed in `rag/pipeline.py::retrieve`): optionally rewrite the question
   before retrieval and/or retrieve a wider candidate set and rerank it down
   to `RETRIEVAL_TOP_K` - see below.
4. **Generation** (`rag/pipeline.py`): passes the retrieved chunks as context
   to an LLM, which answers grounded in that context.

## 🗄️ Data

All data is fetched from the public Kubernetes GitHub repo, not stored anywhere
else, and is checked into this repo so the project is reproducible without
re-running ingestion:

- **Source**: `rag/ingestion/fetch_spec.py` downloads the OpenAPI v3 spec
  (one JSON file per API group/version - `INCLUDED_FILES` in that module
  lists the 18 stable groups) from
  `raw.githubusercontent.com/kubernetes/kubernetes/<release>/api/openapi-spec/v3/`,
  pinned to the release in `.env` (`K8S_RELEASE`, default `release-1.31`).
- **Storage**:
  - `data/raw/*.json` - the raw downloaded OpenAPI spec files.
  - `data/processed/chunks.jsonl` - ~470 flattened per-schema documents built
    by `rag/ingestion/chunk.py` (this is what gets embedded and indexed).
  - `data/processed/ground_truth.jsonl` - LLM-generated Q&A pairs used for
    evaluation (`rag/eval/generate_ground_truth.py`).
  - `data/processed/retrieval_eval.json` / `llm_eval.json` /
    `best_practices_eval.json` - evaluation results (see Evaluation below).
- **Regenerating**: none of it needs to be committed to work - `uv run python
  ingest.py` re-fetches and rebuilds `data/raw/` and `data/processed/chunks.jsonl`
  from scratch at any time (e.g. to pick up a newer Kubernetes release).

## 🎯 Query rewriting and reranking

Two optional steps sit between retrieval and generation, composed in
`rag/pipeline.py::retrieve`:

- **Query rewriting** (`rag/rewrite.py`): before searching, an LLM call
  rewrites the question into a standalone form and expands common
  Kubernetes abbreviations (e.g. "depl" -> "Deployment", "svc" -> "Service").
  Useful for informal or shorthand-heavy user input; the *retrieved* chunks
  are still scored against the rewritten query, but sources/generation use
  the original question.
- **Reranking** (`rag/rerank.py`): retrieval fetches a wider candidate set
  (`RERANK_CANDIDATE_K`, default 20) instead of just `RETRIEVAL_TOP_K`, then
  an LLM call reorders those candidates by relevance to the *original*
  question and keeps only the top `RETRIEVAL_TOP_K`. This catches cases
  where the embedding/BM25 similarity score ranked a less-relevant chunk too
  highly.

Both are config-gated (`QUERY_REWRITE_ENABLED`, `RERANK_ENABLED` in
`rag/config.py`, default `false`/`true` respectively - see Evaluation
below for why) and can be overridden per-call via `retrieve(question,
rewrite=..., rerank=...)`.

## 📊 Evaluation

```bash
uv run python -m rag.eval.generate_ground_truth   # ~470 LLM-generated Q&A pairs, one per chunk
uv run python -m rag.eval.retrieval_eval          # compares vector / text / hybrid retrieval
uv run python -m rag.eval.llm_eval                # compares generation prompt variants via LLM-as-judge
uv run python -m rag.eval.best_practices_eval     # compares baseline vs +rewrite vs +rerank vs +both
```

**Retrieval** (hit-rate / MRR @ k=5, n=469): vector 0.996 / 0.935, hybrid
0.998 / 0.917, text (BM25) 0.902 / 0.765. Vector wins and is the default
(`RETRIEVAL_STRATEGY` in `.env`). Caveat: the ground-truth questions are
LLM paraphrases of each chunk, which structurally favors semantic (vector)
retrieval over lexical (BM25) matching - a real-world query mix would likely
narrow this gap, which is part of why hybrid is still implemented and worth
revisiting with real user queries.

**Generation** (LLM-as-judge relevance, n=50 sampled questions): a
"detailed" prompt (mentions field names/types/required-ness) and a "concise"
prompt scored effectively the same (0.990 avg / 98% relevant). The judge
rewards factual relevance, not verbosity. "detailed" is kept as the default
since it better fits an API-reference use case.

**Query rewriting / reranking** (hit-rate / MRR @ k=5, vector retrieval,
n=100 sampled questions): `+rerank` wins clearly - 0.990 / 0.975, vs. 0.990 /
0.937 for the `baseline` (no rewrite, no rerank). `+rewrite` alone is
slightly *worse* than baseline (0.980 / 0.922), and adding it on top of
rerank doesn't help either (0.990 / 0.955 for `+rewrite+rerank`). Reranking
is on by default (`RERANK_ENABLED=true`); rewriting is implemented and
evaluated but off by default (`QUERY_REWRITE_ENABLED=false`). Likely cause:
the ground-truth questions are themselves LLM paraphrases close to the
chunk text (same caveat as the retrieval evaluation above), so rewriting
adds a lossy hop rather than closing a real vocabulary gap - it may earn
its keep on messier, real user queries.

## 🗂️ Project layout

```
rag/
  config.py           # env-driven settings
  openai_client.py     # shared OpenAI client + retry/backoff
  embeddings.py        # OpenAI embedding helper
  search.py            # vector / text / hybrid retrieval
  rewrite.py            # LLM query rewriting
  rerank.py             # LLM reranking of candidates
  logs.py               # Q&A + feedback logging into Elasticsearch
  prompts.py           # prompt templates
  pipeline.py          # retrieve (+ rewrite/rerank) + generate + log
  ingestion/
    fetch_spec.py      # download OpenAPI v3 spec files
    chunk.py            # flatten schemas into text chunks
    index.py             # embed + load into Elasticsearch
  eval/
    generate_ground_truth.py  # LLM-generated Q&A pairs from chunks
    retrieval_eval.py          # hit-rate/MRR across retrieval strategies
    llm_eval.py                 # LLM-as-judge comparison of prompt variants
    best_practices_eval.py      # hit-rate/MRR for rewrite/rerank on/off
ingest.py               # orchestrates the ingestion pipeline
main.py                 # CLI entrypoint
docker/
  app.Dockerfile         # image for the app service
  ingest.Dockerfile       # image for the ingest service
  build.sh                 # builds every docker/*.Dockerfile, tags as crossminds/k8s-rag-<name>
  docker-compose.yml       # Elasticsearch + app + ingest + grafana
  grafana/provisioning/
    datasources/            # Elasticsearch datasource pointed at k8s-rag-logs
    dashboards/              # dashboard provider config + the dashboard JSON itself
```

## ✅ Status

Core RAG pipeline (ingestion → retrieval → generation), query rewriting,
reranking, all three evaluation stages (retrieval, LLM output,
rewrite/rerank), and monitoring (feedback + Grafana dashboard) are
implemented. Not yet done: a proper UI, an orchestrated ingestion tool, and
cloud deployment.
