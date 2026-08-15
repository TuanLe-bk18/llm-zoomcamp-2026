# Spoiler-aware RAG system for "The Name of the Wind" fantasy book series

**A question-answering system over a fan wiki that will not spoil the book series
you are still reading.**

![The Streamlit interface](docs/images/streamlit_ui_1.png)
![The Streamlit interface](docs/images/streamlit_ui_2.png)

---

## The problem

A fan wiki is organised by subject, not by reading position. The page about a
character you meet in chapter three of book one also describes how they die
in book two — same page, often the same paragraph. There is no way to read a
wiki "up to where I am". Fans avoid them mid-series for exactly this reason.

A question-answering system built naively on that wiki inherits the problem
and makes it worse: it retrieves the *most relevant* passage, and the most
relevant passage is very often the one that ruins the story. Accuracy alone
is not the goal here. **The system has to be accurate about what it is
allowed to know.**

So the reader declares a **clearance** — which books they have finished — and
every one of the 1,761 passages in the corpus carries a **book level**: the
earliest book by which its content is public. Retrieval never sees anything
above the reader's clearance. Not "the model is told not to mention it":
the passage is not in the search results at all.

Note: this playfully simulates an AI safety measure, where you do not want the
RAG system giving out sensitive information.

---

## Architecture

![The retrieval path end to end: both arms, the clearance filter applied inside each query, fusion, rerank, answer with citations](docs/images/rag-pipeline-diagram.png)

---

## Quickstart


### Prerequisites

| | need | check |
|---|---|---|
| Docker | Engine + Compose **v2** | `docker compose version` |
| uv | runs every `make` target below, and fetches its own Python — your system version does not matter | `uv --version`; install with `curl -LsSf https://astral.sh/uv/install.sh \| sh`, then restart your shell |
| Memory | **4 GB available to Docker** | see below |
| Disk | ~5 GB free | |
| Ports | 9200, 5432, 8501, 3000 free | |
| OpenAI | an API key with credit | ~$0.004 for a full index build |

> **Under 4 GB of memory available to Docker?** Open the repo in a
> [GitHub Codespace](https://github.com/features/codespaces) instead — the
> default 2-core machine has 8 GB and runs this stack unchanged. Ports 8501
> and 3000 are forwarded automatically; open them from the **Ports** tab.
> On macOS and Windows, Docker Desktop caps memory well below your machine's
> total (often at 2 GB by default) — check
> *Settings → Resources* before assuming you have enough.

### 1. Clone and configure

```sh
git clone https://github.com/Lighfe/RAG-kingkiller-wiki.git
cd RAG-kingkiller-wiki
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. The other variables ship with working
defaults for local use — leave them alone.

### 2. Check your environment

```sh
make check
```

Reports on Docker, memory, disk, the four ports and your `.env`, and prints
the fix next to anything that fails. It makes no network calls; add
`--check-api-key` to confirm your OpenAI key is live (a free metadata call
that consumes no tokens):

```sh
python3 scripts/preflight.py --check-api-key
```

Fix anything marked **FAIL** before continuing. **WARN** rows are safe to
proceed past: a port collision is usually this project's own containers from
an earlier run, and the reranker-weights row warns until you have built a
corpus, because until then you are simply earlier in this list than the check
is.

### 3. Everything else, in one command

```sh
make quickstart
```

Fetches the reranker weights, starts Elasticsearch, builds and indexes the
corpus, starts the stack, and prints the URLs. About two minutes and ~$0.004
on a machine that passes step 2. It stops at the first failure and names the
stage; every stage is safe to re-run.

```
  App      http://localhost:8501
  Grafana  http://localhost:3000
```

- **App** — pick a reading level in the sidebar, ask a question, expand the
  sources, leave feedback.
- **Grafana** — provisioned automatically; fills as you use the app.


### Every target, and what it actually runs

`make` is the entry point, not a build system: every target below is one
command. If you would rather not use `make`, run the middle column instead —
it is what the target does, verbatim. `make` on its own prints this list.

| target | what it runs | cost |
|---|---|---|
| `make` / `make help` | prints this list | free |
| **`make quickstart`** | **the five stages below, in order, stopping at the first failure** | **~$0.004** |
| `make check` | `python3 scripts/preflight.py` | free |
| `make models` | `uv run python -m ingest.download_model Xenova/ms-marco-MiniLM-L-6-v2` | free, ~88 MB |
| `make ingest-free` | `uv run python scripts/run_pipeline.py --from-labels` | ~$0.004 |
| `make ingest` | `uv run python scripts/run_pipeline.py` | ~$1.68 + ~$0.004 |
| `make ingest-plan` | `uv run python scripts/run_pipeline.py --from-labels --dry-run` | free |
| `make up` | `docker compose up -d --wait`, then prints the two URLs | free |
| `make down` | `docker compose down` — containers only, volumes and data untouched | free |
| `make test` | `uv run pytest -q` | free |
| `make labels` | `uv run python scripts/export_chunk_labels.py` | free |

`make quickstart` is these five, in this order:

| | command | why here |
|---|---|---|
| 1 | `python3 scripts/preflight.py --check-api-key` | fails now rather than four minutes in. `--check-api-key` because a key the API rejects would otherwise die at stage 4 |
| 2 | `make models` | the app builds a cross-encoder before it can answer |
| 3 | `docker compose up -d --wait elasticsearch` | stage 4 indexes into it |
| 4 | `make ingest-free` | builds the corpus and the index |
| 5 | `make up` | starts the rest and prints the URLs |

Every stage is safe to repeat, so the answer to a failure is always: fix it,
run `make quickstart` again. `make models` skips files it already has; the
ingest stages rebuild from scratch by design, which costs the ~$0.004 of
embeddings again each time.

**Labelling the corpus cost \$1.68 of API calls, and you do not have to spend
it again.** The labels — and only the labels, no wiki prose — are committed
as `data/chunk_labels.jsonl`. The merge step reattaches them by passage id
and verifies each one against a content hash, so a passage whose wiki text
has changed since labelling is refused rather than silently given a stale
label. Only the vector index has to be done again at ~$0.004 token costs.

### Reproducibility

**The running system is four containers.** `docker-compose.yml` defines all of
them — Elasticsearch, Postgres, the Streamlit app, Grafana — each with a
healthcheck, which is what lets `make up` block until the URLs it prints
actually answer. The app is the only image built here: `Dockerfile` installs
into `python:3.12-slim` with `uv sync --frozen --no-dev`. Grafana's datasource
and its dashboard are provisioned from `monitoring/grafana/` on startup, not
clicked together by hand.

**uv is what the host needs**, for the two things that are deliberately not
containerized: building the corpus and running the tests. `uv run` fetches its
own Python and installs from the committed `uv.lock`, so the host and the app
container resolve to identical dependency versions — `pyproject.toml` carries
ranges, the lock file is the pin, and `uv sync --frozen` is the install that
refuses to drift from it.

---

## For reviewers: where each criterion lives

One row per scoring criterion, pointing at the file that implements it. The
numbers behind these rows are in the three evaluation documents, linked from
the rows that need them.

| criterion | implementation | what to look at |
|---|---|---|
| **Problem description** | — | the top of this file: a wiki cannot be read "up to where I am", and a naive RAG system over one makes it worse |
| **Retrieval flow** | [app/rag.py](app/rag.py) | `answer()` is the whole flow in one function: retrieve → compose. The knowledge base is Elasticsearch ([app/search.py](app/search.py)), the LLM composes from the retrieved passages only ([app/answer.py](app/answer.py)) |
| **Retrieval evaluation** | [ingest/significance_check.py](ingest/significance_check.py) | four approaches, one module each — BM25 grid ([text_search_tuning.py](ingest/text_search_tuning.py)), 3 embedding models ([embedding_bakeoff.py](ingest/embedding_bakeoff.py)), hybrid RRF ([hybrid_search_rrf.py](ingest/hybrid_search_rrf.py)), cross-encoder rerank ([reranker.py](ingest/reranker.py)) — and every comparison between them run through the bootstrap in the left column. The shipped config is pinned in [app/search.py](app/search.py) to the run that measured it |
| **LLM evaluation** | [app/eval_prompts.py](app/eval_prompts.py) | three prompt variants scored on identical retrieved context; the shipped one is [app/prompts.py](app/prompts.py). The judge was itself audited by hand — [scripts/build_judge_audit.py](scripts/build_judge_audit.py) |
| **Interface** | [app/ui.py](app/ui.py) | Streamlit: clearance radio, question box, per-source expanders, 👍/👎. The module docstring says why the clearance control is the product |
| **Ingestion pipeline** | [scripts/run_pipeline.py](scripts/run_pipeline.py) | four stages, script-driven, no notebooks — see the table below |
| **Monitoring** | [app/db.py](app/db.py) | writes `interactions` (one row per question) and `feedback` (one row per rating); the seven panels read straight from those two tables |
| **Containerization** | [docker-compose.yml](docker-compose.yml) | four services, healthchecked; [Dockerfile](Dockerfile) builds the app image |
| **Reproducibility** | [uv.lock](uv.lock) | see [Reproducibility](#reproducibility) above; `make test` runs 804 tests over [tests/](tests/) |
| *Best practice:* **hybrid search** | [ingest/hybrid_search_rrf.py](ingest/hybrid_search_rrf.py) | keyword and vector fused with reciprocal rank fusion; evaluated, and reported as a tie — see below |
| *Best practice:* **document reranking** | [ingest/reranker.py](ingest/reranker.py) | cross-encoder over the fused top 50, ships on |
| *Best practice:* **query rewriting** | [app/rewrite.py](app/rewrite.py) | implemented, measured twice, ships **off** — the measurement did not support it |

**The ingestion pipeline** is [scripts/run_pipeline.py](scripts/run_pipeline.py),
which runs four stages in order and stops at the first failure:

| stage | module | what it does | cost |
|---|---|---|---|
| 1 | [ingest/fetch_pages.py](ingest/fetch_pages.py) | 464 wiki pages as raw markup, ~13 API requests | free |
| 2 | [ingest/chunk_pages.py](ingest/chunk_pages.py) | section-aware chunking → 1,761 passages | free |
| 3 | [ingest/label_llm.py](ingest/label_llm.py) | assigns each passage its book level. `--from-labels` reattaches the committed labels instead of paying for them again | free / **$1.68** |
| 4 | [ingest/build_elasticsearch_index.py](ingest/build_elasticsearch_index.py) | embeds and indexes 1,761 passages | **$0.004** |

Every stage writes a manifest under `data/` and is gated on schema and content
hashes afterwards ([ingest/checks.py](ingest/checks.py)), so a stage that
half-succeeded fails instead of passing bad data downstream.

---

## Results at a glance

**Retrieval** — 200-question benchmark, half of it deliberately corrupted
with typos (`data/eval/reranking_v3_full_nocorr.json`):

| stage | hit@1 | hit@3 | hit@10 | MRR@10 |
|---|---|---|---|---|
| keyword + vector, fused | 0.67 | 0.87 | 0.965 | 0.7785 |
| **+ cross-encoder rerank (ships)** | **0.695** | 0.90 | 0.98 | **0.8074** |

"hit@1" is how often the correct passage ranked first; MRR@10 rewards ranking
it early rather than merely finding it.

**Spoiler containment** — the filter held everywhere it was checked:

| check | result |
|---|---|
| retrieved passages above the reader's clearance | **0** of 60 retrievals |
| deliberately withheld passages that leaked back in | **0** of 20 |
| label accuracy against blind hand-labelling | **77/84 = 0.917** (threshold ≥ 0.90, set in advance) |
| book-2 content correctly caught on an adversarial sample | **40/49 = 0.816** (threshold ≥ 0.80) |

**And where it does not hold:** 49 of the 1,188 passages labelled book-1
(4.1%) actually disclose book-2 content, and in testing the system composed
spoilers out of them. The filter is exact; the labels underneath it are not. That is the
honest limit and [docs/spoiler-gate.md](docs/spoiler-gate.md) §5 is about it.

**Things that were built and then removed on evidence:**

| component | measurement | outcome |
|---|---|---|
| BM25 field boosts | best setting +0.0094 MRR@10, sign-stable in only 0.7792 of resamples | **off** |
| Infobox-type correction | +0.26 MRR@10 on infobox passages, −0.04 on prose — and prose carries 152 of the 200 benchmark questions | **removed** |
| LLM query rewriting | measured twice; best arm +0.0021, sign-stable in 0.6297 | **off by default** |
| Hybrid vs vector search alone *(v1 set, n=148)* | +0.0012 MRR@10, sign-stable in 0.5257 — a coin flip | **kept, reported as a tie** |

The first three rows are measured on the 200-question v3 benchmark; the
fourth is the one comparison never re-run on it, because there is no
vector-only arm in the v3 harness — see
[docs/retrieval-evaluation.md](docs/retrieval-evaluation.md) §3.

A difference counts in this project only if it keeps its sign in ≥90% of
bootstrap resamples. Three components failed that bar and were removed rather
than kept for the sake of the feature list. The reranker that ships also
fails it (0.854) and ships anyway, on a stated judgment — that argument is in
[docs/retrieval-evaluation.md](docs/retrieval-evaluation.md) §6.

### Where the full workings are

**Start with [docs/spoiler-gate.md](docs/spoiler-gate.md).** It is the
shortest of the three and it explains what the system is actually for; the
other two are the measurements behind it. Read
[docs/retrieval-evaluation.md](docs/retrieval-evaluation.md) next if you care
how the search was tuned, and
[docs/llm-evaluation.md](docs/llm-evaluation.md) if you care how the
answering was validated. None of them assumes you have read the others.

---

## The Streamlit app

Once everything is set up, open the app at http://localhost:8501.

Pick a reading level in the sidebar — which books you have already finished:

| clearance | covers |
|---|---|
| book 1 | *The Name of the Wind* |
| book 2 | *The Wise Man's Fear* |
| book 3 | speculation, plus the author's comments on the upcoming *The Doors of Stone* |

Type a question and press Enter, or click **Ask**. You then see the 10 most
relevant passages the system found for it, in rank order; the ones marked ★
are the ones the answer cited. If the search finds nothing at your clearance,
the app says so instead of making something up.

Note: each query costs up to $0.005 in tokens.

---

## The Grafana dashboard

Once you have asked a few questions, they show up on the dashboard at
http://localhost:3000. Seven panels, provisioned automatically:

| panel | what it shows |
|---|---|
| Questions over time | load |
| Latency p50 / p95 | how fast the system answers — p50 is the median, p95 the 95th percentile, which is where the slow tail shows |
| Token cost per day | spend — below, ~$0.05 for 35 answers |
| 👍 vs 👎 | user ratings, up to one per query |
| Clearance distribution | which reading level askers selected |
| Insufficient-context rate | how often the model did not have enough context to answer — which is good when it means refusing to spoil, and bad when it means retrieval found nothing |
| Spoiler gate | retrievals that returned content above the reader's clearance; the correct reading is always "0 of N" |

![The monitoring dashboard](docs/images/grafana.png)

---

## Working notes — optional

You do not need any of this to review the project. The three documents linked
above carry the evidence; everything here is the project's own record of how
it got there.

| where | what |
|---|---|
| `docs/decisions/` | 71 numbered decisions with the reasoning, including approaches tried and abandoned |
| `docs/evidence-inventory.md` | every scoring criterion mapped to the artifact and number that supports it — including the gaps |
| `tasks/`, `reports/`, `notebooks/` | the task specs the project was built from, the corpus exploration behind the chunking rules, and two interactive explorers |
| `docs/archive/` | superseded documents, kept as record |

---

## Attribution and licensing

The corpus is the text of the
[Kingkiller Chronicle Fandom wiki](https://kingkiller.fandom.com), licensed
[CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). This project
credits the wiki and its contributors as the source of all corpus text, and
the app cites the source page of every passage it answers from.

**The corpus prose itself is not redistributed here.** Because of the
licence's share-alike clause, the files containing wiki text — the page
cache, both chunk files, and the curated samples — are gitignored. Everything
else under `data/` is committed: the manifests, every evaluation artifact,
the question sets, and the label export. A reviewer can therefore check every
number in this repository without the corpus, and rebuild the corpus from the
wiki in about a minute.

The fetcher is hard-locked to `kingkiller.fandom.com`. The separately-run
`kingkiller.wiki` is CC BY-**NC**-SA and licence-incompatible, so the code
refuses any other host by design.

Built for the DataTalksClub LLM Zoomcamp 2026 capstone.
