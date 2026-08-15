# FPL Expert Agent — Agentic RAG Application

An end-to-end LLM application acting as an **FPL (Fantasy Premier League) Expert Agent**. This project was built for the [DataTalks.Club LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp).

## 1. Problem Description

Fantasy Premier League (FPL) managers face information overload. Making good decisions (transfers, captaincy) requires cross-referencing **structured numerical stats** (points, price, form) with **unstructured qualitative context** (injuries, press conferences, tactical shifts). 

This project solves this by using an **Agentic RAG approach**:
1. It queries the live, official FPL API for structured data.
2. It queries a vectorized Elasticsearch knowledge base (built via an automated ingestion pipeline) for unstructured football news.
3. An OpenAI Agent uses **Function Calling (Tools)** to autonomously decide which source to query based on the user's question, combining both into a final expert response.

## 2. Evaluation Criteria Fulfillment

This project aims for maximum points (21/21) across all evaluation criteria:

*   **Problem Description (2/2):** Clearly defined above and solved via agentic tools.
*   **Retrieval Flow (2/2):** The agent uses an Elasticsearch KB for news and live APIs for stats, orchestrated via an LLM.
*   **Retrieval Evaluation (2/2):** Multiple approaches (Text/BM25, Vector/kNN, and Hybrid/RRF) are evaluated in `evaluation/retrieval_eval.py`.
*   **LLM Evaluation (2/2):** Two models (gpt-4o-mini vs gpt-3.5-turbo) are evaluated using an LLM-as-a-judge with structured outputs in `evaluation/llm_eval.py`.
*   **Interface (2/2):** A fully featured UI built with Streamlit (`app.py`).
*   **Ingestion Pipeline (2/2):** An automated pipeline using **Prefect 3** (`ingestion/pipeline.py`) that chunks and embeds news into Elasticsearch.
*   **Monitoring (2/2):** Captures user feedback (+1/-1), auto-evaluates relevance with an LLM Judge, and visualizes it all. There is a **Grafana Dashboard** AND a **Streamlit Dashboard** (`dashboard.py`) with 5+ charts (Cost, Response Time, Token Usage, Judge Relevance, User Feedback).
*   **Containerization (2/2):** Everything (Elasticsearch, PostgreSQL, Grafana, Streamlit) runs via a single `docker-compose.yml`.
*   **Reproducibility (2/2):** All dependencies pinned, synthetic news generation provided to bypass API limits, and clear instructions below.
*   **Best Practices (3/3 Bonus):**
    *   [x] **Hybrid Search:** Implemented in `es_client.py`.
    *   [x] **Document Re-ranking:** Handled natively via RRF (Reciprocal Rank Fusion) during Hybrid Search.
    *   [x] **User Query Rewriting:** Implemented in `agent.py`.

## 3. Architecture

*   **UI:** Streamlit (`app.py`)
*   **Monitoring DB:** PostgreSQL (`db_*.py` files)
*   **Vector DB:** Elasticsearch 8
*   **Orchestrator:** Prefect 3 (`ingestion/pipeline.py`)
*   **LLM:** OpenAI (`gpt-4o-mini`)

## 4. Setup and Execution

### Prerequisites
*   Docker & Docker Compose
*   An OpenAI API Key

### Step-by-Step Instructions

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-link>
    ```

2.  **Environment Variables:**
    Copy the example file and add your OpenAI API Key.
    ```bash
    cp .env.example .env
    # Edit .env and paste your OPENAI_API_KEY
    ```

3.  **Start the Infrastructure:**
    Spin up all containers (Streamlit, Grafana, Elasticsearch, Postgres).
    ```bash
    docker-compose up -d
    ```

4.  **Run the Ingestion Pipeline:**
    We need to populate the Elasticsearch knowledge base. We generate synthetic news articles to ensure reproducibility without relying on unstable scrapers.
    Run this command *inside* the streamlit container:
    ```bash
    docker-compose exec streamlit_app python -m ingestion.pipeline
    ```
    *(Note: This creates `data/news_articles.json`, chunks them, generates embeddings, and saves them to Elasticsearch).*

5.  **Initialize the Monitoring Database:**
    You can optionally fill the dashboard with fake historical data to test the charts:
    ```bash
    docker-compose exec streamlit_app python generate_data.py
    ```

### 5. Access the Applications

*   **FPL Agent Chat (Streamlit):** [http://localhost:8501](http://localhost:8501)
*   **Monitoring Dashboard (Streamlit):** [http://localhost:8502](http://localhost:8502)
*   **Grafana Dashboard:** [http://localhost:3000](http://localhost:3000) (User: `admin`, Pass: `admin`) -> Go to Dashboards -> "FPL Agent Metrics"

### 6. Run Evaluations (Optional)

If you want to run the mathematical evaluations (Retrieval Hit Rate/MRR and LLM Judge comparisons):

```bash
# 1. Generate Ground Truth (Questions based on the news)
docker-compose exec streamlit_app python -m evaluation.generate_ground_truth

# 2. Run Retrieval Evaluation (Compares BM25, kNN, and Hybrid)
docker-compose exec streamlit_app python -m evaluation.retrieval_eval

# 3. Run LLM Evaluation (Compares models via Judge)
docker-compose exec streamlit_app python -m evaluation.llm_eval
```

## Example Questions to ask the Agent:
*   "Who are the top 3 scoring midfielders?" *(Will use the FPL API tool)*
*   "Is Haaland injured?" *(Will use the News Search tool)*
*   "Compare Saka and Palmer." *(Will use the FPL API tool)*
