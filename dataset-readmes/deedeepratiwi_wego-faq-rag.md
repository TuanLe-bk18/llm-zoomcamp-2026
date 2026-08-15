# ✈️ Wego FAQ Customer Support RAG System
An end-to-end, production-ready Retrieval-Augmented Generation (RAG) assistant designed to help [**Wego**](https://www.wego.co.id/) customers quickly navigate flight changes, hotel bookings, cancellation policies, and refund rules.

The system combines **Automated Web Scraping with Crawl4AI**, **Prefect Workflow Orchestration**, **Hybrid Search (BM25 + Vector)**, **Cross-Encoder Re-ranking**, **LLM Query Rewriting**, **real-time Prometheus & Grafana Observability**, and **Langfuse Tracing** — all fully containerized using `uv` and `Docker`.

![Wego FAQ Assistant Demo](images/wego_faq_rag.gif)

---

## 🎯 Evaluation Criteria Mapping

This project addresses all criteria from the evaluation rubric from [LLM Zoomcamp course](https://github.com/DataTalksClub/llm-zoomcamp/blob/main/project.md):

| Evaluation Criteria | Score | Evidence / Implementation in Code |
| :--- | :---: | :--- |
| **Problem Description** | **2 / 2** | Detailed below in [Problem Statement](#-problem-statement). |
| **Retrieval Flow** | **2 / 2** | Knowledge base (PostgreSQL + pgvector) and LLM (`gpt-5.4-mini`) used in flow. |
| **Retrieval Evaluation** | **2 / 2** | Evaluated 5 retrieval pipelines in `src/evaluate.py`. |
| **LLM Evaluation** | **2 / 2** | Evaluated Faithfulness & Answer Relevance in `src/evaluate_rag_triad.py`. |
| **Interface** | **2 / 2** | Streamlit Web Application with built-in feedback system (`app.py`). |
| **Ingestion Pipeline** | **2 / 2** | **Automated Prefect pipeline** (`src/ingest_flow.py`) running inside Docker Compose. |
| **Monitoring** | **2 / 2** | **User Feedback Collection** (👍/👎 buttons) + **Grafana Dashboard** with **5 live charts**. |
| **Containerization** | **2 / 2** | Everything orchestrated via `docker-compose.yml` (`postgres`, `ingestion`, `app`, `prometheus`, `grafana`). |
| **Reproducibility** | **2 / 2** | Single-command deployment (`docker compose up --build -d`) with strict dependency lockfiles via `uv`. |
| **Best Practice: Hybrid Search** | **1 / 1** | Evaluated and selected PostgreSQL BM25 Full-Text + pgvector Cosine similarity via RRF. |
| **Best Practice: Re-ranking** | **1 / 1** | Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) re-ranks top candidate documents. |
| **Best Practice: Query Rewriting**| **1 / 1** | Implemented and evaluated `PostgresQueryRewrittenRAG` against base models. |

---

## 📖 Problem Statement
Travelers using customer support platforms often face long wait times to get answers to routine questions about flight cancellations, baggage allowances, date changes, or refund processing. Search interfaces that rely purely on exact keyword matches fail when users ask vague questions (e.g., "date chg flight").

The Solution:
The **Wego FAQ RAG Assistant** provides instant, context-aware answers to travel queries. By leveraging:
1. **Automated Knowledge Ingestion** from Wego's support portal across 20+ travel categories,
2. **Orchestrated Ingestion Pipeline** via Prefect to seed relational tables and `pgvector` embeddings,
3. **Hybrid Search & Re-ranking** to retrieve the exact FAQ entries,
4. **OpenAI gpt-5.4-mini** to compose friendly, natural responses grounded only in verified knowledge base context.

---

## 🏗️ Architecture & Pipeline Flow

```text
 ┌────────────────┐
 │ Wego Support   │
 │ Support Portal │
 └───────┬────────┘
         │ 1. Asynchronous Crawl (Crawl4AI)
         ▼
 ┌────────────────┐    2. Extract & Parse    ┌───────────────────────┐
 │ src/scrape.py  │ ───────────────────────> │ data/scraped_faqs.json│
 └────────────────┘                          └──────────┬────────────┘
                                                        │
                                                        │ 3. Automated Ingestion
                                                        ▼
                                             ┌──────────────────────┐
                                             │  Prefect Flow Engine │
                                             │ (src/ingest_flow.py) │
                                             └──────────┬───────────┘
                                                        │
                                                        │ 4. Seed Tables & Vector Embeddings
                                                        ▼
                                             ┌──────────────────────┐
                                             │ Postgres + pgvector  │
                                             └──────────┬───────────┘
                                                        │
 ┌────────────────┐     5. User Query                   │ 6. Hybrid Search & Re-rank
 │ Streamlit UI   │ ────────────────────────────────────┴──────────┐
 └───────┬────────┘                                                │
         │                                                         ▼
         │ 7. Response & Feedback                        ┌───────────────────┐
         └────────────────────────────────────────────── │ LLM Engine        │
                                                         │ (gpt-5.4-mini)    │
                                                         └───────────────────┘
```

---

## 🛠️ Datasests and Ingestion Pipeline
The dataset was taken from Wego's public support portal (https://support.wego.com/) and scraped using **Crawl4AI**. The scraped data is stored in `data/scraped_faqs.json` and ingested into PostgreSQL with `pgvector` for semantic search.

The dataset pipeline consists of three modular Python scripts in `src/`:
1. **Web Scraping** (`src/scrape.py`):
- Uses `Crawl4AI` (`AsyncWebCrawler`) to asynchronously crawl Wego's support portal across 21 distinct categories (e.g., travel-disruption, insurance, hotel-policies, flights).
- Parses Markdown outputs into structured FAQ objects (`question`, `answer`, `category`, `source_url`) and cleans out redundant metadata.
- Saves deduplicated FAQ JSON entries to `data/scraped_faqs.json`.

2. **Relational Ingestion** (`src/ingest_postgres.py`):
- Connects to PostgreSQL using `psycopg`.
- Creates the `wego_faqs` database table.
- Upserts the parsed FAQ documents using `ON CONFLICT (doc_id) DO UPDATE` to prevent duplicates.

3. **Vector Ingestion** (`src/ingest_vectors.py`):
- Enables `pgvector` inside PostgreSQL (`CREATE EXTENSION IF NOT EXISTS vector;`).
- Uses `sentence-transformers/all-MiniLM-L6-v2` to compute 384-dimensional embeddings for each FAQ.
- Updates `wego_faqs` with vector representations for fast cosine similarity retrieval.

### **Automated Ingestion Pipeline (`Prefect`)**
Data ingestion is orchestrated using **Prefect** (`src/ingest_flow.py`). When Docker starts, the ingestion service executes the flow automatically before launching the web application:
- Task 1: **PostgreSQL Schema & Text Setup** (`src/ingest_postgres.py`):
Creates the wego_faqs database table and upserts raw FAQ JSON records.
- Task 2: **Vector Embedding Generation** (`src/ingest_vectors.py`):
Enables `pgvector`, computes 384-dimensional embeddings using `sentence-transformers/all-MiniLM-L6-v2`, and stores vectors in PostgreSQL.

Manual Local Ingestion Execution (via `uv`):
```bash
# Run full Prefect flow locally
uv run python src/ingest_flow.py
```

---

## 📊 Evaluation & Experimentation
Evaluation scripts are available under `src/evaluate.py` (Retrieval Evaluation) and `src/evaluate_rag_triad.py` (LLM Evaluation).

### **Retrieval Evaluation** (`src/evaluate.py`)
Evaluated 5 distinct retrieval pipelines against a dataset of annotated ground-truth travel Q&As (`data/ground_truth_data.json`) using `Hit Rate @ 5` and `MRR @ 5 (Mean Reciprocal Rank)`:

| Retrieval Method | Hit Rate @ 5 | MRR @ 5 | Avg Faithfulness | Avg Relevance | Latency / Query | Selected for Production? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Text Search (BM25) | 0.2339 | 0.1908 | — | — | ~0.03s | ❌ |
| Vector Search (pgvector) | 0.9620 | 0.8720 | — | — | ~0.04s | ❌ |
| Hybrid Search (RRF) | 0.9678 | 0.7892 | — | — | ~0.05s | ❌ |
| **Hybrid + Cross-Encoder Re-ranker** | **0.9708** | **0.8736** | **0.9963** | **0.9633** | **~0.28s** | ✅ Selected |
| Rewriter + Hybrid + Cross-Encoder | 0.9708 | 0.8589 | — | — | ~1.78s | ❌ |


*Key Finding*: While Query Rewriting achieved the same Hit Rate (0.9708), it **lowered MRR @ 5 from 0.8736 down to 0.8589** due to over-expansion of specific travel terminology. Therefore, **Hybrid + Cross-Encoder Re-ranker** (`PostgresRerankedHybridRAG`) was selected as the final production model.

### **LLM Evaluation** (`src/evaluate_rag_triad.py`)
Evaluated the generation quality of the end-to-end **Hybrid + Cross-Encoder Re-ranker** RAG system against the ground-truth dataset using **LLM-as-a-Judge** across a 30-query sample set:

| Generation Metric | Average Score (0.0 to 1.0) | Target |
|  :--- | :---: | :---: |
| Avg Faithfulness | 0.9963 | >0.95 |
| Avg Answer Relevance | 0.9633 | >0.90 |

*Conclusion*: Strict system prompts prevent hallucinations, ensuring 99.6% of generated claims are directly grounded in the retrieved Wego support documents.

---

## 🚀 Quickstart & Reproducibility (Zero Setup)
Everything runs inside Docker. No local Python or Database configuration is needed.

### **Prerequisites**
- Docker Desktop installed and running
- An `OPENAI_API_KEY` set in the `.env` file

### **Step 1. Clone the Repository & Configure Environment**
```bash
git clone https://github.com/deedeepratiwi/wego-faq-rag.git
cd wego-faq-rag

# Create.env file
cat > .env <<EOL
OPENAI_API_KEY=sk-proj-your-key-here    
```

### **Step 2. Launch the Application Stack**
```bash
docker compose up --build -d
```
What Docker Does Automatically:
- Boots `postgres` (with `pgvector`) and waits for health check to pass.
- Boots `ingestion` container and runs `uv run python src/ingest_flow.py` via `Prefect`.
- Once ingestion completes, launches `app` (Streamlit interface), `prometheus`, and `grafana`.

### **Step 3. Access the Endpoints**

| Component |URL | Description | Credentials |
| :--- | :---: | :---: | :---: |
| 💬 Streamlit Web App | http://localhost:8501 | Main User Chat Interface | None |
| 📊 Grafana Dashboard | http://localhost:3000 | Operational Metrics Console | Pre-configured (`admin/admin`) |
| 📈 Prometheus Metrics | http://localhost:8000/metrics | Raw App Prometheus Exposition | None |

### **Step 4. Stopping the Application**
```bash
docker compose down
```

---

## 🖥️ Application & Observability Preview
### **User Interface (Streamlit)** (`app.py`)
- **Ask Travel Questions**: Test queries like *"How do I change my flight date?"* or *"What is Wego refund policy?"*
- **Provide Feedback**: Every assistant response includes 👍 / 👎 buttons along with a *"Was this helpful?"* prompt that triggers real-time feedback ingestion into Prometheus and Langfuse.

![UI_1](images/web_app_1.png)

![UI_1](images/web_app_2.png)

### **Live Monitoring Dashboard (Grafana)**
Grafana auto-loads via **YAML Provisioning as Code** upon startup. It displays **5 live charts**:
- **User Satisfaction Rate (%) (Stat Gauge):** Calculates CSAT ratio: $\frac{\text{Thumbs Up}}{\text{Total Feedback}} \times 100$.
- **Total Query Volume & Feedback Summary (Pie Chart):** Real-time breakdown of user sentiment.
- **Total Token Cost Over Time ($) (Stat Card):** Live tracking of LLM API expenses.
- **End-to-End Latency Breakdown (Time Series):** Live P50 (Median) vs P95 response time percentiles.
- **Total Token Usage Split (Bar Chart):** Input vs. Output token consumption.

![Dashboard](images/grafana_dashboards.png)

---

## 📂 Project Repository Structure

```text
wego-faq-rag/
├── data/                     
│   ├── scraped_faqs.json                 # Cleaned FAQ dataset scraped from Wego
│   └── ground_truth_data.json            # Ground truth data for evaluation
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/                  # Auto-wires Prometheus target (datasources.yml)
│   │   └── dashboards/                   # Auto-wires Dashboard loader (dashboards.yml)
│   └── dashboards/
│        └── wego_rag_dashboard.json      # Pre-built 5-panel Grafana dashboard
├── src/
│   ├── scrape.py                         # Crawl4AI async scraper across 21 support categories
│   ├── ingest_postgres.py                # PostgreSQL table schema & text data ingestion
│   ├── ingest_vectors.py                  # SentenceTransformers embedding generation & pgvector sync
│   ├── ingest_flow.py                    # Prefect orchestration pipeline
│   ├── evaluate.py                       # Evaluation script for retrieval and generation
│   ├── evaluate_rag_triad.py             # Faithfulness and Answer Relevance LLM-as-a-Judge script
│   ├── generate_ground_truth_data.py     # Script to generate ground truth data for evaluation
│   └── rag.py                            # Core RAG engine, Prometheus metrics, and Postgres logic   
├── app.py                                # Streamlit User Interface
├── docker-compose.yml                    # Container orchestration (App, Postgres, Prometheus, Grafana)
├── Dockerfile                            # Dockerfile for building the RAG system image   
└── README.md                             # Project documentation and overview
```

