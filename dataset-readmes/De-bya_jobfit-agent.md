# JobFit Agent

An AI agent that analyzes how well a resume matches a job posting — not with a
generic "add more keywords" tip, but with a grounded, step-by-step breakdown of
which requirements are met, which are gaps (and how severe), and concrete,
honest suggestions for closing them.

Built as the final project for [DataTalksClub's LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp).

## Problem

Job seekers apply to dozens of postings without a clear picture of where they
actually stand: which skill gaps are dealbreakers versus minor, whether their
resume will survive an ATS keyword filter, or which postings are worth
prioritizing. JobFit Agent ingests a job posting and a resume, reasons through
the match requirement-by-requirement, and produces a structured, actionable
fit assessment.

**Scope:** professional/knowledge-work roles — software engineering, data/AI/ML,
product management, design, marketing, finance/business analysis, project
management, HR/operations. (Not manual trades, agriculture, or other
occupation categories outside this scope.)

## Architecture

A multi-step Retrieval-Augmented Generation agent — knowledge-base retrieval
feeds directly into every LLM reasoning step (see the highlighted RAG loop
in the diagram below).

![JobFit Agent architecture](resources/architecture.png)

```
Job postings (JSearch API) --[dlt pipeline]--> DuckDB (raw corpus)
                                                       |
Skills taxonomy (ESCO + O*NET) + ATS notes --[chunk+embed]--> Elasticsearch
                                                       |
                                          Streamlit UI --> JobFit Agent
                                                             |
                                                    parse -> retrieve -> reason
                                                    per-gap -> score -> suggest
                                                             |
                                                    Postgres (logging) --> Grafana
```

### Agent flow (multi-step, not a single prompt)
1. **Parse job requirements** (`agent/jobfit_agent.py::parse_requirements`) — LLM extracts structured requirements from the JD
2. **Parse resume skills** (`::parse_resume_skills`) — LLM extracts structured skills/experience
3. **Per-requirement gap analysis** (`::analyze_gaps`) — for EACH requirement individually: a
   targeted hybrid-search retrieval pass (`rag/retrieval.py::hybrid_search`) against the knowledge
   base, then an LLM call classifying severity (`Met`, `Minor/nice-to-have`,
   `Adjacent/transferable gap`, `Experience-level mismatch`, `Hard filter risk`)
4. **Score** (`::compute_fit_score`) — bounded weighted-credit formula (not raw point subtraction,
   which floors out at 0 too easily with many gaps)
5. **Suggestions** (`::generate_suggestions`) — grounded rewrite suggestions; explicitly instructed not
   to fabricate skills the candidate doesn't have
6. **Rank** (`::rank_postings`) — sorts multiple postings by fit score

## Current status

The core pipeline (ingestion, retrieval, agent, interface, monitoring) is complete and
containerized. `rag/retrieval.py` also implements HyDE query rewriting and cross-encoder
reranking as an `advanced_search` alternative; evaluation showed plain hybrid search has
the better Hit Rate for this agent's use case, so it's what the agent uses in production
(see Evaluation section) — the advanced pipeline is implemented and evaluated but not the
default. Cloud deployment is not yet done.

## Tech stack

- **LLM**: OpenAI `gpt-4o-mini`
- **Embeddings**: `sentence-transformers` (`multi-qa-MiniLM-L6-cos-v1`), local — no API cost
- **Knowledge base**: Elasticsearch (hybrid BM25 + dense vector)
- **Ingestion**: `dlt` (job postings from JSearch API), automated/re-runnable
- **Interface**: Streamlit
- **Monitoring**: Postgres (logging) + Grafana (dashboard)
- **Containerization**: Docker Compose (Elasticsearch, Postgres, Grafana, app)

## Data sources

- **Job postings**: [JSearch API](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) (RapidAPI)
- **Skills taxonomy**: [ESCO](https://esco.ec.europa.eu/) v1.1.1, via the
  [Tabiya open dataset mirror](https://github.com/tabiya-tech/tabiya-open-dataset)
  (CC BY 4.0) — occupations, skills, and occupation-to-skill relations, filtered
  to in-scope occupations
- **Skill importance / technology usage**: [O\*NET 30.3 Database](https://www.onetcenter.org/database.html)
  (US Dept. of Labor / USDOL/ETA), filtered to in-scope occupations
- **ATS behavior guidance**: original synthesis (see `data/skills_taxonomy/ats_guidance_notes.md`)
  of well-established, publicly-known ATS/recruiting-technology practices

## Screenshots

![JobFit Agent results screenshot](resources/UI.png)

![JobFit Agent results screenshot](resources/Screenshot2.png)

**Analysis results — fit score with per-requirement reasoning trace:**

![JobFit Agent results screenshot](resources/app-screenshot.png)

Each requirement is classified by severity (Met / Minor / Adjacent gap /
Experience mismatch / Hard filter risk) with its own reasoning, followed by
grounded, non-fabricated rewrite suggestions and 👍/👎 feedback capture.

![JobFit Agent results screenshot](resources/Screenshot.png)

## Configuration

Model and retrieval behavior can be adjusted via `.env` without touching code:

| Variable | Purpose | Default |
|---|---|---|
| `OPENAI_API_KEY` | LLM + judge calls | *(required)* |
| `JSEARCH_API_KEY` | Job posting ingestion | *(required)* |
| `ES_HOST` | Elasticsearch endpoint | `http://localhost:9200` (overridden to `http://elasticsearch:9200` in Docker) |
| `POSTGRES_DSN` | Monitoring DB connection | `postgresql://jobfit:jobfit@localhost:5432/jobfit_monitoring` (overridden in Docker) |

## Setup

### Prerequisites
- Docker Desktop
- Python 3.12, a virtual environment
- API keys: OpenAI (`OPENAI_API_KEY`), JSearch/RapidAPI (`JSEARCH_API_KEY`)

### 1. Environment
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env  # then fill in your real API keys
```

### 2. Download the knowledge base source data
Place these in `data/skills_taxonomy/`:
- ESCO skills/occupations/relations CSVs — see `load_knowledge_base.py` header comments for exact URLs
- O*NET `essential_skills.csv`, `software_skills.csv`, `occupation_data.csv` from
  https://www.onetcenter.org/database.html#tabular

### 3. Start infrastructure
```bash
docker compose up -d elasticsearch postgres grafana
```

### 4. Load the knowledge base
```bash
python load_knowledge_base.py
```

### 5. Ingest job postings
```bash
python ingestion/pipeline.py
```

### 6. Initialize monitoring schema
```bash
python monitoring/monitoring_db.py
```

### 7. Run the app
Either directly:
```bash
streamlit run app/streamlit_app.py
```
Or fully containerized:
```bash
docker compose up -d --build app
```
Open http://localhost:8501.

Grafana dashboard: http://localhost:3000 (default login `admin`/`admin`).

## Evaluation

### Retrieval evaluation
Compared four strategies against a 53-question LLM-generated eval set
(ground truth: which knowledge-base chunk each question was generated from).

| Strategy | Hit Rate | MRR |
|---|---|---|
| Vector (kNN) | 0.679–0.698 | 0.560–0.569 |
| Text (BM25) | 0.698 | 0.546 |
| **Hybrid (RRF)** | **0.717** | 0.521 |
| Advanced (HyDE rewrite + rerank) | 0.679 | **0.604** |

**Chosen for production use: Hybrid (RRF).** It has the best Hit Rate — the
metric that matters most here, since the agent reasons over the full top-k
result set rather than only the top-1 result. The advanced pipeline (query
rewriting + reranking) achieves the best MRR, meaning it ranks correct
results higher *when found*, but its HyDE rewriting step reduces recall on
this dataset — likely because most queries here are already close in style
to the indexed documents, so rewriting doesn't help as much as it would for
vaguer queries, and it adds meaningful latency/cost (an extra LLM call and a
reranker pass per query) for a metric that matters less to this specific
agent design. All three "best practice" techniques (hybrid search, query
rewriting, reranking) are implemented and evaluated in `rag/retrieval.py`;
hybrid was selected on the evidence rather than by default.

### LLM evaluation
Compared two prompting strategies for the gap-analysis task, scored by an
LLM-as-judge (specificity, actionability, groundedness; 1-5 each) across 3
resume/posting pairs.

| Strategy | Specificity | Actionability | Groundedness | Overall |
|---|---|---|---|---|
| Naive (single prompt, no retrieval) | 4.00 | 3.00 | **5.00** | 4.00 |
| **Structured + grounded (retrieval + explicit steps)** | 4.00 | **3.67** | 4.67 | **4.11** |

**Chosen: structured + grounded.** Wins clearly on actionability — the
dimension that matters most for the tool's actual purpose (helping a
candidate act on the analysis) — while giving up only a small amount of
groundedness, plausibly because the judge weighs literal resume/JD text
matches more heavily than legitimately-retrieved external context.

## Monitoring

Grafana dashboard (`monitoring/grafana_dashboards/jobfit_dashboard.json`)
includes 7 panels: analyses over time, fit-score distribution, feedback
ratio, gap-severity breakdown, average latency over time, most common
hard-filter-risk requirements, and average fit score. User feedback
(👍/👎) is collected per-analysis in the Streamlit app.

## Project structure

```
jobfit-agent/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── data/skills_taxonomy/       # ESCO, O*NET, ATS notes
├── ingestion/pipeline.py       # dlt pipeline: job postings -> DuckDB
├── load_knowledge_base.py      # chunks + embeds + indexes KB -> Elasticsearch
├── rag/retrieval.py            # vector / text / hybrid / advanced search
├── agent/jobfit_agent.py       # parse -> retrieve -> reason -> score -> rank
├── eval/                       # eval set generation + retrieval/LLM eval scripts
├── app/streamlit_app.py        # Streamlit interface
└── monitoring/                 # Postgres logging + Grafana dashboards
```

## Notes on design choices

- **Bounded scoring formula**: an earlier version used raw point subtraction,
  which floored out at a flat 0 for candidates with many gaps, losing the
  ability to distinguish "poor fit" from "zero fit." The current formula
  (weighted credit per requirement, naturally bounded 0-100) fixes this.
- **No PII stored in monitoring**: only aggregate/structural data (scores,
  gap counts, latency) is logged to Postgres — resume text itself is never
  persisted.
- **Domain-filtered knowledge base**: ESCO and O*NET cover every occupation;
  both are filtered to in-scope occupations before indexing, so retrieval
  isn't diluted by irrelevant content (e.g. unrelated trade/agriculture
  skill entries).
