# ⚔️ Elden Ring Lore Guide (RAG System)

An advanced Retrieval-Augmented Generation (RAG) system built to answer questions about Elden Ring weapons, bosses, and NPCs. This application uses **PostgreSQL (pgvector)**, **Hybrid Search**, **FlashRank Document Re-ranking**, **Query Rewriting**, and **Llama 3.2** to deliver highly accurate, context-grounded answers alongside real-time weapon and boss images.

---

## 📖 Problem Description

In massive RPGs like Elden Ring, players frequently consult wikis to look up weapon scaling, boss locations, and lore requirements. However, generic LLMs often hallucinate stats (such as inventing non-existent attributes) or miss game-specific context.

This project solves this problem by building a local, private RAG pipeline that:

1. **Prevents Hallucinations:** Constrains the LLM to verified database records.
2. **Improves Search Precision:** Translates fragmented user queries (e.g., "beastclaw scaling") into semantically rich search parameters.
3. **Validates Quality:** Includes automated evaluations for retrieval and generation.
4. **Ensures Enterprise Security:** Isolates system telemetry inside an admin-only Grafana dashboard rather than exposing internal metrics to the public app client.

## 📂 Data Source

The data utilized in this project is stored locally in the `data/` directory. It is sourced and structured from:

* **Primary Source:** [Ultimate Elden Ring with Shadow of The Erdtree DLC (Kaggle)](https://www.kaggle.com/datasets/pedroaltobelli/ultimate-elden-ring-with-shadow-of-the-erdtree-dlc)

---

## 🛠️ Architecture & Tech Stack

* **Frontend UI:** Streamlit
* **Database:** PostgreSQL + `pgvector` (Vector similarity + Full-Text search)
* **Orchestration & Ingestion:** Kestra (Automated ETL)
* **Query Rewriting & Generation:** Ollama (`llama3.2:1b`)
* **Document Re-ranking:** FlashRank (`ms-marco-TinyBERT-L-2-v2`)
* **Monitoring & Telemetry:** Grafana (Direct PostgreSQL telemetry)

---

## 🚀 How to Run the Project

### 1. Prerequisites

Ensure you have the following installed:

* [Docker & Docker Compose](https://docs.docker.com/get-docker/)
* [Ollama](https://ollama.com/) (running locally with `llama3.2:1b` pulled: `ollama pull llama3.2:1b`)

### 2. Startup the Containers

Spin up the entire stack (PostgreSQL, Grafana, Kestra, and the Streamlit UI) using a single command:

```bash
docker compose up --build -d
```

### 3. Ingest the Dataset

1. Open Kestra at `http://localhost:8080`.
2. Import and run the ingestion flow located in your orchestration configurations. This will automatically clean the Elden Ring CSV dataset, generate vector embeddings, and load them into PostgreSQL.

### 4. Open the Application

Access the user interface at: 👉 `http://localhost:8501`

---

## 🔍 Evaluation Metrics

### 1. Retrieval Evaluation (`evaluation/evaluate_retrieval.py`)

We compared three retrieval approaches against our golden-standard `ground_truth.json` dataset using the **Hit Rate@1 (Recall@1)** metric:

| Retrieval Approach | Hit Rate @ 1 |
| :--- | :---: |
| Pure Full-Text Keyword Search (FTS) | 33.3% |
| Pure Dense Vector Search | 100.0% |
| **Hybrid Search + FlashRank Reranker (Ours)** | **100.0%** |

### 2. LLM-as-a-Judge Evaluation (`evaluation/evaluate_llm.py`)

Using an LLM judge, we evaluated the generation output quality on a scale of 1 to 5 to measure relevance and identify hallucinations:

| Generation Approach | Avg Judge Score |
| :--- | :---: |
| Approach A (Naive Prompting) | 3.2 / 5.0 |
| **Approach B (Optimized RAG Prompt Template - Ours)** | **4.8 / 5.0** |

To run the evaluations locally:

```bash
python evaluation/evaluate_retrieval.py
python evaluation/evaluate_llm.py
```

---

## 📊 Monitoring (Grafana Integration)

Following production best practices, system monitoring is entirely isolated from the client-facing UI.
Administrators can monitor system health by logging into **Grafana** at `http://localhost:3000` (Credentials: `admin`/`admin`).

Our dashboard monitors:

* **System Latency Trend (ms):** Monitors response generation times.
* **User Feedback Ratio:** Tracks thumbs-up/thumbs-down feedback logged to `conversation_logs`.
* **Database Query Volumes:** Visualizes traffic spikes and popular item categories.
