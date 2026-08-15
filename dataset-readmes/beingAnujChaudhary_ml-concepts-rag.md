# [ML Concepts Atlas](https://beinganujchaudhary-ml-rag-concepts.streamlit.app/)

An end-to-end retrieval-augmented generation application that answers machine-learning questions from a curated Wikipedia knowledge base. It is designed for learners who want concise, source-backed explanations instead of searching through long articles. Every grounded answer also includes a Mermaid concept map to illustrate the relationships or process being explained.

## Architecture

The automated ingestion script fetches over 500 machine learning, AI, and data science articles through the Wikipedia API, cleans and chunks the text, embeds chunks with `all-MiniLM-L6-v2`, and pushes them to a Pinecone Serverless vector index. At query time, the LLM rewrites the question, Pinecone performs dense vector retrieval, results are re-ranked by a cross-encoder, and the LLM generates a context-only answer plus a Mermaid diagram. Streamlit provides the interface with a custom typography and color theme. Supabase (Cloud PostgreSQL) stores interactions, latency, and feedback; Grafana visualizes this monitoring data locally.

| Capability | Technology |
|---|---|
| Data source | Wikipedia API |
| LLM | Groq (Llama-3.1-8b) & OpenAI (GPT-4o-mini fallback) |
| Embeddings | Sentence Transformers `all-MiniLM-L6-v2` |
| Knowledge base | Pinecone Serverless Vector DB |
| Interface | Streamlit with custom brand theme and Mermaid diagrams |
| Monitoring | Supabase (PostgreSQL) and Grafana 11 |
| Runtime | Streamlit Community Cloud (App) + Docker Compose (Grafana) |

## Prerequisites

Create free accounts and get API keys from:
- **Groq:** https://console.groq.com/keys
- **Pinecone:** https://pinecone.io (Create a serverless index named `ml-concepts`, dimension 384)
- **Supabase:** https://supabase.com (Get the PostgreSQL connection URI)

Install Docker Desktop with Docker Compose. Never commit or paste your keys into source code.

## Run locally

Clone the repository and enter its directory. Then create the local environment file:

```powershell
Copy-Item .env.example .env
notepad .env
```

Populate the `.env` file with your `GROQ_API_KEY`, `PINECONE_API_KEY`, and `DATABASE_URL` (Supabase). Open the terminal and fetch Wikipedia content, create embeddings, and populate Pinecone:

```bash
pip install -r requirements.txt
python data_ingestion/ingest.py
```

Build and start the local environment (App + Grafana):

```bash
docker compose up -d --build
docker compose ps
```

Open the services:

- Streamlit: http://localhost:8501
- Grafana: http://localhost:3000

Try questions such as “How does backpropagation work?”, “Compare supervised and unsupervised learning,” or “What is a random forest?” Expand **Show Sources** to inspect retrieved evidence and use the feedback buttons to populate monitoring data.

To inspect failures:

```bash
docker compose logs --tail=100 app
docker compose logs --tail=100 grafana
```

To stop the project, use `docker compose down`. Add `-v` only when you intentionally want to delete indexed and monitoring data.

## Evaluation criteria

**Problem description (2):** The application provides focused, source-backed explanations and visual concept maps for people learning machine learning.

**Retrieval flow (2):** Questions are rewritten, embedded, retrieved with Pinecone vector search, re-ranked by a cross-encoder, and answered by the LLM from the top contexts.

**Retrieval evaluation (2):** `evaluation/evaluate_retrieval.ipynb` compares text, vector, and hybrid retrieval. Hybrid search is the production choice.

**LLM evaluation (2):** `evaluation/evaluate_llm.ipynb` compares multiple prompts with an LLM-as-a-judge workflow using Groq. Run it with a valid API key and record the results before submission.

**Interface (2):** Streamlit offers chat, expandable citations, feedback controls, and generated Mermaid concept diagrams.

**Ingestion pipeline (2):** `data_ingestion/ingest.py` is fully automated as a **Prefect** workflow (`@flow` and `@task` decorators). It automates fetching 500+ Wikipedia articles, cleaning, chunking, embedding, index creation, and indexing, which guarantees reliable execution and retry logic.

**Monitoring (2):** Feedback and latency are stored in Supabase PostgreSQL. The provisioned Grafana dashboard contains five panels: total queries, average response time, feedback distribution, queries over time, and recent queries.

**Containerization (2):** Streamlit and Grafana run with Docker Compose. Pinecone, Supabase, Groq, and OpenAI are external managed cloud APIs.

**Reproducibility (2):** Dependencies and service versions are specified, the dataset is fetched from a public API, configuration is documented, and no secret is committed.

**Best practices:** Dual LLM provider fallback logic, Pinecone vector search, query rewriting, and document re-ranking with a cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) are implemented.

## Evaluation and submission checklist

Before submission, execute both evaluation notebooks, save visible results, capture screenshots of the UI and five-panel Grafana dashboard, test the setup from a fresh clone, and verify that `.env` is not tracked. Submit the public GitHub repository URL and the exact final commit hash. Complete three peer reviews to receive the associated points.
