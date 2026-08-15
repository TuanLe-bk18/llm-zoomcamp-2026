# Banking Assistant

An end-to-end RAG banking assistant.

A customer-facing chatbot for a fictional UK high-street bank. It:

1. Masks any PII/financial-sensitive data (account numbers, sort codes, card numbers, names, etc.) before doing anything else with the query
2. Retrieves relevant guidance from a synthetic banking knowledge base (text + vector + hybrid search)
3. Generates a grounded, customer-friendly answer tagged to the relevant banking division
4. Logs the masked query, PII detections, and feedback to PostgreSQL
5. Tracks everything in a Grafana dashboard

The entire knowledge base and every customer query in this repo is **synthetic and template-generated** — no real customer data, no scraped content, no copyright issues. Names, addresses, phone numbers, account numbers, etc. used for testing are all fabricated (phone numbers use Ofcom's officially reserved fictional ranges).

# 10 banking divisions

Current Accounts (CA) · Savings & ISAs (SAV) · Mortgages (MORT) · Credit Cards (CC) · Loans (LOAN) · Investments (INV) · Insurance (INS) · Fraud & Security (FRAUD) · Business Banking (BIZ) · Complaints & Regulations (COMP)

## Architecture

```
Customer question
      │
      ▼
┌─────────────────┐     ┌──────────────────────────┐
│  PII masking     │────▶│ regex layer (deterministic)│
│  (pii_masker.py) │     │ + LLM layer (names/addr)   │
└─────────────────┘     └──────────────────────────┘
      │  masked text + tokens/lemmas
      ▼
┌─────────────────┐     ┌───────────┐   ┌─────────┐
│  Retrieval       │────▶│ Minsearch │ + │  FAISS  │──▶ Reciprocal Rank Fusion
│  (rag.py)        │     │  (text)   │   │(vector) │
└─────────────────┘     └───────────┘   └─────────┘
      │  top-5 chunks + detected division
      ▼
┌─────────────────┐
│  LLM answer      │  (HuggingFace or OpenAI)
│  (llm.py)        │
└─────────────────┘
      │
      ▼
Streamlit chat UI ──▶ PostgreSQL (masked query, PII types, feedback) ──▶ Grafana
```

## Tech stack

- **Language:** Python 3.11+, managed with [uv](https://docs.astral.sh/uv/)
- **Search:** Minsearch (text) + FAISS (vector) + hybrid RRF fusion — no Elasticsearch
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2`
- **LLM:** two-provider support via `LLM_PROVIDER` env var — `huggingface` (default, free) or `openai`
- **PII masking:** two-layer — regex (primary, deterministic) + LLM (secondary, for names/addresses), followed by tokenize/lemmatize (NLTK) to produce a clean record safe for logging/analysis
- **Frontend:** Streamlit chat interface
- **Database:** PostgreSQL 16 (Docker container)
- **Monitoring:** Grafana 11 (Docker container)

Only PostgreSQL and Grafana run as containers. Everything else (the app, ingestion, evaluation) runs directly via `uv run`.

## Screenshots

**Chat interface** — answers are grounded in retrieved guidance and tagged to a division:

![Chat answer example](banking_assistant/docs/screenshots/chat-answer.jpg)

**PII masking in action** — the name and account number in the question below never reach the LLM or the database in raw form:

![PII masking example](banking_assistant/docs/screenshots/pii-masking.jpg)

**Grafana monitoring** — query volume, PII detection rate, response times, and feedback, all live:

![Grafana dashboard](banking_assistant/docs/screenshots/grafana-dashboard.jpg)

## Project structure

```
banking_assistant/
├── README.md
├── docker-compose.yml         # postgres + grafana only
├── pyproject.toml             # uv-managed dependencies
├── .env.example
├── .gitignore
│
├── app/
│   ├── app.py                 # Streamlit chat interface
│   ├── rag.py                 # Minsearch + FAISS retrieval + hybrid RRF
│   ├── llm.py                 # Two-provider LLM client (huggingface | openai)
│   ├── prompts.py              # Answer generation + PII detection + vulnerability prompts
│   ├── pii_masker.py           # Regex + LLM masking, then tokenize/lemmatize
│   ├── db.py                   # PostgreSQL read/write
│   └── config.py               # All settings from env vars
│
├── data_generation/
│   ├── generate_data.py        # Generates everything below
│   ├── knowledge_base.json     # ~200 synthetic banking guidance documents
│   ├── queries.json            # ~500 synthetic customer questions, some with injected fake PII 
│   └── pii_cases.json          # 100 PII masking test cases with ground-truth masks
│
├── ingestion/
│   ├── chunk_config.py         # Chunk size/overlap
│   └── ingest.py                # knowledge_base.json → chunk → embed → indices in data/
│
├── evaluation/
│   ├── ground_truth.json       # 50 Q&A pairs sampled from queries.json, for retrieval/RAG eval
│   ├── retrieval_eval.py       # Hit rate@5, MRR, division accuracy — text vs vector vs hybrid
│   ├── rag_eval.py             # LLM-as-judge scoring of the full pipeline
│   ├── pii_eval.py             # PII masking precision/recall vs pii_cases.json
│   └── results/                # Markdown reports written by the scripts above
│
├── monitoring/
│   ├── init_db.sql             # PostgreSQL schema
│   └── grafana/
│       ├── dashboard.json      # 9-panel dashboard (8 metrics, vulnerability split into stat+table)
│       └── provisioning/       # Auto-provisions the datasource + dashboard on container start
│
└── data/                       # gitignored — indices rebuilt by ingestion/ingest.py
```

## Getting started (GitHub Codespaces)

1. **Install uv** (one-time, inside the codespace terminal):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. **Clone the repository**
   ```bash
   git clone https://github.com/bkganti/llm_capstone_project.git
   ```

3. **Create env file for credentials**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   - For the free default provider, set `HF_TOKEN` to a [Hugging Face access token](https://huggingface.co/settings/tokens).
   - Or set `LLM_PROVIDER=openai` and `OPENAI_API_KEY=sk-...`.

4. **Start PostgreSQL and Grafana**:
   ```bash
   docker compose up -d
   ```

5. **Generate the synthetic data** :
   ```bash
   uv run python data_generation/generate_data.py
   ```

6. **Build the search indices**:
   ```bash
   uv run python ingestion/ingest.py
   ```

7. **Run the app**:
   ```bash
   uv run streamlit run app/st_app.py
   ```

## Running the evaluation suite

```bash
# Retrieval quality: hit_rate@5, MRR, division accuracy for text/vector/hybrid
uv run python evaluation/retrieval_eval.py

# PII masking precision/recall against 100 test cases
uv run python evaluation/pii_eval.py

# LLM-as-judge scoring of the full pipeline (needs a configured LLM provider)
uv run python evaluation/rag_eval.py
```

Results are written to `evaluation/results/*.md`.

## PII masking design

Two layers, run in sequence (`app/pii_masker.py`):

1. **Regex (deterministic)** — card numbers, sort codes, account numbers, NI numbers, UK postcodes, phone numbers, emails, DOB-shaped dates, CVV. Includes context-aware disambiguation: an 8-digit number preceded by "account"/"a/c" is masked as an account number, but one preceded by "£"/"paid"/"balance" is left alone (it's money, not an account number).
2. **LLM (for names and addresses)** — patterns regex can't reliably catch. Only runs when `PII_USE_LLM=true` and a provider is configured.

The masker then tokenizes and lemmatizes the *masked* text (NLTK) to produce a clean record — `masked_text`, `pii_found`, `detections` (type + method only, **never the original value**), `tokens`, `lemmas` — which is what gets logged to PostgreSQL or handed to a dataframe for analysis. The raw, unmasked text is never stored, logged, or displayed.

## Grafana dashboard

Panels, all backed by SQL against the `queries` / `pii_detections` tables:

1. Queries by division (bar chart)
2. Query volume over time (time series)
3. PII detection rate (gauge)
4. PII types breakdown (pie chart)
5. Detection method split — regex vs LLM (stacked bar)
6. Average response time (time series)
7. Feedback by division — thumbs up vs down (grouped bar)
8. Vulnerability flags — count (stat) + flagged queries (table)

## Environment variables

See `.env.example`. Key ones:

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER` | `huggingface` (default, free) or `openai` |
| `HF_TOKEN` / `HF_MODEL` | Hugging Face Inference API credentials |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | OpenAI credentials |
| `SEARCH_METHOD` | `text`, `vector`, or `hybrid` (default) |
| `PII_USE_LLM` | Enable the LLM PII layer (names/addresses) |
| `POSTGRES_*` | Match `docker-compose.yml` defaults unless changed |
| `GF_SECURITY_ADMIN_PASSWORD` | Grafana admin password |


# Retrieval Evaluation Results

| Method | Hit Rate@5 | MRR | Division Accuracy |
|---|---|---|---|
| text | 0.280 | 0.133 | 0.980 |
| vector | 0.260 | 0.114 | 0.980 |
| hybrid | 0.220 | 0.108 | 0.980 |

## Troubleshooting

If you keep getting **503** errors, just allow few minutes for inference usage throttling to reduce. This can be monitored on https://huggingface.co/settings/billing