# 🎲 Game Board Rules Helper

A RAG assistant that answers questions about board game rules, setup, and playtime — grounded in an actual game knowledge base instead of a generic (and possibly hallucinated) LLM answer.

> **For reviewers:** this README is organized so each grading criterion in `project.md` maps to one section below. Jump straight to [Evaluation Criteria Map](#evaluation-criteria-map) if you just want to find where to score something.

---

## Table of Contents

- [Problem Description](#problem-description)
- [Evaluation Criteria Map](#evaluation-criteria-map)
- [Architecture](#architecture)
- [Dataset](#dataset)
- [Setup & Run Instructions](#setup--run-instructions)
- [Retrieval Evaluation](#retrieval-evaluation)
- [LLM (RAG) Evaluation](#llm-rag-evaluation)
- [Interface](#interface)
- [Monitoring](#monitoring)
- [Containerization](#containerization)
- [Screenshots](#screenshots)
- [Repo Layout](#repo-layout)

---

## Problem Description

New or infrequent players constantly interrupt game night to look up rules: *"how many cards do I draw?"*, *"how long does this actually take?"*, *"can I play this with only two people?"*

**Game Board Rules Helper** is a RAG assistant over a structured board-game knowledge base (game name, genre, player count, playtime, complexity, setup instructions, and rules summary) that answers these questions instantly, grounded in the retrieved rules/setup text for the relevant game — rather than a generic answer the LLM might invent on its own.

**Audience:** board game groups / game nights.
**Pain point:** rules-lookup friction mid-game.
**Mechanism:** retrieval-grounded answers, not free-form LLM guessing.

---

## Evaluation Criteria Map

| Rubric item | Where it's covered |
|---|---|
| Problem description | [Problem Description](#problem-description) |
| Retrieval flow (KB + LLM) | [Architecture](#architecture), `src/search.py`, `src/rag_helper.py` |
| Retrieval evaluation | [Retrieval Evaluation](#retrieval-evaluation), `notebooks/retrieval_eval.ipynb` |
| LLM evaluation | [LLM (RAG) Evaluation](#llm-rag-evaluation), `notebooks/rag_eval.ipynb` |
| Interface | [Interface](#interface), `app.py` |
| Ingestion pipeline | `src/ingest.py` (see [Dataset](#dataset)) |
| Monitoring | [Monitoring](#monitoring), `src/dashboard.py` |
| Containerization | [Containerization](#containerization), `Dockerfile` / `docker-compose.yml` |
| Reproducibility | [Setup & Run Instructions](#setup--run-instructions) |

---

## Architecture

```
User question (Streamlit)
        │
        ▼
   SEARCH  (SQLite FTS5 — keyword search over game_name, genre,
            setup_instructions, rules_summary, with per-field BM25 boosting)
        │  top-k matching games
        ▼
   PROMPT  (instructions + question + retrieved game context)
        │
        ▼
    LLM    (OpenAI Responses API, gpt-5.4-mini)
        │
        ▼
   Answer + logged to SQLite (question, answer, tokens, cost, latency)
        │
        ▼
   Streamlit "Monitoring" tab reads the log back and charts it
```

Each stage is swappable in isolation (e.g. FTS5 could be replaced with a vector index without touching the prompt or LLM code.

**Stack:** Codespaces + devcontainer · OpenAI (`gpt-5.4-mini`) · SQLite (FTS5 for search, plain tables for logging) · Streamlit (UI + monitoring dashboard) · Docker (containerization).

---

## Dataset

The dataset is a synthetic, LLM-generated set of board games (`data/games.csv`), produced by `data/generate_dataset.py` using structured output (`pydantic` + OpenAI's `responses.parse`). Each row has:

| Field | Description |
|---|---|
| `id` | Stable id, e.g. `game-001` (used to check retrieval correctness during evaluation) |
| `game_name` | Name of the game |
| `genre` | Strategy, Party, Cooperative, Card Game, etc. |
| `player_count` | e.g. `2-4 players` |
| `playtime_minutes` | Average playtime |
| `complexity` | Light, Medium, Heavy |
| `setup_instructions` | How to set the game up |
| `rules_summary` | Core rules and how to play |

`games.csv` is **committed to the repo** so reviewers can inspect the data without needing an API key.

Ingestion (`src/ingest.py`) loads the CSV into a SQLite **FTS5** virtual table (`data/games.db`, gitignored — regenerated on setup) with `game_name`, `genre`, `setup_instructions`, and `rules_summary` indexed for full-text search; `id`, `player_count`, `playtime_minutes`, and `complexity` are stored `UNINDEXED` (kept for display and filtering, not for text ranking).

```bash
python data/generate_dataset.py   # produces data/games.csv (skip if already committed)
python src/ingest.py              # builds data/games.db from games.csv
```

---

## Setup & Run Instructions

### Option A — Codespaces (recommended)

1. Open this repo in a GitHub Codespace.
2. Add your key as a Codespaces secret: **Settings → Secrets and variables → Codespaces → New repository secret**, name `OPENAI_API_KEY`.
3. Rebuild/start the Codespace. `postCreateCommand` runs `.devcontainer/setup.sh`, which:
   - installs the system `sqlite3` CLI and verifies FTS5 support (fails loudly at setup time if it's missing, rather than surfacing a cryptic `OperationalError` later),
   - creates an isolated `uv` virtual environment at `.venv` and installs `requirements.txt`,
   - installs this repo in editable mode (`uv pip install -e .`) so `src` is importable from notebooks.
4. Open a new terminal (or `source ~/.bashrc`) so the venv auto-activates, then:
   ```bash
   python src/ingest.py
   streamlit run app.py
   ```
   The Streamlit tab (port 8501) opens automatically.

### Option B — Local / Docker

```bash
git clone <repo-url>
cd game-board-rules-helper
cp .env.example .env        # add your OPENAI_API_KEY
docker build -t game-board-rules-helper .
docker run -p 8501:8501 -e OPENAI_API_KEY=$OPENAI_API_KEY game-board-rules-helper
```

The Dockerfile installs the `sqlite3` CLI, verifies FTS5 support at build time, and runs `src/ingest.py` during the image build so the container ships with its own populated index — the whole app (UI, search index, and log store) is self-contained in one container. A `docker-compose.yml` is included for portability and to persist `data/` across restarts.

### Dependencies

All dependency versions are pinned in `requirements.txt` (`openai`, `streamlit`, `pandas`, `pydantic`, `plotly`, `python-dotenv`, `tqdm`, `ipykernel`).

---

## Retrieval Evaluation

Retrieval quality is measured with **Hit Rate** and **MRR** (`src/evaluation_utils.py::evaluate`) against an LLM-generated ground-truth set (`notebooks/ground_truth.ipynb` → `data/ground_truth.csv`): for each game's `rules_summary`, an LLM generates several natural, player-style questions paired with that game's `id`, and retrieval is scored on whether the correct game shows up (and at what rank) for each question.

Search uses SQLite's `bm25()` ranking function with **per-field boosts** on `(game_name, genre, setup_instructions, rules_summary)` — the FTS5 equivalent of `minsearch` field boosting. `notebooks/retrieval_eval.ipynb` compares multiple boost configurations (a hand-picked set, then a systematic grid sweep) against this harness, tuned/selected on a held-out split of `ground_truth.csv` to avoid overfitting to the full set.

**Winning configuration**, wired into `src/search.py::DEFAULT_BOOSTS`:

| `game_name` | `genre` | `setup_instructions` | `rules_summary` |
|---|---|---|---|
| 0.1 | 2.0 | 0.5 | 0.5 |

> Genre is boosted well above the default weight, while game name, setup instructions, and rules text are all weighted down relative to `no_boost` — i.e. the winning config leans on genre matches more than on the longer, prose-heavy fields, which are more prone to noisy incidental keyword overlap.

| Config | Hit Rate | MRR |
|---|---|---|
| `no_boost` (1.0, 1.0, 1.0, 1.0) | 0.864 | 0.7129 |
| **`DEFAULT_BOOSTS`** (0.1, 2.0, 0.5, 0.5) — **selected** | 0.876| 0.731533 |


**Notes for reviewers on `src/search.py`:**
- `bm25()`'s weight arguments are positional against **every** column in the FTS5 table, including `UNINDEXED` ones, so `_build_bm25_weight_args` maps the 4-value boost tuple onto the full 8-column argument list rather than passing it straight through.
- `_sanitize_fts_query` quotes each token individually and joins them with `OR` (not `AND`/bare space) so natural-language questions with punctuation don't break FTS5's query parser, and so stop words in the question don't force a zero-result `AND` match.

---

## LLM (RAG) Evaluation

`notebooks/rag_eval.ipynb` runs the full RAG pipeline (`RAGBase.rag()`) over the same ground-truth questions, then uses an **LLM-as-a-judge** (`src/evaluation_utils.py::judge_answer`) to compare each generated answer against the game's actual `rules_summary`, scoring `good`/`bad` with reasoning.

| Metric | Value |
|---|---|
| Judge pass rate (`good`) | good 0.62 / bad 0.38 (normalize=True) |
| Sample size | 250 |

A random sample of 10–15 judge verdicts was manually spot-checked against the reference rules text to confirm the judge itself is reliable before reporting the number above.

---

## Interface

`app.py` is a Streamlit app with two tabs:

- **🎲 Ask** — a text box for questions, backed by the RAG pipeline, showing the answer plus which game(s) were retrieved, token usage, and response time. 👍/👎 feedback buttons follow each answer.
- **📊 Monitoring** — see below.

Run with `streamlit run app.py` (or via Docker/Codespaces as above).

---

## Monitoring

Every question is logged to SQLite (`conversations` table: question, answer, retrieved ids, tokens, cost, response time, timestamp) via `src/db.py`, and 👍/👎 feedback is logged to a separate `feedback` table.

The **Monitoring** tab (`src/dashboard.py`) reads this log back and renders:

1. Questions over time
2. Response time distribution
3. Cost per question over time
4. Token usage breakdown (input vs. output)
5. User feedback (👍 vs 👎 counts)

...plus summary metrics (total questions, total cost, average response time). This satisfies both halves of the Monitoring criterion — feedback collection **and** a 5+ chart dashboard.

---

## Containerization

A single `Dockerfile`:
- installs the `sqlite3` CLI and verifies FTS5 support at build time (fails the build, not the app, if the base image lacks it),
- installs pinned dependencies from `requirements.txt`,
- runs `src/ingest.py` during the build so the image ships with a populated `games.db`,
- runs `streamlit run app.py` on container start (port 8501).

Because SQLite is just a file (no separate database service like Postgres), the app, search index, and log store are all self-contained in one container. `docker-compose.yml` is also provided, mounting `./data` as a volume so `games.db` and the conversation log persist across container restarts.

```bash
docker build -t game-board-rules-helper .
docker run -p 8501:8501 -e OPENAI_API_KEY=$OPENAI_API_KEY game-board-rules-helper
# or:
docker compose up
```

---

## Screenshots
**Asking a Question**

![Asking a question](<images/Ask question.png>)

**Question answered**

![alt text](<images/Question answered.png>)

**Giving feedback**

![alt text](<images/Giving Feedback.png>)

**Monitoring**

![alt text](images/Monitoring.png)


---

## Repo Layout

```
game-board-rules-helper/
├── .devcontainer/
│   ├── devcontainer.json
│   └── setup.sh
├── data/
│   ├── generate_dataset.py
│   ├── games.csv            # committed — no API key needed to inspect the data
│   └── ground_truth.csv     # committed — evaluation test set
├── src/
│   ├── __init__.py
│   ├── paths.py
│   ├── ingest.py
│   ├── search.py
│   ├── rag_helper.py
│   ├── db.py
│   ├── dashboard.py
│   └── evaluation_utils.py
├── notebooks/
│   ├── ground_truth.ipynb
│   ├── retrieval_eval.ipynb
│   └── rag_eval.ipynb
├── app.py
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore                # excludes data/games.db, keeps games.csv & ground_truth.csv
└── README.md
```

`data/games.db` is gitignored and rebuilt via `src/ingest.py`; `data/games.csv` and `data/ground_truth.csv` are committed so the project is reproducible without regenerating data from the LLM.

---