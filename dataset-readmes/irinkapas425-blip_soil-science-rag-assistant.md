# Soil Science RAG Assistant

## Problem Description

Farmers, agronomy students, and gardeners often need quick, reliable answers about soil science topics - soil pH, fertility, nutrient cycles, soil classification, and related agrochemistry concepts. Searching through long textbooks or scattered web pages is slow and often gives inconsistent or overly technical answers.

This project builds a **Retrieval-Augmented Generation (RAG) assistant** that answers questions about soil science and soil chemistry, using a curated knowledge base of Wikipedia articles as its source of truth. The assistant retrieves the most relevant passages for a question and uses an LLM to generate a clear, grounded answer - reducing the risk of made-up information and giving users a simple chat-like interface instead of manual searching.

## Dataset

The knowledge base consists of **30+ Wikipedia articles** on soil science topics, including: soil pH, soil fertility, soil organic matter, humus, soil horizons, soil texture and structure, soil salinity, cation exchange capacity, the nitrogen and phosphorus cycles, fertilizers, compost, soil microbiology, mycorrhiza, soil classification (chernozem, podzol, laterite), clay minerals, crop rotation, and precision agriculture.

Articles are fetched automatically via the Wikipedia API (see `run_ingestion.py`), split into overlapping chunks (~1500 characters), and embedded using OpenAI's `text-embedding-3-small` model for semantic search.

## Architecture

The pipeline follows a standard RAG flow:

1. **Ingestion** (`run_ingestion.py`): fetch Wikipedia articles, clean and deduplicate them, split into chunks, and compute embeddings.
2. **Retrieval** (`vector_index.py`): given a question, compute its embedding and find the most similar chunks using cosine similarity.
3. **Generation** (`rag_helper.py`, `rag_metrics.py`): build a prompt from the retrieved chunks and send it to an LLM (`gpt-5.4-mini`) to generate an answer.
4. **Interface** (`app.py`): a Streamlit app where users ask questions and give thumbs up/down feedback.
5. **Monitoring** (`metrics_db.py`, `dashboard.py`): every call is logged to a SQLite database (question, answer, tokens, cost, response time), and a separate Streamlit dashboard visualizes this data with 5+ charts.

## Technologies

- **LLM**: OpenAI `gpt-5.4-mini`
- **Embeddings**: OpenAI `text-embedding-3-small`
- **Knowledge base**: in-memory vector search (numpy cosine similarity) and `minsearch` (text search) for comparison
- **Interface**: Streamlit
- **Monitoring**: SQLite + Streamlit dashboard
- **Ingestion**: Python script (Wikipedia API)
- **Containerization**: Docker + Docker Compose

## Evaluation

### Retrieval evaluation

A ground truth set of 60 questions was generated automatically (one question per randomly sampled chunk, using an LLM) and used to compare two retrieval approaches:

| Method | Hit Rate | MRR |
|---|---|---|
| Text search (minsearch) | 0.867 | 0.589 |
| **Vector search (embeddings)** | **0.983** | **0.755** |

Vector search performed significantly better and was chosen for the final RAG pipeline (see `evaluate_search.py` and `evaluate_vector_search.py`).

### LLM answer evaluation

Two prompt variants were compared using an LLM-as-a-judge approach (see `evaluate_prompts.py` and `prompt_variants.py`):

- **V1**: a simple, concise instruction prompt
- **V2**: a more detailed prompt asking for structured, practical answers

Both prompts scored a perfect relevance score (1.000) on a 20-question sample judged by GPT. Prompt V2 was chosen for the final assistant, as it produces more informative, well-structured answers for users while maintaining the same accuracy.

## How to Run

### Option 1: Docker (recommended)

1. Clone this repository
2. Create a `.env` file in the project root with your OpenAI API key:

   OPENAI_API_KEY=sk-your-key-here

3. Build and start both services:

   docker compose up --build

4. Open the app at http://localhost:8501
5. Open the monitoring dashboard at http://localhost:8502

### Option 2: Local setup with uv

1. Clone this repository
2. Install uv if you don't have it: https://docs.astral.sh/uv/
3. Install dependencies:

   uv sync

4. Create a `.env` file with your OpenAI API key (see above)
5. Run the full ingestion pipeline (fetches data, builds embeddings):

   uv run python run_ingestion.py

6. Start the app:

   uv run streamlit run app.py

7. In a separate terminal, start the dashboard:

   uv run streamlit run dashboard.py --server.port 8502

## Project Structure

- `run_ingestion.py` - full automated ingestion pipeline
- `ingest.py`, `clean_articles_lib.py`, `chunking.py`, `compute_embeddings_lib.py` - ingestion steps
- `vector_index.py` - vector search implementation
- `rag_helper.py`, `rag_metrics.py` - RAG pipeline with metrics instrumentation
- `prompt_variants.py` - alternative prompt instructions
- `evaluate_search.py`, `evaluate_vector_search.py` - retrieval evaluation
- `evaluate_prompts.py` - LLM answer evaluation
- `generate_ground_truth.py` - ground truth question generation
- `app.py` - main Streamlit user interface
- `dashboard.py` - monitoring dashboard
- `metrics_db.py` - SQLite storage for conversations and feedback
- `Dockerfile`, `Dockerfile.dashboard`, `docker-compose.yaml` - containerization

## Notes

This project does not use the DataTalksClub course FAQ documents as its knowledge base, per the project requirements.