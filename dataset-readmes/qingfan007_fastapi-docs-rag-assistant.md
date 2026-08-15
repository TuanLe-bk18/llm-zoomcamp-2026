# FastAPI Documentation RAG Assistant

A Retrieval-Augmented Generation (RAG) assistant that answers questions about the official FastAPI documentation using semantic vector search and a Groq-hosted large language model.

The project was built as the project attempt 1 for LLM Zoomcamp 2026.

## Features

- Official FastAPI tutorial documentation as the knowledge base
- Markdown preprocessing and source-code reference expansion
- Semantic vector search using local ONNX embeddings
- RAG answers with source references
- Retrieval evaluation using Hit Rate and MRR
- LLM prompt evaluation
- FastAPI REST API
- Conversation and token-usage tracking with SQLite
- User feedback collection
- Streamlit monitoring dashboard
- Docker Compose setup for reproducible local deployment

## Architecture

```text
                           Official FastAPI Documentation
                                       │
                                       ▼
                          Download & Markdown Processing
                                       │
                                       ▼
                          Source Reference Expansion
                                       │
                                       ▼
                           Section & Chunk Generation
                                       │
                                       ▼
                         Local ONNX Embedding Generation
                                       │
                                       ▼
                             Semantic Vector Search
                                       │
                                       ▼
                         Top-k Relevant Documentation
                                       │
                                       ▼
                              Groq-hosted LLM
                                       │
                                       ▼
                        Answer with Source References
                                       │
                                       ▼
                  SQLite Monitoring & Streamlit Dashboard
```

## How It Works

### Data Preparation

1. Download the official FastAPI tutorial documentation from GitHub.
2. Download referenced source files used by the documentation.
3. Expand source-code references into processed Markdown files.
4. Split the processed documents into structured sections.
5. Build semantic chunks for retrieval.
6. Download the local ONNX embedding model.

### Question Answering Pipeline

1. Convert the user's question into an embedding vector.
2. Perform semantic vector search over all documentation chunks.
3. Retrieve the most relevant documentation chunks.
4. Construct the RAG prompt using the retrieved context.
5. Generate the final answer using the Groq LLM.
6. Return the answer together with the corresponding documentation sources.
7. Store conversation history, token usage, response time, and user feedback in SQLite for monitoring.

## Project Structure

```text
.
├── app/                  # FastAPI application, RAG pipeline, dashboard
├── scripts/              # Data ingestion, preprocessing and evaluation scripts
├── data/
│   ├── source/           # Raw downloaded documentation
│   ├── processed/        # Processed documents and chunks
│   ├── ground-truth.csv  # Retrieval evaluation dataset
│   └── app.db            # SQLite database
├── evaluation/           # Evaluation results
├── models/               # Local ONNX embedding model
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Tech Stack

- Python 3.12
- FastAPI
- Groq API
- ONNX Runtime
- Hugging Face Tokenizers
- SQLite
- Streamlit
- Docker & Docker Compose
- uv (Python package manager)

## Getting Started

### Prerequisites

Make sure the following tools are installed:

- Docker
- Docker Compose
- A Groq API key

### Environment Configuration

Create a local environment file from the example:

```bash
cp .env.example .env
```

Open `.env` and add your Groq API key:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Do not commit the `.env` file to GitHub.

## Run with Docker Compose

Build and start the complete application:

```bash
docker compose up --build
```

The Docker Compose setup runs three services:

- `setup`: downloads and processes the FastAPI documentation and prepares the embedding model
- `api`: runs the FastAPI RAG service
- `dashboard`: runs the Streamlit monitoring dashboard

When the application is running, open:

- Swagger API documentation: http://localhost:8000/docs
- Monitoring dashboard: http://localhost:8501

To stop the services:

```bash
docker compose down
```

After the first successful setup, existing processed data and model files are reused on subsequent starts.

## API Usage

### Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

### Ask a Question

```http
POST /ask
```

Example request:

```json
{
  "question": "How do I define a request body with Pydantic models in FastAPI?"
}
```

Example response:

```json
{
  "conversation_id": "50f875a3-cb03-4d83-bfd4-02f451867dbf",
  "answer": "To define a request body with Pydantic models in FastAPI, declare a class that inherits from BaseModel and use it as the type of a route parameter.",
  "sources": [
    {
      "title": "Request Body",
      "section": "Request body + path parameters",
      "url": "https://fastapi.tiangolo.com/tutorial/body/"
    },
    {
      "title": "Body - Multiple Parameters",
      "section": "Mix `Path`, `Query` and body parameters",
      "url": "https://fastapi.tiangolo.com/tutorial/body-multiple-params/"
    },
    {
      "title": "Extra Models",
      "section": "`Union` or `anyOf`",
      "url": "https://fastapi.tiangolo.com/tutorial/extra-models/"
    }
  ],
  "model": "llama-3.3-70b-versatile",
  "response_time_ms": 2081.33,
  "usage": {
    "prompt_tokens": 1586,
    "completion_tokens": 209,
    "total_tokens": 1795
  }
}
```

### Submit Feedback

```http
POST /feedback
```

Example positive feedback:

```json
{
  "conversation_id": "50f875a3-cb03-4d83-bfd4-02f451867dbf",
  "value": 1
}
```

Example negative feedback:

```json
{
  "conversation_id": "50f875a3-cb03-4d83-bfd4-02f451867dbf",
  "value": -1
}
```

Example response:

```json
{
  "status": "ok"
}
```

## Evaluation

### Retrieval Evaluation

Retrieval quality was evaluated using a manually created ground-truth dataset containing 30 questions from the FastAPI documentation.

For each question, the retriever returned the top 5 most relevant chunks. Performance was measured using:

- **Hit Rate**: whether the expected document appeared anywhere in the top 5 results
- **Mean Reciprocal Rank (MRR)**: how highly the first relevant document was ranked

| Retrieval Method | Hit Rate | MRR |
|------------------|---------:|----:|
| Keyword Search | 0.8333 | 0.7150 |
| Vector Search | **0.9667** | **0.9011** |

Semantic vector search achieved better results than keyword search on both metrics and was selected as the retrieval method used by the application.

The full evaluation results are stored in:

```text
evaluation/retrieval_results.json
```

### LLM Evaluation

Two prompt variants were evaluated using 10 representative questions from the FastAPI documentation.

Each generated answer was scored from 1 to 5 based on:

- Correctness
- Relevance
- Completeness
- Grounding in the retrieved documentation

| Prompt | Average Score |
|--------|--------------:|
| Prompt A | 5.0 |
| Prompt B | 5.0 |

Both prompt variants achieved the same average score. `prompt_a` was selected as the final prompt because it produced correct and complete answers while generally remaining more concise.

Evaluation configuration:

```text
Model: llama-3.3-70b-versatile
Number of questions: 10
Selected prompt: prompt_a
```
The full evaluation results are stored in:
```text
evaluation/llm_results.json
```
The evaluation can be reproduced with:
```bash
uv run python scripts/evaluate_llm.py
```
The evaluation uses an LLM judge, so scores may vary slightly between runs.

## Monitoring

The application stores conversation and feedback data in a local SQLite database.

For each question, the following information is recorded:

- Conversation ID
- User question
- Generated answer
- Retrieved sources
- LLM model
- Response time
- Prompt token usage
- Completion token usage
- Total token usage
- User feedback

A Streamlit dashboard provides a simple interface for monitoring:

- Total conversations
- Average response time
- Total token usage
- Positive and negative feedback
- Recent questions and generated answers

Start the dashboard locally with:

```bash
uv run streamlit run app/dashboard.py
```
Then open: http://localhost:8501


When the application is started with Docker Compose, the dashboard starts automatically together with the API.


## Screenshots

### Swagger API

![Swagger](screenshots/swagger.png)

### Monitoring Dashboard

![Dashboard](screenshots/dashboard.png)

## Known Limitations

- The knowledge base currently includes the official FastAPI tutorial documentation only.
- The application requires a valid Groq API key.
- Retrieval uses semantic vector search without reranking.
- Conversation history is stored locally in SQLite.

## License

This project was created for the LLM Zoomcamp 2026 project.
The FastAPI documentation remains the copyright of its respective authors.

## Acknowledgements

- DataTalks.Club — LLM Zoomcamp
- FastAPI Documentation
- Groq
- Hugging Face
- ONNX Runtime