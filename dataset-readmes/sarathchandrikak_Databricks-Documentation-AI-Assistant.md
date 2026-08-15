# 🚀 Databricks Documentation AI Assistant

A **Retrieval-Augmented Generation (RAG)** application that enables natural language interaction with the official Databricks documentation.

The system automatically ingests documentation from the official Databricks website, builds a semantic knowledge base using OpenAI embeddings and vector search, and provides accurate, citation-backed responses through a conversational interface.

Designed with a modular architecture, the project separates document ingestion, indexing, retrieval, and serving pipelines, making it suitable for production deployment and future extensibility.

---

# Project Highlights

* 📚 Automated documentation ingestion from the official Databricks documentation sitemap
* 📝 Intelligent HTML → Markdown conversion
* ✂️ Token-aware chunking with configurable overlap
* 🧠 OpenAI Embeddings (`text-embedding-3-small`)
* 🔎 Semantic Vector Search using ChromaDB
* 🤖 Retrieval-Augmented Generation (RAG) with the OpenAI Responses API
* 📖 Grounded answers with source attribution
* 💬 Interactive Streamlit chat application
* ⚡ Modular, production-oriented architecture
* 🔄 Offline indexing pipeline separated from the online inference pipeline

---

# System Architecture

```text
                        Databricks Documentation
                                   │
                                   ▼
                    Documentation Ingestion Pipeline
                    (Sitemap + Content Extraction)
                                   │
                                   ▼
                         Markdown Document Store
                                   │
                                   ▼
                        Token-based Chunk Generator
                                   │
                                   ▼
                    OpenAI Embedding Generation
                                   │
                                   ▼
                        Chroma Vector Database
                                   │
                        Semantic Retrieval Engine
                                   │
                                   ▼
                           Prompt Construction
                                   │
                                   ▼
                       OpenAI Responses API
                                   │
                                   ▼
                      Grounded AI Generated Answer
                                   │
                                   ▼
                          Streamlit Web Interface
```

---

# Features

## Documentation Processing

* Automatic sitemap discovery
* Bulk documentation download
* Markdown conversion
* Duplicate removal
* Metadata preservation

---

## Semantic Indexing

* Token-aware chunk generation
* Configurable chunk size
* Configurable overlap
* OpenAI embedding generation
* Persistent vector database

---

## Intelligent Retrieval

* Semantic similarity search
* Top-K retrieval
* Metadata preservation
* Source tracking
* Configurable retrieval depth

---

## AI Assistant

* Natural language interface
* Context-aware answers
* Grounded responses
* Source citations
* Hallucination reduction through Retrieval-Augmented Generation

---

# Technology Stack

## Backend

* Python
* OpenAI Python SDK

## Retrieval

* ChromaDB
* OpenAI Embeddings
* tiktoken

## Data Processing

* requests
* trafilatura
* tqdm

## Frontend

* Streamlit

## Configuration

* python-dotenv

---

# Repository Structure

```text
Databricks-Documentation-AI-Assistant/

├── app.py
├── README.md
├── pyproject.toml
├── requirements.txt
├── uv.lock
│
├── src/
│   ├── assistant.py
│   ├── config.py
│   ├── retriever.py
│   ├── prompt_builder.py
│   ├── vector_store.py
│   └── scripts/
│       ├── download_sitemap.py
│       ├── download_docs.py
│       ├── chunker.py
│       └── index_vectors.py
│
├── data/
│   ├── raw/
│   ├── chunks/
│   └── urls.json
│
└── vector_db/
```

---

# End-to-End Pipeline

## Stage 1 — Documentation Discovery

The application discovers official Databricks documentation pages through the published sitemap.

```
Sitemap
    ↓
Documentation URLs
```

---

## Stage 2 — Document Ingestion

Each documentation page is downloaded, cleaned, and converted into Markdown while preserving metadata.

```
Documentation URL
      ↓
HTML Download
      ↓
Markdown Extraction
```

---

## Stage 3 — Chunk Generation

Documentation is segmented into token-aware overlapping chunks to optimize semantic retrieval.

```
Markdown
     ↓
Tokenization
     ↓
Semantic Chunks
```

---

## Stage 4 — Embedding Generation

Each chunk is converted into a dense vector representation using OpenAI Embeddings.

```
Chunk
   ↓
Embedding
```

---

## Stage 5 — Vector Indexing

Embeddings and metadata are stored in a persistent ChromaDB vector database.

Stored metadata includes:

* Title
* URL
* Chunk ID
* Document Content

---

## Stage 6 — Semantic Retrieval

Every user query is embedded and compared against the vector database to retrieve the most relevant documentation chunks.

```
Question
     ↓
Embedding
     ↓
Vector Similarity Search
     ↓
Top-K Relevant Chunks
```

---

## Stage 7 — Retrieval-Augmented Generation

Retrieved documentation is injected into a structured prompt before invoking the OpenAI Responses API.

This grounding process significantly improves factual accuracy while reducing hallucinations.

```
Retrieved Context
        ↓
Prompt Builder
        ↓
OpenAI Responses API
        ↓
Grounded Response
```

---

# Running the Indexing Pipeline

### Download Documentation URLs

```bash
python src/scripts/download_sitemap.py
```

---

### Download Documentation

```bash
python src/scripts/download_docs.py
```

---

### Generate Chunks

```bash
python src/scripts/chunker.py
```

---

### Generate Embeddings and Build the Vector Database

```bash
python src/scripts/index_vectors.py
```

---

# Running the Application

```bash
streamlit run app.py
```

The application starts a conversational interface where users can ask technical questions related to Databricks services, architecture, administration, governance, Spark, Delta Lake, SQL, and platform features.

---

# Example Questions

* What is Unity Catalog?
* How does Delta Lake guarantee ACID transactions?
* Explain Databricks Auto Loader.
* What is Photon?
* Compare Delta Live Tables and Workflows.
* How does Unity Catalog manage permissions?
* Explain Databricks Connect.
* How do I optimize Spark jobs?
* How do cluster policies work?
* What are the advantages of the Lakehouse architecture?

---

# Design Principles

The application follows a modular architecture where each component has a single responsibility.

| Component           | Responsibility                               |
| ------------------- | -------------------------------------------- |
| download_sitemap.py | Discover documentation URLs                  |
| download_docs.py    | Download and clean documentation             |
| chunker.py          | Generate semantic chunks                     |
| index_vectors.py    | Create embeddings and build the vector index |
| retriever.py        | Perform semantic retrieval                   |
| prompt_builder.py   | Construct grounded prompts                   |
| assistant.py        | Orchestrate retrieval and generation         |
| app.py              | User interface                               |

---

# Scalability

The architecture has been designed for future enhancements without major structural changes.

Potential extensions include:

* PostgreSQL + pgvector
* Hybrid Search (BM25 + Vector Search)
* Cross-Encoder Reranking
* Conversation Memory
* Incremental Documentation Refresh
* Multi-cloud filtering (AWS / Azure / GCP)
* Docker Deployment
* Kubernetes Deployment
* REST API
* Authentication
* Observability and Monitoring

---

# Why Retrieval-Augmented Generation?

Instead of relying solely on an LLM's pretrained knowledge, this project retrieves the most relevant documentation before generating an answer.

This approach provides:

* Higher factual accuracy
* Grounded responses
* Up-to-date information
* Source attribution
* Reduced hallucinations

---

# Future Roadmap

* Hybrid Retrieval (Keyword + Vector Search)
* Metadata-based filtering
* Re-ranking models
* Streaming responses
* Evaluation framework
* Feedback collection
* Automated documentation synchronization
* Multi-document summarization
* Enterprise authentication
* Containerized deployment

---

# License

This project is intended for educational, research, and portfolio purposes. Documentation content belongs to Databricks and is retrieved from publicly available official documentation.
