# CSB Search

A retrieval-augmented question-answering system over U.S. Chemical Safety Board (CSB) completed investigation reports, aimed at process engineers researching incident causes, contributing factors, and safety recommendations.

Ask a question in plain English — e.g. *"What caused the pressure relief valve to fail at the West Fertilizer explosion?"* — and get back a synthesized, cited answer instead of manually searching through PDFs.

## Problem statement

The [CSB](https://www.csb.gov/) (U.S. Chemical Safety and Hazard Investigation Board) is an independent federal agency that investigates industrial chemical accidents — explosions, toxic releases, fires — and publishes a completed investigation report for each one. Every report is a lengthy PDF (often 100+ pages) describing the incident timeline, root causes, contributing factors, and the safety recommendations that came out of the investigation.

If you're a process engineer trying to answer something specific — "what caused the pressure relief valve to fail at the West Fertilizer explosion?" or "what safeguards prevent runaway reactions in batch reactors?" — there's no way to search across these reports as a corpus. You either already know which report has the answer, or you're opening PDFs one at a time.

This project builds a search agent that ingests all of CSB's completed investigation reports into searchable indexes, then answers natural-language questions by reasoning over those indexes and citing the specific report and section each part of its answer came from.

## Demo

**Streamlit UI** — ask a question, get a synthesized answer with numbered citations back to the source report:

![Streamlit app answering a question about the West Fertilizer explosion, with a cited source](docs/img/streamlit_answer.png)

**Grafana monitoring dashboard** — every agent run and tool call is traced, so response time, token usage, tool-call mix, and running cost are all visible live:

![Grafana dashboard showing agent response time, token usage, tool calls per type, cumulative cost, and retry attempts](docs/img/grafana_dashboard.png)

## How it works

```
CSB.gov PDFs → Scrape/scrape.py → Markdown reports → Ingest/ingest.py → 4 SQLite search indexes
                                                                              │
                                                                              ▼
                                                        agent.py (LangChain agent + 6 search tools)
                                                                              │
                                                              ┌───────────────┴───────────────┐
                                                              ▼                                ▼
                                                        app.py (Streamlit UI)      Monitoring/sqlite_exporter.py
                                                                                    → tracer.db → Grafana
```

1. **Scrape** — download every CSB Final Investigation Report PDF and convert it to Markdown.
2. **Ingest** — chunk and index the Markdown into four SQLite-backed indexes: overlapping word chunks (for keyword search), the same chunks embedded into vectors (for semantic search), whole sections keyed by heading (for larger coherent passages), and headings alone (for browsing a report's table of contents).
3. **Agent** — a LangChain agent with one tool per index (plus a couple of exact-lookup helpers) runs a visible, structured reasoning loop: current understanding → what's missing → which tool to call next, for up to 5 tool calls, then produces a final answer with numbered references back to file + heading.
4. **Serve & monitor** — a Streamlit front end exposes the agent to end users; every run is traced with OpenTelemetry into a SQLite database that a Grafana dashboard visualizes.

### Worked example

Question: *"What caused the pressure relief valve to fail in the West Fertilizer explosion?"*

Real agent answer (captured from the running app):

> The failure of the pressure relief valve in the West Fertilizer explosion was primarily due to it being knocked off the tank during cleanup operations, likely involving crane and lift bucket activities in the area. This incident occurred prior to a site inspection on May 28, 2013, which may have contributed to the conditions leading to the explosion.
>
> 1. **west-fertilizer-explosion-and-fire-\_1** — Section discussing pressure relief valve failure

Behind the scenes, the agent picked a tool (in this case `vector_search`), found the relevant section, and had enough evidence to answer directly — no further tool calls needed. More ambiguous questions trigger multiple rounds: e.g. a heading lookup to find the right report, followed by a section fetch.

## Search evaluation results

[Evaluations/Search/search_evaluation.py](Evaluations/Search/search_evaluation.py) measures hit-rate and MRR (top 5 results) for the text and vector indexes independently, against 5,000 LLM-generated ground-truth questions each:

| Index | Hit-rate | MRR |
|---|---|---|
| Text (keyword) search | 0.827 | 0.669 |
| Vector (semantic) search | 0.505 | 0.451 |

Keyword search clearly outperforms vector search on this corpus — likely because CSB report questions tend to reference specific equipment, chemicals, and facility names verbatim, which favors exact/lexical matching over embedding similarity. This is part of why the agent has both a keyword tool (`chunk_text_search`) and a vector tool (`vector_search`) available and picks between them per query, rather than relying on vector search alone.

Field boosting (weighting certain keyword fields more heavily in the text index) was also tried, but didn't produce a noticeable improvement over the unboosted results above.

## Agent evaluation results

[Evaluations/Agent/get_agent_answers.py](Evaluations/Agent/get_agent_answers.py) ran the full agent (current system prompt, `gpt-4o-mini`) over 97 sampled ground-truth questions (total agent cost: $0.12). [Evaluations/Agent/agent_evaluation.py](Evaluations/Agent/agent_evaluation.py) then had an LLM judge (`gpt-5.4-mini`, cost: $0.02) score each run's final answer and tool-call trajectory as good/bad against the question's known-relevant source chunk:

| | Good | Bad | Good rate |
|---|---|---|---|
| Answer quality | 86 | 11 | 88.7% |
| Tool-call trajectory quality | 93 | 4 | 95.9% |

Answer quality is judged on whether the agent's answer references the same file as the ground-truth chunk and is consistent with its subject matter. Trajectory quality is judged on whether tool calls were relevant, non-redundant, and supported the final answer. Most answer failures traced back to the agent citing a plausible but different file than the one the ground-truth question was generated from — several CSB cases have multiple report files (e.g. different versions/revisions of the same investigation), so the agent's citation and the ground-truth file can both be legitimate sources for the same fact, just not an exact filename match.

### Prompt iteration experiment

Based on the failure cases above, [agent.py](agent.py)'s system prompt was rewritten to add:
- **Grounding rules** requiring every specific fact (dates, publication years, standard numbers, quantities) to come verbatim from a retrieved chunk rather than the model's own training knowledge, and forbidding citing a file unless the specific claim next to it was actually retrieved from that file.
- **A search strategy** telling the agent to filter subsequent searches to a file once identified (to reduce cross-file drift), and to retry with a different tool/query before giving up with "I don't know" instead of stopping after one failed search.
- Broadening an overly narrow decision rule ("a result is irrelevant when the chemical name doesn't match") to general subject-matching, and removing a `[self]`-tagged outside-knowledge exception that conflicted with the new grounding rules.

Re-running the same evaluation pipeline with the new prompt (a different random sample, 78 questions after some hit OpenAI rate limits) gave:

| | Good rate (original prompt, n=97) | Good rate (revised prompt, n=78) |
|---|---|---|
| Answer quality | 88.7% | 82.1% |
| Tool-call trajectory quality | 95.9% | 93.6% |

Both numbers moved slightly *down*, not up. Reading through the individual judge explanations for the revised run's failures, 9 of 14 bad answers were the same failure mode as before — content judged correct and on-topic, just citing a different (but real) file than the one ground truth happened to sample. The new instructions aimed at exactly this didn't move it. Given the sample sizes and that the samples aren't identical between runs, this isn't a fully controlled comparison, but there's no evidence of improvement, so **the prompt change was reverted** — the results and evaluation data documented above reflect the original prompt currently in `agent.py`. This pattern looks more like a limitation of the ground-truth methodology (one file per question, when the same fact often legitimately appears in multiple report files) than something a prompt change can fix.

## Evaluation criteria

This section maps typical project-evaluation criteria to where they're addressed in this repo, so a reviewer doesn't have to hunt for them:

| Criterion | Where it's addressed |
|---|---|
| **Problem description** | [Problem statement](#problem-statement) above |
| **Retrieval flow** (knowledge base + LLM) | [How it works](#how-it-works); implemented in [agent.py](agent.py) |
| **Retrieval evaluation** (multiple approaches compared) | [Search evaluation results](#search-evaluation-results) — hit-rate/MRR for text vs. vector search, computed by [Evaluations/Search/search_evaluation.py](Evaluations/Search/search_evaluation.py) against LLM-generated ground truth |
| **RAG/agent evaluation** | [Agent evaluation results](#agent-evaluation-results) — LLM-as-judge scoring of answer quality and tool-call trajectory quality, computed by [Evaluations/Agent/get_agent_answers.py](Evaluations/Agent/get_agent_answers.py) + [Evaluations/Agent/agent_evaluation.py](Evaluations/Agent/agent_evaluation.py) |
| **Interface** | Streamlit UI ([app.py](app.py)), see [Demo](#demo) |
| **Ingestion pipeline** (automated) | [Scrape/scrape.py](Scrape/scrape.py) → [Ingest/ingest.py](Ingest/ingest.py), fully scripted, no manual steps |
| **Reproducibility** | Pinned dependencies via `uv.lock`, Docker/Docker Compose setup, prebuilt indexes committed to the repo — see [Setup](#setup) |
| **Monitoring** | OpenTelemetry tracing of every agent run/tool call into `tracer.db`, visualized in a 5-panel Grafana dashboard (response time, token usage, tool-call mix, cumulative cost, retry attempts) — see [Demo](#demo) |
| **Containerization** | [Dockerfile](Dockerfile) + [docker-compose.yml](docker-compose.yml) run the app and Grafana |
| **Best practices** | Hybrid retrieval (separate keyword and vector indexes, plus structural section/heading indexes the agent can choose between), structured JSON reasoning loop with a bounded tool-call budget, retry-with-backoff on transient LLM failures |

## What I built

**Data pipeline**
- [Scrape/scrape.py](Scrape/scrape.py) — crawls csb.gov's completed-investigations listing, downloads each case's Final Investigation Report PDF (verifying it's actually an "Investigation Report" from the cover page, not an update/appendix), and converts each PDF to Markdown with `pymupdf4llm`. Retries with backoff and resumes safely if interrupted. Output goes to `Scrape/data/Completed_Investigations/`.
- [Ingest/ingest.py](Ingest/ingest.py) — turns the Markdown reports into four searchable SQLite indexes under `Ingest/data/`:
  - `chunk_text_index.db` / `chunk_vector_index.db` — fixed-length overlapping word chunks (100 words, 25-word overlap), indexed for keyword search and, after embedding with `all-MiniLM-L6-v2`, for vector (semantic) search.
  - `section_text_index.db` — one entry per Markdown heading and its full body text, for keyword search over larger, structurally-coherent passages.
  - `headings_text_index.db` — headings only, for discovering a report's table of contents.
- [embedder.py](embedder.py) — a minimal `all-MiniLM-L6-v2` embedder using `onnxruntime` + `tokenizers` directly (tokenize → run the ONNX graph → mean-pool → L2-normalize), instead of `sentence-transformers`/`torch`. Keeps the dependency footprint small (no torch, no CUDA). [download.py](download.py) fetches the ONNX weights + tokenizer from the `Xenova/all-MiniLM-L6-v2` Hub repo into `models/Xenova/all-MiniLM-L6-v2/` (gitignored; re-run `python download.py` after a fresh checkout).
- [load_db.py](load_db.py) — shared helpers for opening these indexes (via the `sqlitesearch` library).

**Search agent**
- [agent.py](agent.py) — a LangChain agent (`gpt-4o-mini` by default) with six tools, one per index plus exact-lookup variants (`chunk_text_search`, `vector_search`, `section_text_search`, `headings_text_search`, `get_headings_by_file`, `get_sections_by_heading`). A system prompt forces the agent into a visible, structured JSON reasoning loop (current understanding → missing information → next tool call) for up to 5 tool calls, then a final JSON answer with numbered references back to file + heading. Every agent run and tool call is traced with OpenTelemetry into `Monitoring/data/tracer.db` via a custom exporter ([Monitoring/sqlite_exporter.py](Monitoring/sqlite_exporter.py)), and the whole call is retried on transient failure.
- [app.py](app.py) — a minimal Streamlit front end: enter a question, get the agent's answer and its numbered source references.

**Evaluation**
- [Evaluations/Search/generate_ground_truth_text.py](Evaluations/Search/generate_ground_truth_text.py), [Evaluations/Search/generate_ground_truth_vector.py](Evaluations/Search/generate_ground_truth_vector.py), [Evaluations/Agent/generate_ground_truth_agent.py](Evaluations/Agent/generate_ground_truth_agent.py) — use an LLM to generate realistic natural-language questions from sampled chunks, producing labeled ground-truth CSVs (`ground_truth_text.csv`, `ground_truth_vector.csv`, `ground_truth_agent.csv` in their respective `data/` folders, plus the shared `Evaluations/data/ground_truth_docs.csv`).
- [Evaluations/Search/search_evaluation.py](Evaluations/Search/search_evaluation.py) — measures hit-rate and MRR of the raw text and vector indexes against their ground truth.
- [Evaluations/Agent/get_agent_answers.py](Evaluations/Agent/get_agent_answers.py) — runs the full agent over a sample of ground-truth questions, capturing the final answer, full tool-call trajectory, and cost (`Evaluations/Agent/data/agent-answers.csv`).
- [Evaluations/Agent/agent_evaluation.py](Evaluations/Agent/agent_evaluation.py) — LLM-as-judge scoring of each agent run's answer quality and tool-call trajectory quality as good/bad (`Evaluations/Agent/data/agent-evaluations.csv`).
- [Evaluations/evaluation_utils.py](Evaluations/evaluation_utils.py) — shared helpers: structured LLM calls with retry, cost calculation, and a concurrent `map_progress` runner with a progress bar.

**Monitoring**
- `docker-compose.yml` runs a Grafana instance provisioned ([Monitoring/grafana/provisioning](Monitoring/grafana/provisioning)) with the `frser-sqlite-datasource` plugin pointed at `Monitoring/data/tracer.db`, so agent queries, tool calls, token usage, and cost can be visualized.

**Tests**
- [tests/](tests/) — pytest suite covering the agent's tools (`test_agent.py`), ingestion logic (`test_ingest.py`), and index loaders (`test_load_db.py`). `conftest.py` stubs out the embedding model and SQLite index loading at import time so tests don't need the real (200+MB) index files.

## Project structure

```
load_db.py                    # shared index-loading helpers
agent.py                      # LangChain search agent + tools + tracing
app.py                        # Streamlit UI

Scrape/
  scrape.py                   # download + convert CSB reports to Markdown
  data/Completed_Investigations/  # downloaded source PDFs (gitignored)

Ingest/
  ingest.py                   # build the four search indexes from Markdown
  data/
    Input data/                   # converted Markdown reports (ingest.py reads this)
    chunk_text_index.db, chunk_vector_index.db
    section_text_index.db, headings_text_index.db

Evaluations/
  evaluation_utils.py             # shared evaluation helpers
  data/ground_truth_docs.csv      # shared ground-truth source documents
  Search/
    generate_ground_truth_text.py, generate_ground_truth_vector.py
    search_evaluation.py          # hit-rate / MRR for text & vector search
    data/                         # ground_truth_{text,vector}.csv, ground_truth_*_index.db
  Agent/
    generate_ground_truth_agent.py
    get_agent_answers.py          # run agent over ground-truth questions
    agent_evaluation.py           # LLM-judge scoring of agent answers
    recover_agent_answers.py
    data/                         # ground_truth_agent.csv, agent-answers.csv, agent-evaluations.csv

Monitoring/
  sqlite_exporter.py           # OpenTelemetry -> tracer.db exporter
  data/tracer.db                # agent run/tool-call traces
  grafana/provisioning/         # Grafana datasource config for tracer.db

docs/img/                     # README screenshots
tests/                        # pytest suite

Dockerfile, docker-compose.yml
```

The four index `.db` files under `Ingest/data/` (`chunk_text_index.db`, `chunk_vector_index.db`, `section_text_index.db`, `headings_text_index.db`) are committed to the repo, so a fresh checkout can run the app immediately without re-scraping or re-ingesting anything.

## Setup

Requirements: Python 3.14, [uv](https://docs.astral.sh/uv/), an OpenAI API key. Docker + Docker Compose if you want to run it containerized.

1. Create a `.env` file in the project root with:
   ```
   OPENAI_API_KEY=sk-...      # required — used by the agent LLM and ground-truth/eval scripts

   # optional, for LangSmith tracing of agent runs (separate from the Grafana/OpenTelemetry monitoring below)
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=...
   LANGSMITH_PROJECT=...
   ```
   `OPENAI_API_KEY` is the only variable actually required to run the app — the `LANGSMITH_*` ones only matter if you want LangSmith's hosted tracing UI in addition to the local Grafana dashboard.

## Running it

### Option A — Docker Compose (recommended)

```bash
docker compose up app
```
Serves the Streamlit UI at http://localhost:8501, using the index `.db` files already in the repo — no ingestion step required. The image only installs the core app dependency group (see below) — scraping, ingestion, and evaluation are host-side only, run with `uv` (Option B).

Optional extra:
```bash
# start Grafana (traces/costs from Monitoring/data/tracer.db), at http://localhost:3000
docker compose up grafana
```
Login with the Grafana default credentials — username `admin`, password `admin`. It'll prompt you to set a new password on first login (safe to skip for local/dev use). The `CSB_Agent monitoring` dashboard (shown in the [Demo](#demo) above) is what you land on.

### Option B — Local with uv

```bash
uv sync
python download.py   # fetch the ONNX embedding model into models/ (one-time)
streamlit run app.py
```

`pyproject.toml` splits dependencies into groups — `scrape`, `ingest`, `eval`, and `notebook` (plus `dev` for pytest) sit on top of the core app dependencies. Plain `uv sync` installs all of them by default, matching this section; the Docker image installs only core.

To rebuild the indexes locally instead of using the committed ones:
```bash
python Scrape/scrape.py all   # download CSB report PDFs and convert to Markdown
# move/copy the converted Markdown files into "Ingest/data/Input data/"
python Ingest/ingest.py       # rebuild chunk/vector/section/headings indexes
```

### Tests

```bash
uv run pytest
```

### Evaluation (optional, calls the OpenAI API)

```bash
python Evaluations/Search/generate_ground_truth_text.py     # ground truth for text search
python Evaluations/Search/generate_ground_truth_vector.py   # ground truth for vector search
python Evaluations/Agent/generate_ground_truth_agent.py     # ground truth for full agent eval
python Evaluations/Search/search_evaluation.py              # hit-rate / MRR for text & vector search
python Evaluations/Agent/get_agent_answers.py                # run the agent over sampled questions
python Evaluations/Agent/agent_evaluation.py                 # LLM-judge scoring of agent answers
```

## Tech stack

LangChain / LangGraph agent orchestration, OpenAI (`gpt-4o-mini`) for the agent LLM, `onnxruntime` + `tokenizers` (`all-MiniLM-L6-v2`, no torch) for embeddings, `sqlitesearch` (SQLite-backed text + LSH vector indexes), Streamlit UI, OpenTelemetry + Grafana for tracing/monitoring, `pymupdf4llm` + BeautifulSoup for report scraping/conversion, pytest for tests.
