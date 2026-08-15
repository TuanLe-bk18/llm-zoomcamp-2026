# HealthBot — General Health Q&A Assistant

HealthBot is a Retrieval-Augmented Generation (RAG) application that answers
general health questions (sleep, nutrition, exercise, mental health, and
more) using a curated knowledge base of health articles. It's built as the
final project for the LLM Zoomcamp course.

**⚠️ Disclaimer:** HealthBot provides general health information for
educational purposes only. It is **not** a substitute for professional
medical advice, diagnosis, or treatment. Always consult a qualified
healthcare provider for concerns about your health.

## Table of contents

- [Problem description](#problem-description)
- [Dataset](#dataset)
- [Architecture](#architecture)
- [Evaluation results](#evaluation-results)
- [Setup instructions](#setup-instructions)
- [Usage](#usage)
- [Monitoring](#monitoring)
- [Project structure](#project-structure)
- [Evaluation criteria mapping](#evaluation-criteria-mapping)

## Problem description

People often turn to search engines with health questions and get answers
scattered across dozens of blog posts, some outdated or inconsistent. This
project builds a chatbot that retrieves relevant passages from a fixed,
reviewed set of health articles and uses an LLM to synthesize a direct,
grounded answer — with source links so the user can verify the information
themselves, and a persistent reminder that this isn't medical advice.

Example questions HealthBot can answer:

- "How much sleep do adults actually need?"
- "What's a normal blood pressure reading?"
- "How much water should I drink a day?"
- "What are the signs of burnout?"

## Dataset

The knowledge base is built from general health articles scraped from
public health blogs (e.g. Healthline, Mayo Clinic, WebMD-style content)
covering topics like sleep, nutrition, exercise, mental health, and common
health metrics.

- `data/raw/sample_articles.json` — 10 seed articles included so the project
  runs out of the box without any scraping.
- `ingestion/scrape_articles.py` — scraper to pull additional real articles
  from URLs you provide (see [Setup instructions](#setup-instructions)).

Each article has the shape:

```json
{
  "id": "sleep-001",
  "title": "How Much Sleep Do You Really Need?",
  "url": "https://...",
  "category": "Sleep",
  "text": "Most adults need between 7 and 9 hours..."
}
```

## Architecture

```
User question
     │
     ▼
┌─────────────────────────┐
│  Retrieval (rag.py)      │
│  - keyword (TF-IDF)      │
│  - vector (Ollama embed) │
│  - hybrid (weighted mix) │──► top-k relevant chunks
└─────────────────────────┘
     │
     ▼
┌─────────────────────────┐
│  Prompt construction     │  (3 styles: default / concise / cited)
└─────────────────────────┘
     │
     ▼
┌─────────────────────────┐
│  LLM generation          │  (local llama3.2 via Ollama)
└─────────────────────────┘
     │
     ▼
Answer + sources ──► logged to SQLite ──► monitoring dashboard
     │
     ▼
User feedback (👍/👎)
```

**Ingestion pipeline:** raw articles → chunked (150 words, 30-word overlap)
→ TF-IDF index + local embeddings computed via Ollama → saved to
`data/processed/index.pkl` (`ingestion/build_index.py`).

**Retrieval:** three interchangeable retrievers are implemented in
`app/rag.py` so they can be directly compared:
- **Keyword** — TF-IDF + cosine similarity
- **Vector** — Ollama `nomic-embed-text` + cosine similarity
- **Hybrid** — normalized weighted combination of both (best-practice item)

**Generation:** local `llama3.2` (served via [Ollama](https://ollama.com)),
with three selectable prompt styles (`default`, `concise`, `cited`) so we
could evaluate which produces the best answers.

> **Why Ollama instead of a cloud API?** Running everything locally means
> the entire project — ingestion, retrieval, generation, and evaluation —
> costs $0 to run and requires no API key, while still using the same
> OpenAI-compatible client interface (`openai` Python package) that cloud
> providers use. Swapping back to OpenAI, Groq, or another provider only
> requires changing the `base_url`/`api_key` in `app/rag.py`.

## Evaluation results

### Retrieval evaluation

We generated 57 test questions automatically from the knowledge base
(`evaluation/generate_ground_truth.py`, 3 questions per chunk, using the
local `llama3.2` model) and measured **Hit Rate** and **MRR** for each
retriever (`evaluation/evaluate_retrieval.py`):

| Retriever | Hit Rate | MRR |
|-----------|----------|-----|
| vector    | 1.000    | 0.956 |
| hybrid    | 1.000    | 0.904 |
| keyword   | 0.912    | 0.846 |

Full results also saved to `evaluation/retrieval_results.json`.

**Vector search performed best** on this knowledge base (MRR 0.956), narrowly
ahead of hybrid (0.904), with keyword search clearly behind (0.846). This
makes sense given the test questions were LLM-generated paraphrases of the
source text rather than exact keyword matches — vector embeddings capture
that semantic similarity better than TF-IDF alone. Based on this result,
**the app defaults to the `vector` retriever**. Hybrid search remains
available in the UI and codebase as an alternative, and may outperform pure
vector search on a larger, more keyword-heavy knowledge base.

### LLM output evaluation

We used an LLM-as-a-judge approach (`evaluation/evaluate_llm.py`, judged by
the local `llama3.2` model) to score answers from each prompt style on
**relevance** and **faithfulness** (1-5 scale each), using 15 sample
questions from the ground truth set:

| Prompt style | Avg Relevance | Avg Faithfulness |
|--------------|---------------|-------------------|
| concise      | 4.73          | 5.00 |
| default      | 4.67          | 5.00 |
| cited        | 4.47          | 5.00 |

Full results also saved to `evaluation/llm_eval_results.json`.

All three styles scored a perfect 5.00 on faithfulness — answers stayed
grounded in the retrieved context rather than hallucinating. **The concise
style scored highest on relevance** and is used as the app's default,
likely because shorter, more direct answers give the judge model less
surface area to drift off-topic. The `cited` style scored lowest, possibly
because inserting inline citations sometimes interrupted the directness of
the answer. `default` and `cited` remain available in the UI for
comparison.

## Setup instructions

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/download) (runs the LLM and embedding model locally — free, no API key needed)
- Docker + Docker Compose (optional, for containerized run)

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/healthbot.git
cd healthbot
```

### 2. Install and start Ollama

Download and install Ollama from [ollama.com/download](https://ollama.com/download).
Once installed, pull the two models this project uses:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

Ollama runs as a background service on `localhost:11434` — no need to start
it manually.

### 3. Set up a Python virtual environment

```bash
python -m venv venv
```

Activate it:
- macOS/Linux: `source venv/bin/activate`
- Windows (PowerShell): `venv\Scripts\Activate.ps1`
  (if you get an execution-policy error, run
  `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once first)

Install dependencies:

```bash
pip install -r requirements.txt
```

### 4. (Optional) Scrape more real articles

The project ships with 10 seed articles so this step is optional.

```bash
# Add article URLs to ingestion/urls.txt (one per line), then:
python ingestion/scrape_articles.py --urls ingestion/urls.txt --out data/raw/scraped_articles.json
```

Read the docstring at the top of `ingestion/scrape_articles.py` first —
it explains scraping etiquette (robots.txt, rate limiting, ToS) before you
point it at real sites.

### 5. Build the knowledge base index

This chunks all articles in `data/raw/*.json`, computes embeddings via your
local Ollama server, and saves the searchable index:

```bash
python ingestion/build_index.py
```

### 6. Run the app

```bash
streamlit run app/streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501).

### Alternative: run everything with Docker Compose

```bash
docker compose up --build
```

- App: [http://localhost:8501](http://localhost:8501)
- Monitoring dashboard: [http://localhost:8502](http://localhost:8502)

Notes:
- Ollama must still be running on your host machine (Docker Desktop exposes
  it to containers via `host.docker.internal`, already configured in
  `docker-compose.yml`).
- You still need to run step 5 (`build_index.py`) locally at least once
  before starting the containers, since the index file is mounted in via
  the `./data` volume.
- If port 8501/8502 are already in use (e.g. a local `streamlit run` is
  still active in another terminal), stop that process first — Docker can't
  bind to a port that's already taken.

## Usage

Once the app is running:

1. Type a health question in the chat box.
2. (Optional) In the sidebar, switch between retrieval methods
   (`vector` / `hybrid` / `keyword`) and answer styles
   (`concise` / `default` / `cited`) to see how they change the response —
   `vector` and `concise` are the defaults based on our evaluation results
   below. You can also toggle **query rewriting** and **re-ranking** on for
   experimentation (off by default, since they add extra local LLM calls
   and slow down responses).
3. Expand "Sources" under any answer to see which articles it was grounded in.
4. Use the 👍/👎 buttons to leave feedback — this is logged and shown in the
   monitoring dashboard.

**Example interaction:**

> **You:** How much water should I drink daily?
>
> **HealthBot:** The amount of water you should drink daily varies based on
> individual needs, but a commonly cited guideline is 8 glasses (about 2
> liters) for most people. However, this may not be suitable for everyone,
> especially those who exercise intensely, live in hot climates, or are
> pregnant or breastfeeding.
>
> *Note: This answer is based solely on the provided context and should not
> be considered medical advice.*
>
> **Sources:** How Much Water Should You Drink Daily?

## Monitoring

Run the dashboard with:

```bash
streamlit run monitoring/dashboard.py --server.port 8502
```

(or it's already running at `localhost:8502` if you used Docker Compose)

It reads from `data/healthbot.db` (created automatically the first time you
use the app) and shows:

1. Conversations over time
2. Response time distribution
3. Retrieval method usage breakdown
4. Prompt style usage breakdown
5. User feedback (👍/👎) breakdown
6. Distribution of number of sources retrieved per answer

### Screenshots

**Chat interface, answering a question with sources:**

![Chat example](screenshots/chatbot.png)

**Monitoring dashboard:**

![Monitoring dashboard](screenshots/monitoring-dash.png)

**Running the full stack with Docker Compose:**

![Docker running](screenshots/docker.png)

## Project structure

```
healthbot/
├── .streamlit/
│   └── config.toml            # custom theme (sage/teal clinical palette)
├── app/
│   ├── streamlit_app.py     # main chat UI
│   ├── rag.py                # retrieval + prompt + generation logic
│   └── db.py                  # SQLite logging (conversations + feedback)
├── ingestion/
│   ├── scrape_articles.py    # scraper for real health blog articles
│   ├── urls.txt                # list of URLs to scrape
│   └── build_index.py        # chunking + embedding + index building
├── evaluation/
│   ├── generate_ground_truth.py  # auto-generates test questions
│   ├── evaluate_retrieval.py     # compares keyword/vector/hybrid search
│   ├── evaluate_llm.py           # compares prompt styles via LLM-as-judge
│   ├── ground_truth.json         # generated test questions (57 pairs)
│   ├── retrieval_results.json    # retrieval evaluation results
│   └── llm_eval_results.json     # prompt style evaluation results
├── monitoring/
│   └── dashboard.py           # usage + feedback dashboard
├── data/
│   ├── raw/sample_articles.json   # seed dataset (10 articles)
│   ├── processed/                  # generated index (gitignored)
│   └── healthbot.db                # conversation + feedback log (gitignored)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Evaluation criteria mapping

For reviewers — quick reference to where each rubric item is addressed:

| Criterion | Where |
|---|---|
| Problem description | This README, [Problem description](#problem-description) |
| Retrieval flow (knowledge base + LLM) | `app/rag.py` |
| Retrieval evaluation (multiple approaches compared) | `evaluation/evaluate_retrieval.py`, results above |
| LLM evaluation (multiple approaches compared) | `evaluation/evaluate_llm.py`, results above |
| Interface | `app/streamlit_app.py` (Streamlit UI) |
| Ingestion pipeline | `ingestion/scrape_articles.py` + `ingestion/build_index.py` (semi-automated via script) |
| Monitoring (feedback + dashboard) | `app/db.py` (feedback capture), `monitoring/dashboard.py` (6 charts) |
| Containerization | `Dockerfile`, `docker-compose.yml` (full stack, tested end-to-end) |
| Reproducibility | Setup instructions above, no API key required, pinned `requirements.txt` |
| Best practice: hybrid search | `app/rag.py::search_hybrid`, evaluated against keyword/vector above |
| Best practice: query rewriting | `app/rag.py::rewrite_query`, toggle in sidebar |
| Best practice: document re-ranking | `app/rag.py::rerank_chunks`, toggle in sidebar |

## Notes on scope and future improvements

- The ingestion pipeline is currently a semi-automated Python script; it
  could be upgraded to a fully orchestrated pipeline (Prefect, Airflow, or
  dlt) for additional automation credit.
- Query rewriting (`app/rag.py::rewrite_query`) and document re-ranking
  (`app/rag.py::rerank_chunks`) are implemented as optional toggles in the
  sidebar (off by default, since each adds extra local LLM calls and
  noticeably slows down responses). Rewriting turns a vague question into a
  clearer search query before retrieval; re-ranking fetches a larger
  candidate pool and has the LLM re-score each one against the original
  question before keeping the top results.
- Cloud deployment (e.g. Streamlit Community Cloud, an EC2 instance, or a
  managed container service) is a natural next step for the bonus points.
  Since the current setup relies on a local Ollama server, a cloud
  deployment would need either a cloud-hosted LLM (OpenAI, Groq, etc.) or a
  cloud VM with Ollama installed alongside the app.
- This project runs entirely on free, local infrastructure (Ollama for both
  the chat model and embeddings) — no API key or billing account is
  required to reproduce any part of it, including the evaluation scripts.