[Español](README.es.md) | **English**

# Course Assistant

A RAG agent that answers questions about a course's material *and* its academic data — from
the same chat, deciding on its own which one a question needs.

## The problem

A course accumulates, over the years, a folder of scattered files: lecture notes as PDFs,
assignment sheets as Word docs, slide decks as PowerPoints, a syllabus/attendance policy, and
grade & attendance spreadsheets. The instructor loses time hunting for which file has what, and
can't answer an aggregate question ("how many students passed this year?") without opening a
spreadsheet by hand.

There are, in fact, **two different kinds of question** hiding behind "ask the course assistant":

| Type | Example | How it's answered |
|---|---|---|
| Document search | *"Where are the exercises on improper integrals?"* | hybrid search over text chunks |
| Data / analytics | *"How many students passed the first term in 2025?"* | read-only SQL over the normalized spreadsheets |

A plain RAG pipeline (embed everything, retrieve chunks, hand them to the LLM) **handles the
first case well and fails the second**: no chunk of a grade spreadsheet lets you *count* or
*average* over the whole table. So this project isn't a fixed RAG chain — it's an **agent with
three tools** that decides, per question, whether to search the material or query the data.

This makes it a reasonably realistic template for "a chatbot over my organization's messy folder
of documents plus a database," not just a course demo — swap the corpus and the grading vocabulary
for your own domain and most of the architecture still applies.

> **Note on language**: the assistant's content, prompts, and UI are in **Spanish** (Argentine
> Spanish, specifically) because the target use case is an Argentine university course. The
> synthetic demo course is "Análisis Matemático II" (Calculus II). Everything else — code,
> identifiers, this documentation — is in English. If you adapt this for an English-speaking
> course, the string to change is `SYSTEM_PROMPT` in
> [`agent.py`](src/catedra_assistant/agent.py), plus regenerating the corpus in English.

## Architecture

```
data/synthetic/raw/ (or your own material, see "Using your own material" below)
        │
        ▼
  ingest/pipeline.py  (python -m catedra_assistant.ingest.pipeline)
        │
        ├── extract → chunk → embed ──► texto.db + vectores.db  (sqlitesearch)
        └── tabular.py → normalizes xlsx ──► academico.db (students, grades,
                                              documents, view v_condicion_final)
                                                    │
   Streamlit chat (app/chat.py) ──► agent.responder() ──► tools.py ──┤
        │                            (function-calling loop)         ├─ buscar_documentos
        │                                                             │  (hybrid RRF, see
        │                                                             │  search/hybrid.py)
        │                                                             ├─ consultar_datos_academicos
        │                                                             │  (text-to-SQL + sqltool.py,
        │                                                             │  read-only guard)
        │                                                             └─ listar_archivos
        │
        └──► db.py (PostgreSQL: conversations, messages, tool_calls,
                     llm_calls, feedback) ──► Grafana (6 panels) / dashboard.py
```

Real stack (see [`pyproject.toml`](pyproject.toml)): extraction with `markitdown` + `pypdf` /
`python-docx` / `python-pptx` / `openpyxl`; indexes with `sqlitesearch` (FTS5 text + vector);
embeddings with `sentence-transformers` (`intfloat/multilingual-e5-small`, multilingual because
the demo corpus is in Spanish — see [`config.py`](src/catedra_assistant/config.py)); LLM via the
`openai` SDK pointed at Groq/OpenAI/Ollama depending on `LLM_PROVIDER`
([`llm.py`](src/catedra_assistant/llm.py) is the only place in the project that instantiates an
LLM client); Streamlit UI ([`app/chat.py`](src/catedra_assistant/app/chat.py), dashboard at
[`app/pages/1_Dashboard.py`](src/catedra_assistant/app/pages/1_Dashboard.py)); monitoring via
PostgreSQL + Grafana provisioned as code.

## Quickstart

Requires Python 3.13+ and [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync                        # install dependencies
cp .env.example .env           # fill in an API key, see below
uv run python scripts/smoke_test_llm.py   # confirm the LLM responds and can call tools
make ingest                    # index the bundled demo corpus (data/synthetic/raw/)
make docker-up                 # bring up app + Postgres + Grafana
```

Chat at `http://localhost:8501`, Grafana at `http://localhost:3000` (`admin`/`admin` in this
local-dev setup — see [`docs/setup.md`](docs/setup.md)). Full step-by-step instructions,
including running things outside Docker and troubleshooting, are in
[`docs/setup.md`](docs/setup.md).

### Choosing an LLM provider

The project talks to the LLM exclusively through [`llm.py`](src/catedra_assistant/llm.py) via the
OpenAI-compatible chat-completions API, so switching providers is an environment variable, not a
code change:

| Provider | `.env` setup | Notes |
|---|---|---|
| **Groq** (default) | `LLM_PROVIDER=groq`, `GROQ_API_KEY=...` | Free tier, fast inference; `LLM_MODEL=llama-3.3-70b-versatile` by default. This is what the project was built and evaluated against. |
| **OpenAI** | `LLM_PROVIDER=openai`, `OPENAI_API_KEY=...`, `LLM_MODEL=gpt-4o-mini` (or any chat model with tool-calling) | Drop-in swap: same code path, no changes needed beyond `.env`. Not separately evaluated (see [`docs/evaluation.md`](docs/evaluation.md)) but the tool-calling contract is the same OpenAI API both providers implement. |
| **Ollama** (local) | `LLM_PROVIDER=ollama`, `ollama serve` running on `localhost:11434` | No API key, nothing leaves your machine — use this if the material you're indexing can't go to a third party at all. Needs a locally-pulled model with tool-calling support (e.g. `llama3.1`). |

## Using your own material

Point `DATA_DIR` in `.env` at any local folder with the expected structure
(`apuntes/`, `practicas/`, `clases/`, `examenes/`, `normativa/`, `planillas/` — see
[`docs/usage.md`](docs/usage.md) for the full layout and spreadsheet column mapping), then run
`make ingest`.

**If your material lives in Google Drive**: this project does not implement a Google Drive API
connector (OAuth, `drive.readonly` scope, etc.) — that was scoped out early on. The practical way
to use Drive content today, without downloading everything by hand, is **Google Drive Desktop in
"stream files" mode** (or `rclone mount`): it exposes your Drive as a regular local folder and
downloads each file on demand the first time something reads it, not upfront. Point `DATA_DIR` at
that virtual folder and run the ingestion normally — from the pipeline's point of view it's just a
local directory. See [`docs/setup.md`](docs/setup.md) for the walkthrough.

Real student data is sensitive: the pipeline can pseudonymize names before indexing
(`ANONYMIZE=true`), and `data/real/` is gitignored by convention so nothing you drop there gets
committed. Details in [`docs/security.md`](docs/security.md).

The repo ships with a **synthetic demo corpus** (a fictional course, "Análisis Matemático II" —
Calculus II — cycles 2024/2025) generated by
[`scripts/generate_synthetic_corpus.py`](scripts/generate_synthetic_corpus.py), so you can try
everything without any real data at all.

## What it can answer

- **Document questions** — *"Where are the exercises on Fourier series?"* → calls
  `buscar_documentos`, cites file + page/slide.
- **Analytical questions** — *"How many students passed the first term in 2024?"* → calls
  `consultar_datos_academicos`, shows the SQL it ran, returns the number (`75` in the bundled demo
  data).
- **"What material do I have?"** questions → calls `listar_archivos` without reading content.
- **Honesty on gaps**: if the search or query comes up empty, or the question is unrelated to the
  course, the agent says so explicitly instead of inventing content, files, grades, or students —
  this is a hard instruction in the system prompt, not a hope.

See [`docs/usage.md`](docs/usage.md) for the full behavior (including what it deliberately
*can't* do — writes to the data, scanned PDFs without OCR, questions needing more than 2-3
chained tool calls).

## Features

- **Hybrid document search** — BM25 keyword + vector search fused with Reciprocal Rank Fusion,
  optional cross-encoder re-ranking, with metadata filters (`doc_type`, `year`, `unit`) exposed to
  the agent. Backed by an actual evaluation over 145 questions, not a default picked by eyeballing
  four queries — see [`docs/evaluation.md`](docs/evaluation.md).
- **Read-only SQL tool** with five independent defense layers (read-only file handle, SQL
  statement whitelist via `sqlglot`, table whitelist, SQLite's own authorizer callback, row
  limit + timeout) — a hostile or broken SQL generation can't write, and can't wander outside the
  academic schema. Details in [`docs/security.md`](docs/security.md).
- **Incremental ingestion** — hashes each source file; a second run with no changes reprocesses
  nothing, so re-running ingestion is always safe.
- **Streamlit chat** with cited sources, visible tool calls, visible generated SQL, and 👍/👎
  feedback with an optional comment.
- **Monitoring** — every conversation, tool call, and LLM call is logged to PostgreSQL; a Grafana
  dashboard (provisioned as code, 6 panels) and an equivalent in-app Streamlit dashboard show
  query volume, tool-usage split, latency, token/cost, feedback ratio, and (once wired up) judge
  relevance scores.
- **Everything containerized** — `docker compose up` brings up the app, Postgres, and Grafana
  together; ingestion runs as an on-demand one-shot service.

## Documentation

- [`docs/setup.md`](docs/setup.md) — detailed install & run instructions, all environment
  variables, and troubleshooting (port conflicts, Grafana first-login, missing OCR, etc.).
- [`docs/usage.md`](docs/usage.md) — how to use the chat and dashboard, what the agent can and
  can't answer, and the spreadsheet-to-database column mapping.
- [`docs/security.md`](docs/security.md) — the SQL read-only model, PII pseudonymization, and how
  to plug in real course material without publishing it.
- [`docs/evaluation.md`](docs/evaluation.md) — executive summary of the four evaluations
  (retrieval, generation, agent routing, analytical accuracy), each backed by a detailed report in
  [`eval/`](eval/) (in Spanish — the evaluation questions and generated answers are in Spanish, so
  the analysis stays in the same language as its data).

## Testing

```bash
make test
# equivalent: uv run pytest -m "not slow and not requires_postgres"
```

209 tests, skipping the ones that need the embedding model loaded or a real Postgres instance.
Run `uv run pytest` on its own (with the stack up) for the full suite.

## Project context

This started as the final project for DataTalks.Club's
[LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp), which is why some design choices
(a synthetic instead of a real corpus, the specific evaluation methodology) trace back to that
course's grading rubric. That context doesn't drive the documentation above — this README
describes the software as software. If you're curious about the rubric mapping specifically, the
short version: problem framing, an agent-based (not fixed-chain) retrieval flow, a real retrieval
evaluation across 3 approaches, an LLM-as-a-judge evaluation across 3 prompts, an ingestion
pipeline, a chat UI, PostgreSQL+Grafana monitoring, and full containerization are all implemented
and covered above; the one thing scoped out was a Google Drive API connector (see "Using your own
material").

## Future work

The LLM-as-a-judge evaluation (`eval/llm.md`) ran with substitute models
(`llama-3.1-8b-instant`, `openai/gpt-oss-20b`) because Groq's free daily quota for the project's
default model (`llama-3.3-70b-versatile`) was exhausted at the time, on a small sample (7
questions). Re-running it against the default model with a larger sample, once quota allows, is
a reasonable next step — noted in [`eval/README.md`](eval/README.md).
