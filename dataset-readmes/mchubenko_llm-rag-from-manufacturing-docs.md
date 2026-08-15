# Company Handbook Assistant

A RAG Q&A app over the internal handbook of a fictional manufacturing company.
You can ask a question and it finds the relevant handbook chunks,
answers strictly from them, shows which documents it used, and says "not in
here" when it doesn't know instead of guessing.

Runs locally, one `docker compose up`: Postgres, a one-time ingestion job,
a Streamlit app, a Grafana dashboard.

## Why this exists

Every manufacturing company has this problem: there's always some part of how
things actually run that nobody currently holds in their head. Stuff gets
reinvented or repeated over time because nobody remembers it was already
solved. People who held the knowledge rotate out or leave without passing it
on. And when an improvement project kicks off, it usually starts with weeks of
analysis, sitting with people, trying to reconstruct "how does this actually
work" - and that reconstruction is never quite accurate, because it depends on
someone remembering to mention something, not on whether it was important.

If the procedures, sub-processes, and the reasoning behind them are actually
written down, that analysis gets faster and more complete, nothing falls
through the cracks, and onboarding a new person is a lot less painful.

The edge case that made this click for me: multi-plant setups in the same
manufacturing group. You want to standardize or change something across
plants, so you run meetings, map out how each site currently does it,
sometimes across languages, then figure out what to change. A RAG assistant
over each plant's documentation would cut a huge chunk of that mapping time -
which is the direction this points, even though this project is a single
company/single handbook by scope.

## What a good answer looks like

Grounded in the handbook, direct, cites its sources, refuses when the
handbook doesn't cover it. That refusal behavior is graded as its own thing,
not an afterthought.

It doesn't touch the ERP, live inventory, or today's schedule - handbook only,
read-only, and it points to the responsible procedure/role rather than acting
as the final word itself.

## What it looks like

Ask, get the answer with the handbook sections it came from, rate it:

![The Streamlit Q&A screen: a question about purchase order approvals, the grounded answer, the expandable Sources list, and thumbs up/down](docs/images/qa-screen.png)

Every question logs a row to Postgres, and Grafana reads that table - volume,
latency, refusal rate, thumbs up/down, judge scores, token spend, and which
part of the handbook people are actually asking about:

![The Grafana dashboard, eight panels: query volume, p50/p95 latency, refusal rate, feedback pie, judge quality trend, token usage totals and over time, and questions by handbook area](docs/images/monitoring-dashboard.jpeg)

## Running it

```
cp .env.example .env      # paste your OPENAI_API_KEY in
docker compose up         # loads data, then serves everything
```

Retrieval itself is free and offline (local embeddings); the key is only used
to generate the actual answer.


| Service  | URL                                            | What it is                                |
| -------- | ---------------------------------------------- | ----------------------------------------- |
| App      | [http://localhost:8501](http://localhost:8501) | the Streamlit Q&A screen                  |
| Grafana  | [http://localhost:3000](http://localhost:3000) | dashboard (anonymous viewing on)          |
| Postgres | localhost:5432                                 | vectors, full-text index, interaction log |

The dashboard reads the interaction log, so it's empty until the app has been
used - ask two or three questions first, then open Grafana.

First run is slower than later ones: the images build and the embedding model
is downloaded into them.

Other commands:

```
make ingest     # re-run ingestion by hand
make judge      # score logged answers with an LLM judge
```

The two eval notebooks live in `notebooks/` and run on the host
(`uv run jupyter lab`) against the same Postgres on 5432. The retrieval one
re-runs with no API key needed, from a committed ground-truth CSV. The LLM
one makes real OpenAI calls.

`docker compose down -v` wipes the Postgres volume for a clean-slate re-run.

## How it works

Question gets embedded locally (fastembed, `bge-small-en-v1.5`), 
top 5 chunks come back from Postgres, `gpt-4o-mini` writes the
answer from those chunks at temperature 0. Everything - answer, sources,
latency, tokens, your thumbs up/down - logs to one Postgres table, which
Grafana reads.

The corpus is authored Markdown under `data/corpus/<doc_type>/*.md`, split on
headings into chunks at ingest time. A chunk is one section, and its ID is
`<doc_type>/<document>#<heading>` - derived from the content, so it's stable
across re-ingests. That ID is what the model is told to cite and what the
Sources list shows, which is why it carries the document name and not just the
heading: fifteen different documents have a section called "Purpose".

Retrieval mode is `RETRIEVER=keyword|vector|hybrid`, defaults to whichever the
eval notebook found best (hybrid, via reciprocal rank fusion - both live in
`retrieval/retrieve.py`).

## Map

Where each piece lives, in the order the
[LLM Zoomcamp project rubric](https://github.com/DataTalksClub/llm-zoomcamp/blob/main/project.md)
asks about them:

| Area                 | Lives in                                                                                                        |
| -------------------- | --------------------------------------------------------------------------------------------------------------- |
| Problem description  | the "Why this exists" and "What a good answer looks like" sections above                                         |
| Retrieval flow       | `retrieval/retrieve.py` + `generation/generate.py`, wired together in `app/app.py`                               |
| Retrieval evaluation | `notebooks/retrieval-evaluation.ipynb` - keyword vs vector vs hybrid on hit-rate@5 / MRR@5, best one shipped     |
| LLM evaluation       | `notebooks/llm-evaluation.ipynb` - three prompts scored by an LLM judge on four criteria, best one shipped       |
| Interface            | `app/app.py`, Streamlit                                                                                          |
| Ingestion pipeline   | `ingest/`, a dlt pipeline, `make ingest`                                                                         |
| Monitoring           | thumbs up/down in the app, plus the 8-panel Grafana dashboard in `grafana/provisioning/`                         |
| Containerization     | everything - app, ingest, db, dashboard - in one `docker-compose.yml`                                            |
| Reproducibility      | committed corpus and eval CSVs, pinned `uv.lock`, one-command setup                                              |
| Hybrid search        | `retrieval/retrieve.py`, reciprocal rank fusion, kept because the eval measured it as the best of the three      |
| Batch quality scoring| `make judge` → `generation/judge_batch.py`, off the serving path, feeds the dashboard's judge panel              |


## Reproducibility

The corpus is synthetic - generated by AI for this project and committed, so nothing
external is needed to rebuild it. `uv.lock` pins every Python dependency, and
Postgres and Grafana are pinned to exact image versions.

Both eval notebooks re-run from committed CSVs. The retrieval one needs no API
key at all; the LLM one only needs a key if you delete its results file and want
to regenerate the answers.

## Scaling this to something real

This ingestion is a simple dlt pipeline on purpose: static corpus, full replace every run, by hand. Some production-grade deploy would load incrementally (merge on doc id + content hash, only re-embed what changed), get triggered by a folder-watcher or a light orchestrator instead of a person (Dagster / Prefect / Kestra), and log per-file ingestion health somewhere so a failed doc doesn't just silently vanish. At scale of that project it didn't make much sense, but worth considering in a real scenario. 