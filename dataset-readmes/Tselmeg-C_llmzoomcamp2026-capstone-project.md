# Pokemon RAG

LLM Zoomcamp 2026 capstone project. A Pokemon search + quiz app built to demonstrate a
full RAG stack: hybrid retrieval, agentic generation, evaluation, and LLM observability.

See [`PROJECT_SPEC.md`](PROJECT_SPEC.md) for the full architecture writeup and phased
build log.

## Stack

- **Data**: [PokeAPI](https://pokeapi.co) Gen-1 subset (151 Pokemon)
- **Hybrid retrieval**: [Qdrant](https://qdrant.tech) (embedded, on-disk) with dense
  (`BAAI/bge-small-en-v1.5`) + sparse (`Qdrant/bm25`) embeddings via
  [FastEmbed](https://github.com/qdrant/fastembed) — fully local, no embedding API cost
- **Re-ranking**: local cross-encoder (`Xenova/ms-marco-MiniLM-L-6-v2`, also via FastEmbed)
  rescoring the hybrid candidate pool — `hybrid_rerank` is the default retrieval strategy
- **Query rewriting**: the agent's search tool condenses the question into a search
  query before retrieval (`src/rewrite.py`), on by default
- **Agentic RAG**: OpenAI `gpt-5.4-mini` with a tool-calling loop (plain OpenAI SDK, no
  agent framework) over the hybrid+rerank retriever
- **Evaluation**: a 68-question curated ground-truth set, Hit Rate@k / MRR across
  dense/sparse/hybrid/hybrid_rerank search, LLM-as-judge faithfulness scoring across
  multiple system-prompt variants
- **Observability**: [Logfire](https://logfire.pydantic.dev) traces every OpenAI call;
  cost computed via [`pydantic/genai-prices`](https://github.com/pydantic/genai-prices);
  user 👍/👎 feedback is also logged as a queryable event — both surfaced in a live
  usage dashboard
- **Frontend**: [Streamlit](https://streamlit.io) — Search, Quiz, and Usage tabs
- **Packaging**: Docker Compose (single `app` service — see "Containerization" below
  for why that's the whole stack, not a shortcut)

## Setup

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env   # then fill in OPENAI_API_KEY (required); LOGFIRE_* optional
```

## Build the data + index

```bash
make fetch          # or: uv run python fetch_pokemon_data.py -> data/pokemon.json, data/pokemon_corpus.jsonl
make build-index     # or: uv run python build_index.py       -> hybrid Qdrant index at qdrant_data/
```

## Run the app

```bash
make ui              # or: uv run streamlit run app.py
```

Open http://localhost:8501 — **Search** (hybrid search + optional AI answer, with
retrieval-strategy / prompt-variant / rewrite toggles in the Settings expander), **Quiz**
(guess-the-Pokemon multiple choice), **Usage** (live LLM cost/token/feedback dashboard,
requires `LOGFIRE_TOKEN`/`LOGFIRE_READ_TOKEN`).

## Run with Docker

```bash
docker compose up --build
```

The image bakes in the Pokemon corpus, the hybrid index, *and* the reranker's model
cache at build time (none of the three needs a secret), so the container is
immediately runnable with just `OPENAI_API_KEY` in `.env` — no separate setup step.
`docker-compose.yml` is a single `app` service on purpose: Qdrant runs embedded
on-disk inside the container (no separate vector-DB process to orchestrate) and
monitoring is the hosted Logfire SaaS, so there's genuinely nothing else to add as a
second service — `docker compose up --build` is still the one command that builds
and runs the whole thing.

Open http://localhost:8501. `OPENAI_API_KEY` is only needed for the "Ask the AI" button
and the Quiz/agent features — Search and Quiz work without it. `LOGFIRE_TOKEN`/
`LOGFIRE_READ_TOKEN` are optional (Usage tab only). All come from `.env` via
`env_file:`, same as running locally.

To rebuild with a fresher Pokemon dataset, just re-run `docker compose up --build` —
no cache-busting needed unless PokeAPI itself changed.

## Evaluation

Both retrieval and answer quality are evaluated across multiple approaches; the
winners are what the app ships by default.

### Retrieval evaluation

`eval/ground_truth.json` is a **68-question curated ground-truth set** — one
descriptive question per Pokemon (name never mentioned), hand-written against the
real fetched corpus so the eval is reproducible offline with zero LLM cost (see
`src/evaluation.py:load_ground_truth`; `generate_ground_truth()` is also available if
you'd rather LLM-generate a fresh set).

```bash
make eval-retrieval   # or: uv run python -m src.evaluation retrieval --k 5
```

Results (68 questions, k=5), reproduced from a real run against the local index:

| Strategy | Hit Rate | MRR |
|----------|:--------:|:---:|
| dense | 0.941 | 0.732 |
| sparse | 0.941 | 0.743 |
| hybrid | 0.985 | 0.836 |
| **hybrid_rerank** | 0.971 | **0.836** |

**Decision:** ship **`hybrid_rerank`** as the default (`PokemonRetriever.search`'s
default `mode`, and what the agent's `search_pokemon` tool uses). It has the best MRR
— the cross-encoder sharpens *where in the top-k* the right Pokemon lands, which is
what matters once the agent only reads the top few tool results. It comes at a small
cost: hit rate is 1.4 points lower than plain `hybrid` (68 points spread thin — that's
one question), because reranking drops a marginal hybrid hit to make room for a
better-ranked one elsewhere. Full JSON: `eval/retrieval_results.json`.

Raw numbers (68 saturating questions on a 151-item corpus) leave dense and sparse
close together and hybrid/hybrid_rerank clearly ahead of either alone — hybrid search
earns its keep here, not just on paper.

Query rewriting is also evaluated (`--rewrite` flag), mirroring the production path
where the agent's tool rewrites the question before searching:

```bash
make eval-retrieval-rewrite   # needs OPENAI_API_KEY — not run in this pass, see note below
```

> This repo ships the **raw-query** results above (`eval/retrieval_results.json`),
> generated without spending API tokens. The `--rewrite` variant needs
> `OPENAI_API_KEY` to call the rewriter — run `make eval-retrieval-rewrite` yourself
> to reproduce `eval/retrieval_results_rewrite.json` and confirm rewriting still
> helps on this corpus (it's evaluated, not just assumed, precisely so this can be
> checked rather than taken on faith).

### Answer evaluation (LLM-as-a-judge)

Three system-prompt variants (`concise`, `detailed`, `cautious` — `src/prompts.py`),
same retrieval (`hybrid_rerank`) and sources, each answer scored 1–5 for faithfulness
to the reference Pokemon description by a judge model.

```bash
make eval-generation   # or: uv run python -m src.evaluation generation --n 15
```

> Needs `OPENAI_API_KEY` (one agent call + one judge call per question per variant —
> 3 variants × 15 questions = 90 calls on the mini model). Not run in this pass for
> the same reason as the rewrite eval above — no key available in the environment
> that made this change. Run `make eval-generation` to produce
> `eval/generation_results.json` and confirm/override the shipped default
> (`concise`, in `src/prompts.DEFAULT_VARIANT`).

## Monitoring

Grafana-style dashboard, built with Logfire + matplotlib, in the Streamlit **Usage**
tab — **6 charts** plus summary metrics, all live off the same Logfire event stream
the app itself writes to:

1. Cost by hour · 2. LLM calls by hour · 3. Token usage by hour (input/output) ·
4. Feedback breakdown (👍 vs 👎) · 5. Satisfaction rate over time · plus summary
metrics (total cost, avg cost/call, total tokens, satisfaction rate).

**Feedback**: every "Ask the AI" answer in the Search tab shows 👍/👎 buttons; a
click logs an `llm_feedback` event (question, answer, rating) via
`src/observability.log_feedback`, queried back by `src/monitoring.feedback_summary` /
`feedback_by_day` for the dashboard above.

Charts only render once there's data — ask a few questions via "Ask the AI" and rate
a couple of answers to populate the Usage tab (requires `LOGFIRE_TOKEN` +
`LOGFIRE_READ_TOKEN`).

## Best practices

- **Hybrid search** — Qdrant native RRF fusion of dense + sparse (`src/retrieval.py`),
  evaluated against each single-mode baseline above.
- **Document re-ranking** — local cross-encoder rescoring the hybrid pool
  (`src/rerank.py`), evaluated as `hybrid_rerank` above and shipped as the default.
- **Query rewriting** — `src/rewrite.py`, used by the agent's search tool before
  retrieval, evaluated via `--rewrite` above.

## Notebooks

Each phase was prototyped on a small data sample before being promoted into `src/`:

| Notebook | Phase |
|---|---|
| `explore_data.ipynb` | Initial data exploration |
| `01_hybrid_retrieval.ipynb`, `02_test_retrieval.ipynb` | Hybrid retrieval |
| `03_agentic_rag.ipynb`, `04_test_agent.ipynb` | Agentic RAG pipeline |
| `06_evaluation.ipynb` | Evaluation pipeline + charts (early prototype — superseded by `src/evaluation.py` + `eval/`, which adds `hybrid_rerank`, query rewriting, prompt-variant comparison, and a committed ground-truth set) |
| `07_quiz_logic.ipynb` | Quiz question generation |
| `08_usage_dashboard.ipynb` | LLM usage/cost dashboard |

## Project structure

```
data/                   fetched/generated data (gitignored — regenerate with make fetch/build-index)
qdrant_data/             on-disk hybrid index (gitignored — regenerate with make build-index)
eval/                    ground truth + eval results (committed — see "Evaluation" above)
notebooks/               numbered prototyping notebooks, one per phase
src/                     reusable modules (retrieval, rerank, rewrite, prompts, agent,
                         quiz, evaluation, observability, monitoring)
tests/                   unit tests for the pure-logic pieces (rerank, rewrite, quiz)
app.py                   Streamlit frontend
fetch_pokemon_data.py    data ingestion script
build_index.py           hybrid index build script
Dockerfile               container build (bakes in data + index + reranker cache)
docker-compose.yml       docker compose up --build -> whole app in one command
Makefile                 uv/docker convenience targets (see `make help` targets below)
.env.example             template for required/optional secrets
```

## Testing

```bash
make test   # or: uv run --group dev pytest tests/ -q
```

Covers the pure-logic pieces that don't need network/API access: cross-encoder
rerank ordering/dedup (`tests/test_rerank.py`, cross-encoder mocked), the query
rewriter's fallback-on-error contract (`tests/test_rewrite.py`, OpenAI client
mocked), and quiz question generation (`tests/test_quiz.py`).

## Notes

Kestra orchestration was attempted (Phase 3) but dropped — Docker Desktop couldn't start
on the dev machine and wasn't worth the detour for a capstone demo. Each pipeline step
(`fetch_pokemon_data.py`, `build_index.py`) runs standalone, so nothing depends on an
orchestrator.
