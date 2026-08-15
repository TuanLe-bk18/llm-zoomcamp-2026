# SupportLens AI

**Customer support intelligence RAG agent with grounded responses, reviewer-friendly dry-run mode, and local monitoring for LLM Zoomcamp 2026.**

## Problem Statement

Customer support teams need fast, consistent, policy-aware responses, but relevant context is usually split across prior cases, policy documents, and internal playbooks. SupportLens AI packages those sources into a retrieval-first workflow that helps support agents inspect similar cases, cite policy evidence, and draft grounded recommendations.

## Features Implemented

- synthetic and public-sample ingestion with `sample`, `public-sample`, and `combined-sample` modes
- retrieval pipeline with keyword, vector, hybrid, and selected `hybrid_rerank` retrieval
- grounded answer generation with citation-ready evidence
- deterministic dry-run answer mode that works without API keys
- optional OpenAI-compatible real LLM mode when environment configuration is available
- dry-run answer-quality evaluation framework
- Streamlit reviewer interface with Ask, Monitoring Dashboard, and Evaluation Report pages
- local feedback logging and monitoring dashboard with demo events

## Architecture Summary

```text
Data sources
-> ingestion pipeline
-> normalized documents and chunks
-> keyword + vector retrieval
-> hybrid retrieval and reranking
-> grounded answer generation with citations
-> feedback logging and monitoring dashboard
-> Docker Compose runtime
```

See [docs/architecture.md](docs/architecture.md).

## Dataset Summary

SupportLens uses a mixed reproducible dataset strategy:

- synthetic SupportLens support cases for controlled evaluation
- synthetic policy documents for customer-facing rules
- synthetic playbooks for internal agent guidance
- Bitext-derived public support-case sample for broader phrasing coverage

Default reviewer mode:

- `combined-sample`

This combines the synthetic benchmark with the Bitext-derived public sample so the app can operate on a broader case set while preserving the controlled evaluation questions.

## Evaluation Results

Confirmed current Attempt 1 metrics:

- hard-set retrieval Hit Rate: `0.9167`
- hard-set retrieval MRR: `0.8083`
- hard-set dry-run answer citation validity: `1.0000`
- hard-set dry-run grounding proxy score: `0.8333`
- hard-set dry-run basic quality pass rate: `1.0000`
- hard-set dry-run section completeness: `1.0000`

## Run Locally Without Docker

1. Install Python 3.11+.
2. Install dependencies from `pyproject.toml`.
3. Prepare the combined sample knowledge base:

```bash
python -m src.ingestion.pipeline --combined-sample
```

4. Optional validation commands:

```bash
python -m src.retrieval.evaluate --sample --top-k 5 --method hybrid_rerank --eval-file data/sample/evaluation_questions_hard.jsonl
python -m src.evaluation.run_answer_evaluation --eval-file data/sample/evaluation_questions_hard.jsonl --top-k 5 --dry-run
python -m src.rag.answer --question "A customer says they were charged twice after upgrading. What should support do?" --top-k 5 --dry-run --prompt-version baseline_grounded
```

5. Launch the app:

```bash
streamlit run app/streamlit_app.py
```

## Run With Docker Compose

Build and run the Streamlit app:

```bash
docker compose up --build
```

The app is exposed at:

- `http://localhost:8501`

Docker defaults to dry-run mode and does not require real LLM secrets.

## How to Use the Streamlit App

1. Open the landing page.
2. Go to **Ask SupportLens**.
3. Keep `combined-sample` selected unless you want a narrower test mode.
4. Click **Prepare / Refresh Knowledge Base**.
5. Enter a support question or load one of the examples.
6. Generate a dry-run answer.
7. Review the answer, citations, and retrieval metadata.
8. Submit optional rating, thumbs feedback, and comments.
9. Visit **Monitoring Dashboard** to review local monitoring charts.
10. Visit **Evaluation Report** to review current retrieval and dry-run answer metrics.

## How Feedback and Monitoring Work

The Ask page logs two local event types under ignored runtime files in `data/processed/`:

- `answer_generated`
- `feedback_submitted`

The monitoring dashboard visualizes:

- questions over time
- feedback submissions over time
- rating distribution
- thumbs up vs thumbs down
- dataset mode usage
- prompt version usage
- source type distribution
- latency distribution
- dry-run vs real-mode usage

A demo button can create synthetic monitoring events for reviewer walkthroughs without committing any runtime logs.

## Known Limitations

- dry-run mode is the default and safest reviewer path
- real Qwen chat validation was blocked by provider quota or billing limits
- monitoring is local and file-backed, not production observability
- the Bitext-derived public sample is a subset, not the full public dataset
- Docker runs the app, but it does not add managed persistence or cloud deployment in this phase

## Submission Info

- repo URL: `https://github.com/KingsAxe/supportlens-ai-rag`
- final commit SHA: `<fill-after-final-commit>`

## Supporting Docs

- [docs/architecture.md](docs/architecture.md)
- [docs/public_dataset_pass.md](docs/public_dataset_pass.md)
- [docs/streamlit_interface.md](docs/streamlit_interface.md)
- [docs/monitoring_dashboard.md](docs/monitoring_dashboard.md)
- [docs/submission_checklist.md](docs/submission_checklist.md)
- [docs/screenshots.md](docs/screenshots.md)
