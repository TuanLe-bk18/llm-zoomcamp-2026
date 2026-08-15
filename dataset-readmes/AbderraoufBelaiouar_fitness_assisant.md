# Fitness Assistant

A RAG (Retrieval-Augmented Generation) application that answers questions about fitness exercises — form, muscle groups, equipment, and exercise replacements — using a dataset of 1,324 exercises.

## Features

- **Search**: keyword search over exercise records (name, muscles, equipment, instructions) with `minsearch`, plus vector search with sentence-transformers embeddings
- **LLM answers**: Groq-powered answers grounded in retrieved exercise context
- **Evaluation**: ground-truth question generation, retrieval metrics (hit rate, MRR), and RAG answer-relevance assessment
- **API** (planned): Flask interface
- **Monitoring** (planned): PostgreSQL + Grafana
- **Deployment** (planned): Docker

## Architecture

```
src/fitness_assistant/
├── ingestion/     # dataset loading, document preparation, chunking
├── search/        # keyword + vector indexes (single source of truth) and query logic
├── rag/           # RAG pipeline: retrieve -> prompt -> answer
├── llm/           # Groq client and prompt templates
├── eval/          # ground-truth generation and retrieval/RAG metrics
├── scripts/       # one-off pipeline steps (embedding generation)
└── main.py        # example usage

data/
├── raw/           # source dataset (exercises.json)
├── processed/     # prepared documents + persisted embeddings
└── eval/          # generated ground-truth retrieval questions
```

The keyword index is built once and cached: every component imports `get_index()` / `load_documents()` from `search/index.py`. The vector index (`get_vector_index()`) loads persisted embeddings from `data/processed/exercises_embeddings.json`.

## Dataset

`data/raw/exercises.json` — 1,324 exercises from the [exercises-dataset](https://github.com/hasaneyldrm/exercises-dataset) project (based on ExerciseDB v1), with multilingual instructions, muscle groups, equipment, and step-by-step guidance.

## Setup

```bash
uv sync
cp .env.example .env   # set GROQ_API_KEY
```

## Usage

Run an example query through the full RAG pipeline:

```bash
uv run python src/fitness_assistant/main.py
```

Generate and persist vector embeddings (one-off, after dataset changes):

```bash
uv run python src/fitness_assistant/scripts/build_embeddings.py
```

Generate ground-truth retrieval questions (sampled, checkpointed — safe to interrupt):

```bash
uv run python src/fitness_assistant/eval/generate_ground_truth.py --sample-size 150
```

Run retrieval evaluation (hit rate / MRR):

```bash
uv run python src/fitness_assistant/eval/evaluate_retreiver.py
```

Run RAG answer-relevance evaluation (RELEVANT / PARTLY_RELEVANT / NON_RELEVANT):

```bash
uv run python src/fitness_assistant/eval/evaluate_rag.py
```

Ground truth is written to `data/eval/ground-truth-retrieval.csv`; generation resumes where it left off and can be forced with `--force`. Generation calls the LLM per exercise, so it consumes API quota.

## Retrieval evaluation

Ground truth is generated per exercise with questions answerable only from the exercise information, so retrieval is scored by exact exercise-id match. Results on 40 questions:

| Retriever | Hit rate | MRR |
|---|---|---|
| Keyword search (tuned boost weights) | **0.95** | **0.86** |
| Vector search (MiniLM, instructions only) | 0.35 | 0.29 |

Keyword search with tuned field boosts (`search/search.py`) is the production retriever: it outperforms the current vector search by 60 points on hit rate. Tuned boosts weight the searchable fields (name, equipment, muscles, instructions) so that queries about exercises, form, and equipment match the right records.

RAG answer quality: on the same 40 questions, **67% of answers were RELEVANT** and **33% PARTLY_RELEVANT** (none NON_RELEVANT), evaluated by an LLM judge against the ground-truth questions.

## Roadmap

- Flask API (`/search`, `/answer`, `/health`)
- Query/answer logging to PostgreSQL and Grafana dashboards
- Docker + docker-compose for the full stack

## License

See [LICENSE](LICENSE).
