# OpenCV `geometry` Module Documentation with LLM-powered Search

OpenCV's `modules/geometry` (git tag 5.0.0) contains ~1268 C++ functions, of which ~79% have zero comment directly above them (measured via ctags + heuristic scan of preceding non-blank line). Affected code includes USAC robust-estimation solvers, point-cloud processing, and template-heavy `detail::` internals.

As a Computer Vision specialist, sometimes working in C++, I suffer a lot from missing documentation and the need to navigate the codebase if I want to know the details.

The focus of the project: 
* Generate the documentation with LLM
* Build a natural-language search over this documentation

## 1. Project description

1. **Ingestion pipeline**

The pipeline is run automatically with Prefect as an orchestrator. The source code of OpenCV tag 5.0.0 is synced from the official repository, the `geometry` module is chosen, and the documents are chunked with ctags. The function body is then fed into a `gpt-4o-mini` with `prompts/describe_function.txt` prompt. Afterwards, the descriptions are embedded with local ONNX embedder `text-embedding-3-small`. Finally, the function text parameters along with vector are put into ElasticSearch index.

2. **Search architecture**

Three mods of search are implemented - text search, vector search and hybrid search, consisting of combined text + vector search. Two advanced options are implemented: query rewriting and reranking. Query rewriting uses `gpt-4o-mini` LLM to rewrite the search query. Reranking puts every query + function description combination into a `gpt-4o-mini`, which rates the relevance of the description to the query, and re-sorts the results, returned by the search engine.

3. **LLM response**

Top-5 returned function descriptions are put into a `gpt-4o-mini` along with the answer prompt to generate the text description.

4. **Evaluation of the results**

Two stages of the pipeline are evaluated - the search and the LLM response. For both of them, the evaluation dataset is generated with `gpt-4o-mini`, which was prompted to generate specific user-like questions to the whole description base, with specific function description as prompt.

The search is evaluated based on Hit Rate and Mean Reciprocal Rank (MRR). The boosting of the fields has been evaluated, as well as pure vector search, and hybrid search with different combinations of text and vector search.

The LLM response is evaluated by LLM Judge `gpt-4o-mini`, which was prompted to return the relevance, faithfullness to context and conciseness. Two prompt templates have been evaluated by these parameters.

5. **The Web UI**

The Web UI for the search has been built with a single-page Streamlit application that asks the user for prompt and shows the LLM generated result as well as top-5 search entries the LLM based its answer on. The user is asked to rate the quality of the answer, but it's optional.

6. **Monitoring**

Two PostgreSQL databases are created to monitor the usage of the app - the common search log and feedback monitoring. Latency, cost, number of usages, and feedback is monitored based on the all requests and user feedback.

7. **Orchestration**

The Prefect orchestration tool has been chosen for the orchestration purpose. This instrument has been chosen due to native Python integration. The pipeline steps contained heavy preprocessing, which I preferred to debug as pure Python scripts, and only run in Prefect UI when I made sure they were working.

## 2. Setup

### 2.1 Prerequisites

- Python ≥3.12
- [uv](https://docs.astral.sh/uv/) — package manager (no pip/requirements.txt)
- Docker & Docker Compose (for running the full stack)
- OpenAI API key

### 2.2 Install Dependencies

```bash
uv sync
```

To install only a subset of dependency groups:

```bash
uv sync --no-dev                      # production deps only
uv sync --group ingest                # + ingestion deps
uv sync --group eval                  # + eval deps
```

### 2.3 Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
cp .env.example .env
# Edit .env with your OPENAI_API_KEY
```

Required:
- `OPENAI_API_KEY` — your OpenAI API key

Optional overrides:
- `DESCRIPTION_LLM` — model for function descriptions (default: `gpt-4o-mini`)
- `ANSWER_LLM` — model for answer generation (default: `gpt-4o-mini`)
- `EMBEDDING_MODEL` — model for embeddings (default: `text-embedding-3-small`)
- `RERANK_ENABLED` — toggle re-ranking (default: `false`)
- `QUERY_REWRITE_ENABLED` — toggle query rewriting (default: `false`)

### 2.4 Running the Full Stack (Docker Compose)

```bash
# Start all services (ES, Postgres, Grafana, Prefect server, Streamlit app)
docker compose up -d

# View logs
docker compose logs -f app
```

Services:
- **Streamlit app**: http://localhost:8501
- **Grafana with Monitoring**: http://localhost:3000 (admin/admin)
- **Prefect server for Orchestration**: http://localhost:4200

## 3. Step execution

### 3.1 Indexing

Pre-generated `data/chunks.jsonl` with descriptions and embeddings is shipped in the
repo. To re-run ingestion from scratch:

```bash
# Make sure search_engine is running (docker compose up -d search_engine)
uv run python -m ingest.flow
```

Or via Prefect 3.x (requires `docker compose up -d prefect-server` first):

```bash
# Register the deployment with the Prefect server
prefect deploy -n ingest-deployment # register once
prefect deployment run 'ingest_flow/ingest-deployment' # trigger

# Trigger via UI at http://localhost:4200
```

### 3.2 Synthesize Evaluation Queries

Runs as a Prefect flow with retries. Two ways to execute:

```bash
# Direct execution (no Prefect server needed)
uv run python -m ingest.make_eval_set
```

Or via Prefect deployment (requires docker compose up -d prefect-server)
```bash
prefect deploy -n make-eval-set-deployment    # register once
prefect deployment run 'make_eval_set/make-eval-set-deployment'   # trigger
```

### 3.3 Evaluation

#### Retrieval Evaluation

Compare text, vector, and hybrid (≥2 RRF variants) modes:

```bash
uv run python -m eval.eval_retrieval
```

Or via Prefect deployment (requires docker compose up -d prefect-server)
```bash
prefect deploy -n eval-retrieval-deployment    # register once
prefect deployment run 'eval_retrieval/eval-retrieval-deployment'   # trigger
```

Results written to `data/results/retrieval_eval.csv`. The mode with the highest
MRR@10 becomes the default in the app.

#### Generation Evaluation

Compare prompt variants v1 (concise) and v2 (cited + confidence):

```bash
uv run python -m eval.eval_generation
```

Or via Prefect deployment (requires docker compose up -d prefect-server)
```bash
prefect deploy -n eval-generation-deployment    # register once
prefect deployment run 'eval_generation/eval-generation-deployment'   # trigger
```

Results written to `data/results/generation_eval.csv`.

## 4. Evaluation Results

### 4.1 Retrieval

| Mode | hit_rate@5 | hit_rate@10 | mrr@10 |
|------|------------|-------------|--------|
| text (best: desc=2, sig=0.5, qname=2, body=0.5) | 0.9067 | 0.9533 | **0.7523** |
| vector | 0.62 | 0.72 | 0.43 |
| hybrid_rrf30 | 0.9333 | 0.9867 | 0.6789 |
| hybrid_rrf60 | 0.9333 | 0.9867 | 0.6789 |
| hybrid_rrf90 | 0.9333 | 0.9867 | 0.6789 |
| hybrid_rrf120 | 0.9333 | 0.9867 | 0.6789 |

*Default mode: **text** — highest MRR@10 (0.7523). See `data/results/retrieval_eval.csv` for full sweep results.*

### 4.2 Generation

| Variant | mean_relevance | mean_faithfulness_to_context | mean_conciseness |
|---------|----------------|------------------------------|------------------|
| answer_v1 | 4.92 | 4.9 | 4.14 |
| answer_v2 | 4.96 | 4.92 | 4.2 |

*Default mode: **answer_v2** - both metrics are higher. See `data/results/generation_eval.csv` for full results.*

## 5. License

This project is licensed under Apache-2.0 (OpenCV source license).

## 6. AI usage claim

The code has been mostly generated by DeepSeek v4 Flash model with CLine extension of VSCode IDE. I claim to read and debug all of it.
