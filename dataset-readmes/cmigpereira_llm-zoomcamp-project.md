# Resiliência PT

Local, bilingual emergency-preparedness answers grounded in official Portuguese
guidance.

> [!IMPORTANT]
> Resiliência PT is for preparation only. It does not provide live alerts, assess
> personal danger, diagnose symptoms, or replace authorities and professional
> services. Official publisher pages remain authoritative.

Resiliência PT turns fragmented public guidance about earthquakes, wildfires,
floods, heatwaves, cold weather, and storms into short Portuguese or English
answers with inspectable citations. The complete pipeline runs locally: ingestion, PostgreSQL/pgvector, embeddings, reranking, query rewriting, Qwen generation, monitoring, and the Streamlit interface. It needs no paid API and deploys to no cloud service.

## Why this project

Residents and visitors often need to search several Portuguese agency sites and
long publications to assemble a practical checklist. This project asks one narrow question: can a local RAG system make that preparedness guidance easier to use without presenting unsupported or live operational advice?

The design makes evidence and failure visible:

- answers follow the question's Portuguese or English language;
- every retained factual or actionable sentence has a numbered citation;
- source cards expose the agency, official URL, and exact indexed excerpt;
- unsupported, live-status, diagnostic, prompt-injection, and unrelated requests are refused;
- uncited model sentences are removed deterministically; an empty result becomes a safe refusal;
- questions, traces, timings, and optional non-personal feedback stay in the local PostgreSQL database.

## Measured results

The committed benchmark contains 100 grounded questions (50 manually reviewed
Portuguese/English pairs) and 20 adversarial/refusal questions (10 pairs).

| Retrieval strategy | Hit Rate@5 | MRR@5 | nDCG@5 | Mean latency |
|---|---:|---:|---:|---:|
| Lexical | 0.52 | 0.3935 | 0.3754 | 13 ms |
| Dense multilingual | 0.75 | 0.5993 | 0.5571 | 21 ms |
| Hybrid RRF | 0.79 | 0.5717 | 0.5590 | 32 ms |
| **Hybrid + reranker** | **0.85** | **0.6748** | **0.6401** | **2,415 ms** |
| Hybrid + reranker + rewrite | 0.82 | 0.6720 | 0.6318 | 6,697 ms |

The evaluated winner is written to [`config/retrieval.yaml`](config/retrieval.yaml). It exceeds the stated Hit Rate@5 ≥ 0.80 and MRR@5 ≥ 0.65 targets. A 12-case stratified, temperature-zero local-judge pilot selected the `concise` prompt. It achieved 1.00 citation coverage and language consistency, but only 0.319 essential-fact recall; this is a known small-model limitation, not a passed completeness target.
The hardened deterministic gate correctly refuses all 20 committed adversarial cases.

See [the complete evaluation report](docs/evaluation.md),
[`retrieval-evaluation.json`](docs/retrieval-evaluation.json),
[`answer-evaluation.json`](docs/answer-evaluation.json), and
[`refusal-evaluation.json`](docs/refusal-evaluation.json).

## Architecture

```mermaid
flowchart LR
    M[Versioned source manifest] --> D[dlt ingestion]
    D --> X[HTML/PDF extraction]
    X --> C[Section-aware chunks<br/>400-token target, 500-token cap]
    C --> E[multilingual-e5-small]
    E --> P[(PostgreSQL 17<br/>pgvector)]

    Q[PT or EN question] --> S[Scope and safety gate]
    S --> W[Optional PT + EN query rewrite]
    S --> L[PostgreSQL full-text search]
    S --> V[pgvector cosine search]
    W --> L
    W --> V
    L --> R[Reciprocal-rank fusion]
    V --> R
    R --> CE[Multilingual cross-encoder]
    CE --> O[Ollama + Qwen3 1.7B]
    O --> G[Language + sentence citation gate]
    G --> UI[Streamlit answer and evidence]
    UI --> T[(Traces and feedback)]
    T --> MON[Seven-chart monitoring page]
```

Stable SHA-256 document and chunk IDs make ingestion idempotent. Full documents, chunks, vectors, conversations, timings, citations, feedback, and evaluation runs share one local PostgreSQL database. Details are in
[docs/architecture.md](docs/architecture.md).

## Technology choices

| Component | Local open technology | Purpose |
|---|---|---|
| App | Streamlit 1.54.0 | Multipage chat, source library, monitoring, methodology |
| Ingestion | dlt 1.15.0, Trafilatura, Beautiful Soup, PyMuPDF | Audited HTML/PDF extraction and staging |
| Database | PostgreSQL 17 + pgvector 0.8.5 | Knowledge, vectors, traces, feedback, evaluations |
| Embeddings | `intfloat/multilingual-e5-small` (pinned revision) | Portuguese/English dense retrieval |
| Lexical search | PostgreSQL `tsvector`/`tsquery` | Free local keyword retrieval |
| Fusion/reranking | Weighted RRF + multilingual mMARCO MiniLM (pinned revision) | Hybrid retrieval and cross-encoder reranking |
| Rewrite/judge/generation | Ollama 0.32.0 + Qwen3 1.7B | Apache-licensed local inference |
| Packaging | Python 3.12.11, uv lockfile, Docker Compose | Repeatable CPU-first setup |

Linux containers use the official CPU-only PyTorch index, avoiding multi-gigabyte
CUDA wheels. Ollama may use hardware acceleration when the host supports it.

## Quick start

Requirements:

- Docker Desktop or Docker Engine with Compose v2;
- approximately 12 GB of free disk space;
- 16 GB RAM recommended;
- internet access on the first run to download official publications and model
  weights. Normal use is local afterward.

Start everything:

```bash
docker compose up --build
```

The first run pulls Qwen3 1.7B, caches the embedding and reranker models, fetches 13 official publications, and performs one idempotent ingestion before starting the app. Depending on the connection and CPU, allow 10–30 minutes. Open <http://localhost:8501>. PostgreSQL is available on port `5432` and Ollama on `11434` for local inspection. All published ports bind to `127.0.0.1`, so the app, database, and model API are not exposed to the local network.

Check health in another terminal:

```bash
docker compose exec app resiliencia-pt smoke
```

Expected corpus state for the locked manifest is 13 documents and 198 unique
chunks. Re-running the ingestion service does not create duplicates:

```bash
docker compose run --rm ingest
```

Stop containers while preserving downloaded models and database data:

```bash
docker compose down
```

Remove the named volumes only when you intentionally want a completely fresh
download:

```bash
docker compose down --volumes
```

## Example questions

- `O que devo preparar em casa antes de um sismo?`
- `What should I do when an earthquake starts?`
- `Como posso proteger uma pessoa idosa durante uma onda de calor?`
- `What should I avoid when driving near a flood?`
- `Como preparo pessoas com mobilidade reduzida para uma evacuação?`
- `What precautions should I take during strong winds?`

Try a refusal as well: `Qual é o aviso meteorológico atual para Lisboa?`

## Reproduce ingestion and evaluation

The Docker workflow is the simplest:

```bash
# Full 100-question retrieval comparison; updates the selected strategy
docker compose --profile evaluation run --rm retrieval-evaluation

# Committed 12-case stratified prompt pilot
docker compose --profile evaluation run --rm answer-evaluation

# Full 120-case prompt run (slow on CPU)
docker compose --profile evaluation run --rm answer-evaluation \
  resiliencia-pt evaluate answers --judge
```

For local development with [uv](https://docs.astral.sh/uv/):

```bash
uv sync --frozen --extra dev
uv run resiliencia-pt build-benchmark
uv run ruff check .
uv run pytest

export DATABASE_URL='postgresql+psycopg://resiliencia:resiliencia@localhost:5432/resiliencia'
export OLLAMA_BASE_URL='http://localhost:11434'
uv run resiliencia-pt ingest
uv run resiliencia-pt evaluate retrieval
uv run resiliencia-pt evaluate answers --limit 12 --judge
uv run resiliencia-pt evaluate refusals
```

Integration tests are opt-in so the normal suite also works without Docker:

```bash
TEST_DATABASE_URL='postgresql+psycopg://resiliencia:resiliencia@localhost:5432/resiliencia' \
  uv run pytest -m integration
```

## Data and attribution

The manifest locks URL, agency, hazard, language, access date, reuse note, and
normalized content checksum for every source. It includes ANEPC risk and
self-protection pages and leaflets, A Terra Treme, DGS heat guidance, APA climate adaptation/risk material, and IPMA weather information.

The repository does **not** redistribute complete raw publications. Ingestion
downloads them from the publisher, verifies the extracted-content hash, and stores only the local index. One ANEPC guide explicitly permits noncommercial
reproduction with attribution; all other entries retain conservative
link-and-attribution notes. See [docs/data.md](docs/data.md) and
[`config/sources.yaml`](config/sources.yaml).

## Repository map

```text
config/                    versioned source and evaluated runtime configuration
data/evaluation/           reviewed seed plus generated 120-case JSONL benchmark
docs/                      architecture, data, evaluation, and verification evidence
scripts/                   local model-cache initialization
src/resiliencia_pt/
  app/                     four Streamlit pages
  evaluation/              retrieval metrics, prompt checks, local judge
  ingestion/               fetch, extract, chunk, dlt stage, idempotent upsert
  retrieval/               embeddings, PostgreSQL search, RRF, rerank, rewrite
  database.py              pgvector schema, traces, feedback, monitoring queries
  rag.py                   typed answer orchestration and citation safety gate
tests/                     unit, PostgreSQL integration, and Streamlit smoke tests
```

## Known limitations

- No live alerts or live sensor/weather/fire feeds.
- Guidance is predominantly Portuguese; English answers are local translations
  grounded in Portuguese excerpts.
- A 1.7B local model trades completeness for memory footprint and latency. The
  citation gate prefers a short answer or refusal over uncited advice.
- Publisher content can change after the manifest access date. Any checksum change
  stops ingestion and requires review plus an intentional manifest update.
- Evaluation relevance is source-level; section hints and essential facts are kept for manual review and answer scoring.

See [docs/verification.md](docs/verification.md) for the observed clean-run checks.

## License

Project code, original prompts, benchmark questions, and documentation are
available under the [MIT License](LICENSE). Upstream publications and model weights retain their own terms.
