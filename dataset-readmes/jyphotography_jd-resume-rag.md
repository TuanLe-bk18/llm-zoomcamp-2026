# jd-resume-rag

**Paste a job description → get a grounded match score, gap analysis, and an
ATS-optimized resume — generated from a real career knowledge base via RAG.**

## Demo

**Run** — paste a JD, watch the 7-step pipeline stream live, then read the match
report (covered / partial / missing) and download the generated ATS resume:

![Run tab: pipeline + match report](demo/run.png)

**Monitoring** — runs per day, match-score distribution, per-stage latency,
tokens, thumbs feedback, ATS coverage:

![Monitoring tab: six charts](demo/monitoring.png)

**Evals** — retrieval hit-rate/MRR across four strategies, plus resume prompt
A/B (`select` vs `rewrite`) judged 1–5:

![Evals tab: retrieval + LLM results](demo/evals.png)

## Problem

Tailoring a resume to every job posting is slow, and generic LLM rewrites
hallucinate skills the candidate doesn't have. This app treats one candidate's
career history (10 years: data engineering, MLOps, forward-deployed engineering)
as a retrieval corpus. For any pasted JD it:

1. parses the JD into structured requirements and ATS keywords,
2. rewrites it into search queries over the knowledge base (query rewriting),
3. retrieves evidence with hybrid search + re-ranking,
4. scores the match per requirement (covered / partial / missing) with honest gaps,
5. generates a one-page ATS resume — **by selection under procedural skills**,
   not free rewriting: authored procedures in `skills/` tell the model how to
   pick bullets and draft Summary/Skills; experience bullets are inserted
   **verbatim** from the knowledge base (≥3 per company), so experience content
   cannot be hallucinated — and
6. checks deterministic ATS keyword coverage, then saves the resume to `output/`.

Every step streams live into a monitoring dashboard

### Memory model

- **Semantic memory** — facts about the candidate: `data/knowledge_base.jsonl`
  (bullets, stories, skill chunks) and `data/candidate.json` (name, contact,
  company timeline). Retrieved via Qdrant for matching; bullets/skills feed
  resume assembly.
- **Procedural memory** — how to tailor a resume: committed `skills/resume-*.md`
  (selection / summary / skills-section procedures) plus deterministic assembly
  in `app/resume_builder.py`. The LLM follows the skills; it does not invent
  Experience text.
- **Episodic memory** — run traces, SQLite monitoring, thumbs feedback, and
  `output/` resumes are observational only (not yet fed back into generation).

`data/knowledge_base.jsonl` — local career corpus (achievement bullets, STAR
stories, project deep-dives, skill groups) with metadata (`company`, `role`,
`dates`, `tags`, `type`). **Not committed** (may contain PII); start from
`data/knowledge_base.example.jsonl`.

`data/candidate.json` — local identity for resume headers (name, contact,
company order / timeline, certifications). **Not committed**; start from
`data/candidate.example.json`. The `companies[].key` values must substring-match
`company` fields in the knowledge base (e.g. key `"Acme"` matches
`"Acme Data Labs"`).

Optionally regenerate the JSONL via `ingest/export_source.py` from private
sources (anonymization map; export fails if forbidden terms leak). Generated
resumes under `output/` are also gitignored.

## Architecture

```
                         ┌─ semantic memory ─────────────────────────────┐
                         │  candidate.json (identity)                    │
                         │  knowledge_base.jsonl → Qdrant (hybrid+rerank) │
                         └───────────┬───────────────────┬───────────────┘
                                     │                   │
JD text ──> jd_parse ──> query_rewrite ──> retrieve ──> match_score
                                                         │
                                                    gap_analysis
                                                         │
              ┌─ procedural memory ──────────────────────┤
              │  skills/resume-*.md (how to select/draft) │
              │  resume_builder.py (verbatim assembly)   │
              └──────────────────────┬───────────────────┘
                                     ▼
              ats_check <── resume_generate (select: ids + summary/skills)
                                     │
                                     ▼
                         ┌─ episodic (observe only) ─────────────────────┐
                         │  .runtime/traces · monitoring.db · output/    │
                         │  👍/👎 feedback (charts; not yet closed-loop)  │
                         └───────────────────────────────────────────────┘
```

- **Memory harness:** semantic facts (KB + candidate) for retrieval and
  grounded bullets; procedural skills + deterministic builder for how to
  tailor; episodic traces/feedback for monitoring (not yet distilled back).
- **Knowledge base:** Qdrant (named dense vector `BAAI/bge-small-en-v1.5` +
sparse BM25, both embedded locally via fastembed — no embedding API cost).
- **LLM:** pluggable provider (`LLM_PROVIDER=anthropic|openai`), generation +
judge models configurable; resume path defaults to skill-driven `select`
(rewrite kept as eval baseline).
- **Observability:** every pipeline step emits observer events → appended to
JSONL traces (`.runtime/traces/`) and streamed to the browser over SSE.
- **Storage:** SQLite (`.runtime/monitoring.db`) for runs, tokens, feedback.
- **UI:** stdlib `http.server` + vanilla JS (no build step): live pipeline
diagram, match report, evidence, rendered resume with download, feedback
buttons, monitoring charts, eval results.



## Quickstart

```bash
# 1. deps (Python 3.11+, uv)
make install
cp .env.example .env        # add ANTHROPIC_API_KEY (or OPENAI_API_KEY + LLM_PROVIDER=openai)

# 2. local personal data (gitignored — may contain PII)
cp data/knowledge_base.example.jsonl data/knowledge_base.jsonl
cp data/candidate.example.json data/candidate.json
# edit both: JSONL = achievement corpus; candidate.json = name/contact/companies

# 3. ingest into embedded Qdrant (no Docker needed)
make ingest

# 4. run the dashboard
make run                    # http://localhost:7788
```

Or fully containerized (Qdrant server + app):

```bash
docker compose up --build   # http://localhost:7788
```

`QDRANT_URL=local` (default) uses Qdrant's embedded mode; docker-compose sets
`QDRANT_URL=http://qdrant:6333` for server mode. Ingestion is idempotent and
runs automatically on app start if the collection is missing.

> Embedded mode is single-process (file lock): stop the dashboard before running
> `make ingest`, `make test`, or `make eval-retrieval` locally. Server mode
> (docker) has no such limit.



## Evaluation



### Retrieval (4 strategies)

Ground truth: an LLM generates 3 JD-style queries per chunk
(`python -m evals.ground_truth`, committed as `evals/ground_truth.jsonl`), then:

```bash
make eval-retrieval
```

compares **keyword (BM25) / dense / hybrid (RRF) / hybrid+cross-encoder-rerank**
on hit-rate@5 and MRR@5 and records the winner in `evals/retrieval_results.json`
(shown in the dashboard's Evals tab). The best strategy is the pipeline default.

### LLM (prompt A/B + judge)

```bash
make eval-llm
```

runs the full pipeline on 3 sample JDs × 2 resume-generation modes
(**select**: fixed template + verbatim bullet selection vs **rewrite**: free-form
grounded generation), scores each output with an LLM judge on grounding /
relevance / ATS quality / clarity plus deterministic keyword coverage, and
records the winner in `evals/llm_results.json`.

### Deterministic tests

```bash
make test    # dataset schema + anonymization, retrieval sanity, full pipeline
             # plumbing with a scripted LLM (no API key needed)
```



## Monitoring

Dashboard → Monitoring tab: 6 charts (runs per day, match-score distribution,
avg latency per stage, tokens per run, user feedback 👍/👎, ATS coverage per
run) plus totals. Feedback is collected per run in the UI.

## Zoomcamp rubric map


| Criterion               | Where                                                               |
| ----------------------- | ------------------------------------------------------------------- |
| Problem description     | this README                                                         |
| Retrieval flow          | knowledge base (Qdrant) + LLM pipeline (`app/pipeline.py`)          |
| Retrieval evaluation    | `evals/retrieval_eval.py` — 4 strategies, best selected             |
| LLM evaluation          | `evals/llm_eval.py` — 2 prompts, judge-scored, best selected        |
| Interface               | web app (`app/dashboard.py` + `app/static/`)                        |
| Ingestion pipeline      | `ingest/export_source.py` + `ingest/pipeline.py` (automated Python) |
| Monitoring              | feedback + 6-chart dashboard                                        |
| Containerization        | `docker-compose.yml` (app + Qdrant)                                 |
| Reproducibility         | example dataset + `uv.lock`, this README                            |
| Hybrid search (bonus)   | dense + BM25 with RRF fusion                                        |
| Re-ranking (bonus)      | cross-encoder re-rank strategy                                      |
| Query rewriting (bonus) | JD → multi-query rewrite step                                       |




## Project layout

```
data/knowledge_base.example.jsonl   corpus template (committed; fictional sample)
data/candidate.example.json         identity template (committed; fictional sample)
data/export_layout.example.json     private-export path template (optional)
data/knowledge_base.jsonl           local corpus (gitignored)
data/candidate.json                 local name/contact/companies (gitignored)
data/export_layout.json             private markdown paths for export (gitignored)
output/                             generated resumes (gitignored)
skills/                             procedural memory (resume select/summary/skills)
ingest/                             export from private sources + Qdrant ingestion
app/procedural_memory.py            loads skills/*.md for the select path
app/rag/                            retrieval strategies, prompts, LLM providers
app/pipeline.py                     the observable 7-step pipeline
app/tracing.py                      JSONL tracer (observer pattern)
app/store.py                        SQLite monitoring store
app/dashboard.py                    stdlib HTTP server (SSE + static UI)
app/static/                         vanilla-JS frontend
evals/                              deterministic tests, ground truth, retrieval + LLM evals
demo/                               dashboard screenshots (Run / Monitoring / Evals)
```

