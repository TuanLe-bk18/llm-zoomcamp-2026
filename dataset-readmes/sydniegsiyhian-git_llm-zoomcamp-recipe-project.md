# 🍳 Recipe Cooking Assistant

A RAG (Retrieval-Augmented Generation) application that answers cooking
questions -- "what can I make with eggplant and garlic?", "how do I make
baigan chokha?" -- by searching a database of ~13,500 real recipes and
generating grounded answers with an LLM.

This is a project for the [DataTalksClub LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp)
(Attempt 1). It is written for readers who have **not** taken the course --
no assumed knowledge of the course videos or terminology.

> This project's evaluation criteria come from the
> [official project.md](https://github.com/DataTalksClub/llm-zoomcamp/blob/main/project.md#evaluation-criteria).
> Each section below is labeled with the criterion it addresses, to make
> reviewing easier.

---

## Problem description

Home cooks often know a few ingredients they have on hand, or remember a
dish by a rough description, but don't know the exact recipe name or the
steps to make it. Searching a huge recipe site by keyword often returns
irrelevant results, and a plain LLM (with no data behind it) may hallucinate
plausible-sounding but wrong recipes and quantities.

This project builds a small, focused Q&A assistant over a real recipe
dataset: the user asks a question in plain language, the app retrieves the
most relevant recipe(s) from the dataset, and an LLM turns that into a
direct, grounded answer -- citing which recipe it used.

## Dataset

- Source: [josephrmartinez/recipe-dataset](https://github.com/josephrmartinez/recipe-dataset)
  (CC BY-SA 3.0), originally scraped from Epicurious and published on Kaggle.
- ~13,500 recipes with `Title`, `Ingredients`, and `Instructions` columns.
- Not the DataTalksClub FAQ documents used elsewhere in the course (those are
  explicitly disallowed for the project).
- The ingestion pipeline downloads a random sample of 2,000 recipes by
  default (configurable) to keep indexing fast in a Codespace; the full
  dataset can be used by passing `--sample-size -1`.

---

## Architecture

```
                 ┌─────────────────┐
User question -> │  query rewrite  │  (bonus: LLM rewrites question -> search query)
                 └────────┬────────┘
                          v
                 ┌─────────────────┐
                 │  hybrid search  │  (text + vector, combined via RRF)
                 └────────┬────────┘
                          v
                 ┌─────────────────┐
                 │  LLM re-ranking │  (bonus: LLM reorders candidates)
                 └────────┬────────┘
                          v
                 ┌─────────────────┐
                 │  prompt + LLM   │  (Groq, llama-3.1-8b-instant)
                 └────────┬────────┘
                          v
                     Grounded answer + sources
                          |
                          v
              logged to SQLite (question, answer, retrieval
              method, latency, feedback) -> monitoring dashboard
```

## Retrieval flow *(criterion: Retrieval flow)*

The app uses both a knowledge base (the recipe index) and an LLM (Groq
`llama-3.1-8b-instant`) -- the question is never sent to the LLM without
retrieved context first.

## Retrieval evaluation *(criterion: Retrieval evaluation)*

Three retrieval approaches are implemented and compared in
`eval/evaluate_retrieval.py`:

| Method | Description |
|---|---|
| `text` | Keyword/TF-IDF search via `minsearch.Index` |
| `vector` | ONNX embeddings (`fastembed`, BAAI/bge-small-en-v1.5) + `minsearch.VectorSearch` |
| `hybrid` | Reciprocal Rank Fusion (RRF) of the two rankings above |

Evaluation uses an LLM-generated ground truth set (`eval/generate_ground_truth.py`
asks the LLM to write realistic questions per recipe) and reports **Hit
Rate** and **MRR** for each method. The best method (by MRR) is saved to
`data/best_retrieval_method.json` and used automatically by the app.

## LLM evaluation *(criterion: LLM evaluation)*

Three prompt templates (`baseline`, `structured`, `step_by_step`) are
compared in `eval/evaluate_llm.py` using an LLM-as-a-judge that scores each
generated answer on **relevance** and **groundedness** (1-5 each). The
best-scoring prompt is saved to `data/best_prompt.json` and used automatically
by the app.

## Interface *(criterion: Interface)*

A Streamlit chat UI (`app/app.py`) -- ask a question, get an answer with
source recipes shown, and give 👍/👎 feedback per answer.

## Ingestion pipeline *(criterion: Ingestion pipeline)*

`ingestion/ingest.py` is a fully automated Python script using **dlt**: it
downloads the CSV, cleans and chunks each recipe into one retrievable
document, and loads it into DuckDB. No manual/notebook steps required.

## Monitoring *(criterion: Monitoring)*

Every conversation (question, rewritten search query, answer, retrieval
method, response time, number of sources, user feedback) is logged to SQLite
(`app/monitoring.py`). `app/dashboard.py` renders a Streamlit dashboard with:

1. Conversations per day
2. Response time over time
3. Retrieval method usage
4. Feedback breakdown (👍/👎/none)
5. Number of sources returned per answer
6. A recent-conversations table

Both user feedback collection **and** a 5+ chart dashboard are included.

## Containerization *(criterion: Containerization)*

`docker-compose.yml` defines three services: `ingest` (one-off setup),
`app` (chat UI, port 8501), and `dashboard` (monitoring, port 8502) -- the
whole stack runs via `docker compose up`, no dependency has to be installed
manually.

## Best practices implemented *(criterion: Best practices)*

- ✅ **Hybrid search** -- combines text and vector search via RRF, evaluated
  against each approach individually in `eval/evaluate_retrieval.py`.
- ✅ **Document re-ranking** -- `RecipeRAG.rerank()` in `rag/rag.py` asks the
  LLM to reorder retrieved candidates by true relevance before answering.
- ✅ **Query rewriting** -- `RecipeRAG.rewrite_query()` in `rag/rag.py`
  turns a conversational question into a keyword-friendly search query
  before retrieval.

---

## Reproducibility *(criterion: Reproducibility)*

### 1. Prerequisites

- Python 3.12 (or use the provided Docker setup instead -- see below)
- A free [Groq API key](https://console.groq.com/keys)

### 2. Clone and set up

```bash
git clone <this-repo-url>
cd llm-zoomcamp-project
cp .env.example .env        # then edit .env and paste your GROQ_API_KEY
pip install -r requirements.txt
```

### 3. Build the knowledge base (ingestion + indexes)

```bash
python ingestion/ingest.py --sample-size 2000   # downloads data, loads into DuckDB
python search/search.py                          # builds text + vector indexes
```

### 4. (Optional but recommended) Run evaluation

```bash
python eval/generate_ground_truth.py --num-docs 100 --questions-per-doc 5
python eval/evaluate_retrieval.py
python eval/evaluate_llm.py
```

This writes `data/best_retrieval_method.json` and `data/best_prompt.json`,
which the app reads automatically. If you skip this step, the app falls
back to sensible defaults (hybrid search, structured prompt).

### 5. Run the app

```bash
streamlit run app/app.py          # chat UI on http://localhost:8501
streamlit run app/dashboard.py    # monitoring dashboard on http://localhost:8502
```

### Or, run everything with Docker

```bash
cp .env.example .env   # then edit with your GROQ_API_KEY
docker compose --profile setup run ingest   # one-off: builds data/
docker compose up app dashboard             # starts both services
```

- App: http://localhost:8501
- Dashboard: http://localhost:8502

---

## Project structure

```
.
├── ingestion/
│   └── ingest.py              # dlt pipeline: download, clean, chunk, load to DuckDB
├── search/
│   └── search.py              # text / vector / hybrid retrieval
├── eval/
│   ├── generate_ground_truth.py
│   ├── evaluate_retrieval.py
│   └── evaluate_llm.py
├── rag/
│   └── rag.py                 # core RAG flow: rewrite -> retrieve -> rerank -> answer
├── app/
│   ├── app.py                 # Streamlit chat UI
│   ├── dashboard.py           # Streamlit monitoring dashboard
│   └── monitoring.py          # SQLite logging
├── data/                      # generated at runtime (git-ignored)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Technologies used

| Purpose | Tool | Covered in course? |
|---|---|---|
| LLM | Groq (`llama-3.1-8b-instant`) | Yes |
| Text search | `minsearch` | Yes |
| Vector embeddings | `fastembed` (ONNX) | Yes |
| Ingestion | `dlt` + DuckDB | Yes |
| Interface | Streamlit | Yes |
| Monitoring storage | SQLite | Yes |
| Containerization | Docker + docker-compose | Yes |

## License

Code in this repository: MIT (or your preferred license).
Dataset: [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/), per
the [source dataset's license](https://github.com/josephrmartinez/recipe-dataset).
