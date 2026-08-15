# AWS Architecture Advisor

An LLM-powered RAG assistant that answers questions about AWS architecture
best practices — grounded in the AWS Well-Architected Framework's six
pillars (Operational Excellence, Security, Reliability, Performance
Efficiency, Cost Optimization, Sustainability).

## Problem description

Engineers designing AWS systems constantly re-derive the same architectural
guidance ("how do I make this resilient to an AZ outage", "how do I cut my
EC2 bill", "what does a serverless API pattern look like") from scattered
whitepapers and blog posts. This app lets you ask that question directly and
get a grounded answer, instead of hunting through docs or
risking an un-grounded LLM hallucinating AWS service behavior.

## Architecture

![alt text](aws-rag.png)

- **Knowledge base**: `data/aws_docs.json`, built by `data/build_dataset.py`
- **Ingestion pipeline**: `ingestion/ingest.py` — builds indexes
- **Retrieval**: `rag/retrieval.py` — retrieval methods; evaluated in `evaluation/evaluate_retrieval.py`)
- **RAG pipeline**: `rag/rag.py` + `rag/prompts.py` — builds a grounded
  prompt from retrieved docs and calls the LLM
- **Interface**: `app/app.py` — Flask API + simple web chat UI
- **Monitoring**: `monitoring/db.py` — logs every conversation + user
  feedback (👍/👎) to Postgres; Grafana dashboards read from that same DB
- **Notebook**: `notebooks/base.ipynb` — interactive
  walkthrough of the whole pipeline
- **Evaluation**: `evaluation/` — retrieval metrics (Hit Rate, MRR) comparing
  lexical-only vs semantic-only vs hybrid, and LLM-as-a-judge evaluation of
  final answer relevance

## Steps to reproduce

### 1. Clone and set up environment (using uv)

[uv](https://docs.astral.sh/uv/) is used.  `uv sync`
reads `pyproject.toml`, creates the virtual environment, and installs every
dependency (plus writes a `uv.lock` for reproducible installs) in one step.

```bash
# install uv once, if you don't have it:
curl -LsSf https://astral.sh/uv/install.sh | sh

# clone this repo

uv sync                          
source .venv/bin/activate        # Windows: .venv\Scripts\activate

cp .env.example .env
# edit .env and set GROQ_API_KEY (free key: https://console.groq.com/keys)
```

### 2. Build the knowledge base and indices

**LLM-generated (fast, synthetic):**
```bash
export $(cat .env | xargs) 
python data/build_dataset.py     # calls Groq to generate data/aws_docs.json
```
Hardcodes only the list of (pillar, service, question) topics to cover, then
calls a Groq model once per topic to write the explanatory paragraph.

### 3. Start Postgres + Grafana (for monitoring)

```bash
docker compose up -d postgres grafana
```

### 4. Run the app

```bash
export $(cat .env | xargs)   
python app/app.py
```

Open http://localhost:5001 and ask a question, e.g.:
- "How do I make my database resilient to an AZ failure?"
- "What's the cheapest way to host a static website?"
- "How should microservices talk to each other on AWS?"

Every answer shows its source documents and has 👍/👎 feedback buttons that
get logged for monitoring.

### You can build app with Docker Compose

```bash
docker compose up --build
```

This starts the app (port 5001), Postgres (port 5433), and Grafana
(port 3000, login `admin`/`admin`). The app's Docker image builds the
retrieval indices from the already-generated `data/aws_docs.json` at
image-build time.

### 5. Run evaluation

```bash
export $(cat .env | xargs)
# 1. Generate a labeled question set
python evaluation/generate_ground_truth.py

# 2. Evaluate retrieval quality: lexical vs semantic vs hybrid vs RRF
python evaluation/evaluate_retrieval.py

# 3. Search for better per-field boost weights, then re-run step 2
#    to see the improvement -- writes evaluation/best_boost.json
python evaluation/optimize_boosting.py --trials 5

# 4. Evaluate end-to-end answer quality (LLM-as-a-judge)
python evaluation/evaluate_rag.py --sample 30
```

`evaluate_retrieval.py` prints Hit Rate and MRR for every retrieval method
implemented in `rag/retrieval.py`:

| Method | What it is |
|---|---|
| `lexical only` | TF-IDF, uniform field weights |
| `semantic only` | sentence-transformers embeddings |
| `hybrid` | `alpha * semantic + (1-alpha) * lexical` (linear blend of raw scores) |
| `RRF` | Reciprocal Rank Fusion — combines the two *rankings*, not raw scores: `score = 1/(k+rank_lexical) + 1/(k+rank_semantic)`, `k=60` |

Run it once with uniform field weights to see the baseline, then again after `optimize_boosting.py` has written `evaluation/best_boost.json` 
— it's picked up automatically and adds two more rows (`hybrid` and `RRF`, both with optimized boosting) so you can see the effect of tuned field weights independent of which combination strategy you use.

`evaluate_rag.py` samples ground truth questions, runs the full pipeline,
and asks an LLM judge to classify each answer as RELEVANT / PARTLY_RELEVANT /
NON_RELEVANT, writing results to `evaluation/rag_eval_results.json`.

### 6. Set up the Grafana dashboard

1. Go to http://localhost:3000, log in (`admin`/`admin`)
2. The Postgres datasource is auto-provisioned
3. Import dashboard from `grafana\dashboard.json` 



