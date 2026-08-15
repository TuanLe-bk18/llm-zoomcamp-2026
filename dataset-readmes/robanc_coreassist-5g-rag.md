# 🚀 CoreAssist

> **Retrieval-Augmented AI Assistant for 5G Packet Core Engineering**

<p align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)
![License](https://img.shields.io/badge/License-MIT-yellow)

</p>

### AI-Powered 5G Packet Core Engineering Assistant

Built with **Streamlit • PostgreSQL/pgvector • OpenAI GPT-4o-mini • Sentence Transformers • BAAI/bge-reranker-base • Docker**

**Developed by Rolando Bancod**


---

# 📚 Table of Contents

- [Overview](#-overview)
- [Problem Description](#problem-description)
- [Project Summary](#-project-summary)
- [Project Highlights](#-project-highlights)
- [Features](#-features)
- [RAG Architecture Overview](#-rag-architecture-overview)
- [System Architecture](#-system-architecture)
- [Application Workflow](#-application-workflow)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Evaluation](#-evaluation)
- [Monitoring](#-monitoring)
- [Reproducibility Guide](#-reproducibility-guide)
- [Running with Docker](#-running-with-docker)
- [Environment Variables](#-environment-variables)
- [Local Development](#-local-development)
- [Troubleshooting](#-troubleshooting)
- [Example Questions](#-example-questions)
- [Screenshots](#-screenshots)
- [Future Improvements](#-future-improvements)
- [Learning Objectives](#-learning-objectives)
- [Contributing](#-contributing)
- [References](#-references)
- [Acknowledgements](#-acknowledgements)
- [License](#-license)


---

## 📖 Overview

CoreAssist is a **Retrieval-Augmented Generation (RAG)** application that answers technical questions about the **3GPP TS 23.501 – System Architecture for the 5G Core (Release 19)** specification.

Instead of relying solely on a Large Language Model, CoreAssist retrieves relevant sections from the official 3GPP specification, reranks them using a cross-encoder model, and generates accurate, evidence-based responses using OpenAI GPT-4o-mini.

The project demonstrates an **end-to-end AI engineering workflow**, including:

- Semantic retrieval using PostgreSQL and pgvector
- Conversational query rewriting
- Cross-encoder reranking
- GPT-powered answer generation
- Retrieval evaluation
- LLM-based answer evaluation
- OpenTelemetry monitoring
- User feedback collection
- Containerized deployment with Docker
- Reproducible execution in both Docker and local environments

CoreAssist was developed as the capstone project for **LLM Zoomcamp (DataTalks.Club)** and showcases modern practices for building production-style Retrieval-Augmented Generation systems.

## Problem Description

Modern 5G Packet Core engineers rely on extensive 3GPP technical specifications to design, integrate, troubleshoot, and validate network functions. These specifications often span hundreds of pages, making it difficult and time-consuming to locate relevant information quickly. Traditional keyword searches frequently return too many irrelevant results, while general-purpose LLMs may generate answers that are not grounded in the official standards.

CoreAssist addresses this challenge by combining a Retrieval-Augmented Generation (RAG) pipeline with a knowledge base built from the **3GPP TS 23.501 Release 19** specification. Instead of relying solely on the LLM's internal knowledge, CoreAssist retrieves the most relevant sections of the specification, reranks them using a cross-encoder model, and generates grounded, context-aware responses.

By providing accurate, specification-based answers through an interactive interface, CoreAssist helps network engineers reduce the time spent searching documentation, improve troubleshooting efficiency, and increase confidence that responses are supported by the official 3GPP standard.


---


## Project Summary

CoreAssist is an end-to-end Retrieval-Augmented Generation (RAG) application that demonstrates the complete AI engineering workflow taught in the LLM Zoomcamp. The project combines automated document ingestion, semantic retrieval, cross-encoder reranking, LLM-powered answer generation, evaluation, monitoring, containerization, and reproducible deployment.

The table below summarizes how CoreAssist satisfies the project evaluation criteria.

| Evaluation Criteria | Implementation |
|---------------------|----------------|
| **Problem Description** | Clearly defines the challenges of searching large 3GPP specifications and explains how CoreAssist provides grounded, specification-based answers. |
| **Retrieval Flow** | Implements a complete RAG pipeline using document chunking, vector embeddings, PostgreSQL + pgvector retrieval, cross-encoder reranking, and GPT-4o-mini for answer generation. |
| **Retrieval Evaluation** | Evaluates multiple retrieval configurations using Hit@k and Mean Reciprocal Rank (MRR) to select the best-performing retrieval strategy. |
| **LLM Evaluation** | Evaluates multiple prompting strategies using an LLM-as-a-Judge framework and selects the best-performing prompt based on answer quality. |
| **Interface** | Interactive Streamlit web application with conversational chat interface and monitoring dashboard. |
| **Automated Ingestion Pipeline** | Fully automated Python ingestion pipeline for loading, chunking, embedding, and storing the 3GPP specification into PostgreSQL. |
| **Monitoring** | Collects user feedback, application metrics, retrieval metrics, and visualizes system performance through a monitoring dashboard. |
| **Containerization** | Complete Docker Compose deployment including PostgreSQL and the Streamlit application with automatic initialization. |
| **Reproducibility** | Comprehensive setup instructions, Docker deployment, local development workflow, dependency management using `uv`, and reproducible project structure. |
| **Document Re-ranking** | Uses the **BAAI/bge-reranker-base** cross-encoder model to improve retrieval accuracy before LLM generation. |
| **User Query Rewriting** | Rewrites user queries to improve semantic retrieval and increase answer relevance. |

---


# 🌟 Project Highlights

CoreAssist demonstrates a complete Retrieval-Augmented Generation (RAG) workflow for technical question answering using the official **3GPP TS 23.501 Release 19** specification.

### Highlights

- ✅ End-to-end Retrieval-Augmented Generation (RAG) pipeline
- ✅ Semantic search using PostgreSQL + pgvector
- ✅ Knowledge base built from **3GPP TS 23.501 Release 19**
- ✅ Cross-encoder reranking for improved retrieval accuracy
- ✅ GPT-4o-mini answer generation
- ✅ Query rewriting using conversation history
- ✅ Multi-turn conversational interface
- ✅ Retrieval evaluation (Hit@k, MRR)
- ✅ Automated LLM evaluation
- ✅ OpenTelemetry monitoring
- ✅ Operational monitoring dashboard
- ✅ User feedback analytics
- ✅ Docker deployment
- ✅ Reproducible local and Docker execution
- ✅ CPU-optimized inference pipeline


# ✨ Features

### Retrieval-Augmented Generation

- Semantic vector search using PostgreSQL + pgvector
- Knowledge base generated from the official 3GPP TS 23.501 specification
- Cross-encoder reranking for improved retrieval precision
- Context-aware answer generation using GPT-4o-mini

### Conversational AI

- Multi-turn conversations
- Query rewriting using conversation history
- Context-aware follow-up questions

### Evaluation

- Retrieval evaluation (Hit@1, Hit@3, Hit@5, MRR)
- Automated LLM evaluation
- Grounded response generation

### Monitoring

- Response latency
- Token usage
- Retrieved document count
- Context length
- Top reranker score
- User feedback collection
- Helpful response rate

### Deployment

- Dockerized application
- Local development workflow
- Reproducible execution
- CPU-only runtime

---

# 📖 RAG Architecture Overview

Large Language Models perform exceptionally well on general knowledge but may hallucinate or overlook important details when answering questions in specialized technical domains.

CoreAssist addresses this limitation using **Retrieval-Augmented Generation (RAG)**. Rather than relying solely on the language model's pre-trained knowledge, the application retrieves relevant sections from the official **3GPP TS 23.501 Release 19** specification stored in a PostgreSQL database with pgvector embeddings. Retrieved passages are then reranked using the **BAAI/bge-reranker-base** cross-encoder before being provided as context to GPT-4o-mini.

This retrieval-first approach improves factual accuracy, grounds responses in authoritative documentation, and reduces hallucinations while maintaining natural conversational interactions.

Beyond question answering, CoreAssist demonstrates a complete AI engineering workflow that includes document ingestion, semantic indexing, retrieval, reranking, LLM integration, automated evaluation, operational monitoring, user feedback collection, and reproducible deployment using Docker.


# 🏗 System Architecture

CoreAssist follows a modular Retrieval-Augmented Generation (RAG) architecture that combines semantic retrieval, cross-encoder reranking, and GPT-based answer generation.

```mermaid
flowchart TD
    A["User"] --> B["Streamlit UI"]

    B --> C["Conversation Memory"]
    C --> D["Query Rewriter"]

    D --> E["Embedding Model<br>all-MiniLM-L6-v2"]
    E --> F[("PostgreSQL + pgvector")]

    F --> G["Top-k Retrieved Chunks"]
    G --> H["Cross-Encoder Reranker<br>BAAI/bge-reranker-base"]

    H --> I["Top-Ranked Context"]
    I --> J["OpenAI GPT-4o-mini"]

    J --> K["Final Answer"]
    K --> B

    J --> L[("Monitoring Database")]
    B --> L

    L --> M["Monitoring Dashboard"]
```

### Pipeline Summary

1. The user submits a question through the Streamlit interface.
2. Conversation history is used to rewrite follow-up questions when appropriate.
3. The rewritten query is converted into an embedding.
4. PostgreSQL with pgvector retrieves the most semantically similar document chunks.
5. Retrieved passages are reranked using the BAAI/bge-reranker-base cross-encoder.
6. The highest-ranked passages are supplied to GPT-4o-mini.
7. The generated response is returned to the user.
8. Operational metrics and user feedback are stored for monitoring and evaluation.

---

# 🔄 Application Workflow

```text
                         User Question
                               │
                               ▼
                    Conversation Memory
                               │
                               ▼
                      Query Rewriting
                               │
                               ▼
                     Embedding Generation
                               │
                               ▼
              PostgreSQL + pgvector Retrieval
                               │
                               ▼
                Cross-Encoder Reranking
                               │
                               ▼
                    GPT-4o-mini Response
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
      Monitoring Metrics                User Feedback
               │                               │
               └───────────────┬───────────────┘
                               ▼
                     Monitoring Dashboard
```

---

# 🛠 Technology Stack

| Category | Technology | Purpose |
|-----------|------------|---------|
| Programming Language | Python 3.11 | Core application development |
| Web Framework | Streamlit | Interactive web interface |
| LLM | OpenAI GPT-4o-mini | Answer generation |
| Embedding Model | sentence-transformers/all-MiniLM-L6-v2 | Semantic vector embeddings |
| Cross-Encoder | BAAI/bge-reranker-base | Retrieval reranking |
| Vector Database | PostgreSQL + pgvector | Semantic search |
| Database Driver | psycopg | PostgreSQL connectivity |
| Observability | OpenTelemetry | Request tracing |
| Monitoring | PostgreSQL + Streamlit | Operational dashboard |
| Package Manager | uv | Dependency management |
| Containerization | Docker & Docker Compose | Reproducible deployment |
| Version Control | Git & GitHub | Source code management |

---

# 📁 Project Structure

```text
coreassist-5g-rag/
│
├── app/
│   ├── CoreAssist.py               # Main Streamlit application
│   └── pages/                      # Monitoring dashboard pages
│
├── ingestion/                      # Document ingestion pipeline
│   ├── export_chunks.py
│   ├── init_db.py
│   └── store_embeddings.py
│
├── rag/                            # RAG orchestration
│
├── retrieval/                      # Semantic retrieval & reranking
│
├── monitoring/                     # Monitoring utilities
│
├── evaluation/                     # Retrieval & LLM evaluation
│
├── scripts/
│   └── create_monitoring_tables.py
│
├── database/                       # Database utilities
│
├── data/                           # Generated document chunks
│
├── docs/
│   └── packet_core/
│       └── TS23501.docx            # Source specification
│
├── screenshots/                    # README screenshots
│
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## 📂 Project Organization

The repository is organized into modular components that separate document ingestion, retrieval, evaluation, monitoring, and application logic.

- **app/** contains the Streamlit user interface and dashboard pages.
- **ingestion/** prepares the 3GPP specification, generates document chunks, and stores vector embeddings.
- **retrieval/** performs semantic search and cross-encoder reranking.
- **rag/** orchestrates retrieval and LLM response generation.
- **evaluation/** measures retrieval quality and LLM answer quality.
- **monitoring/** collects operational metrics and powers the monitoring dashboard.
- **database/** contains PostgreSQL helper utilities.
- **scripts/** includes one-time initialization scripts such as monitoring table creation.

This modular design makes the project easier to extend, test, and maintain.


# 📊 Evaluation

CoreAssist was evaluated using both **retrieval metrics** and **LLM-based answer evaluation** to measure the effectiveness of the Retrieval-Augmented Generation (RAG) pipeline.

---

## Retrieval Evaluation

Multiple retrieval configurations were evaluated using Hit@k and Mean Reciprocal Rank (MRR). The best-performing retrieval pipeline was selected for the final application.

### Retrieval Metrics

| Metric | Score |
|---------|------:|
| Hit@1 | **0.650** |
| Hit@3 | **0.900** |
| Hit@5 | **1.000** |
| Mean Reciprocal Rank (MRR) | **0.770** |

### Metric Definitions

- **Hit@1** – Percentage of queries where the correct document was ranked first.
- **Hit@3** – Percentage of queries where the correct document appeared within the top three retrieved passages.
- **Hit@5** – Percentage of queries where the correct document appeared within the top five retrieved passages.
- **MRR (Mean Reciprocal Rank)** – Measures how highly the correct document is ranked on average.

These results demonstrate that the retrieval pipeline consistently identifies relevant specification sections before answer generation.

---

## LLM Evaluation

Multiple prompting strategies were evaluated using an LLM-as-a-Judge framework. The highest-performing prompt configuration was selected for the final application.

### Overall Score

**4.08 / 5**

Evaluation criteria included:

- ✅ Correctness
- ✅ Completeness
- ✅ Relevance
- ✅ Grounding in retrieved context

Using an LLM judge provides an automated and scalable method for assessing answer quality while encouraging responses that remain grounded in retrieved documentation.

---

## Evaluation Workflow

```text
Evaluation Dataset
        │
        ▼
Retrieve Relevant Chunks
        │
        ▼
Generate Response
        │
        ▼
LLM Judge Evaluation
        │
        ▼
Overall Quality Score
```

---

# 📈 Monitoring

CoreAssist includes built-in operational monitoring to help evaluate system performance and user interactions during runtime.

Monitoring metrics are collected automatically for every request and visualized through the Streamlit dashboard.

---

## Collected Metrics

### Application Performance

- Response latency
- Total response time
- Token usage
- Context length
- Retrieved document count

### Retrieval Quality

- Top reranker score
- Retrieval confidence
- Number of retrieved passages

### User Analytics

- User feedback
- Helpful response rate
- Total conversations
- Total questions answered

---

## Monitoring Dashboard

The monitoring dashboard provides visibility into application behavior and system performance.

The monitoring dashboard includes six operational charts that visualize application performance, retrieval quality, and user interactions.

- Response Time
- Token Usage
- Retrieval Quality
- User Feedback
- Retrieved Documents
- Context Length

This information helps evaluate retrieval quality, monitor system health, and identify opportunities for future optimization.


---

# 🚀 Reproducibility Guide

CoreAssist was designed to be reproducible across multiple development environments. The project supports both a fully containerized Docker deployment and a native local development workflow.

Two installation methods are provided:

### Option 1 – Docker Deployment (Recommended)

The Docker deployment automatically:

- Creates the PostgreSQL database
- Generates document chunks
- Creates vector embeddings
- Loads the knowledge base
- Creates monitoring tables
- Starts the Streamlit application

See the **Running with Docker** section for detailed instructions.

### Option 2 – Local Development

For development and debugging, CoreAssist can also be run locally while using PostgreSQL in Docker.

The local workflow includes:

- Installing dependencies with `uv`
- Starting PostgreSQL
- Generating document chunks
- Initializing the database
- Creating embeddings
- Creating monitoring tables
- Running the Streamlit application locally

See the **Local Development** section for detailed instructions.

---

## Validation

The following execution paths were successfully tested:

| Environment | Status |
|------------|--------|
| Fresh Git clone | ✅ |
| Docker deployment | ✅ |
| Local Streamlit application | ✅ |
| PostgreSQL + pgvector | ✅ |
| Automatic chunk generation | ✅ |
| Automatic embedding ingestion | ✅ |
| Automatic monitoring table creation | ✅ |

Both Docker and native local execution were validated using the instructions provided in this README.

---

# 🐳 Running with Docker

CoreAssist is fully containerized using **Docker Compose**, making deployment consistent across development environments.

---

## Prerequisites

Before running the application, ensure the following software is installed:

- Python 3.11+
- Docker Desktop
- Git
- OpenAI API key

---

## 1. Clone the Repository

```bash
git clone https://github.com/robanc/coreassist-5g-rag.git
cd coreassist-5g-rag
```

---

## 2. Configure Environment Variables

Copy the sample environment file.

### Windows

```powershell
Copy-Item .env.example .env
```

### Linux/macOS

```bash
cp .env.example .env
```

Edit the `.env` file and provide your OpenAI API key.

---

## 3. Build and Start

```bash
docker compose up --build
```

During the first startup, CoreAssist automatically:

- Generates document chunks
- Initializes PostgreSQL
- Creates vector embeddings
- Loads the knowledge base
- Creates monitoring tables
- Starts the Streamlit application

The initial build may take several minutes because Docker downloads dependencies and the reranker model is initialized.

---

## 4. Open the Application

Once all services are running, open:

```
http://localhost:8501
```

---

## 5. Verify Installation

Ask a question such as:

> What is the purpose of the UPF in a 5G Core network?

Verify that:

- ✅ The assistant generates a response.
- ✅ Retrieved context is displayed (if enabled).
- ✅ Monitoring metrics are recorded.
- ✅ User feedback can be submitted.

---

## 6. Stop the Application

Press:

```
Ctrl + C
```

Remove the containers:

```bash
docker compose down
```

---

# 🔑 Environment Variables

CoreAssist uses environment variables to configure database connectivity and OpenAI access.

Create a `.env` file in the project root.

```text
OPENAI_API_KEY=your_openai_api_key

DATABASE_URL=postgresql://coreassist:coreassist@localhost:5432/coreassist

OPENAI_MODEL=gpt-4o-mini

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

RETRIEVAL_LIMIT=5
```

| Variable | Description |
|-----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `DATABASE_URL` | PostgreSQL connection string |
| `OPENAI_MODEL` | OpenAI model used for answer generation |
| `EMBEDDING_MODEL` | Sentence Transformer used for semantic embeddings |
| `RETRIEVAL_LIMIT` | Number of retrieved passages passed to the reranker |

> **Important:** Never commit your `.env` file to GitHub. Store only placeholder values in `.env.example`.


# 💻 Local Development

This workflow runs the **Streamlit application locally** while using the PostgreSQL database running in Docker.

It is recommended for development and debugging because code changes are reflected immediately without rebuilding the Docker image.

---

## 1. Install Dependencies

Install all required Python packages:

```bash
uv sync --locked
```

---

## 2. Configure Environment Variables

Copy the sample environment file.

### Windows

```powershell
Copy-Item .env.example .env
```

### Linux/macOS

```bash
cp .env.example .env
```

Update the `.env` file with your OpenAI API key.

---

## 3. Start PostgreSQL

Start only the PostgreSQL service:

```bash
docker compose up -d postgres
```

Verify the database is running:

```bash
docker ps
```

---

## 4. Generate the Knowledge Base

Generate document chunks from the 3GPP specification.

```bash
uv run python -m ingestion.export_chunks
```

---

## 5. Initialize the Database

Create database tables and load embeddings.

```bash
uv run python -m ingestion.init_db
uv run python -m ingestion.store_embeddings
uv run python -m scripts.create_monitoring_tables
```

---

## 6. Run CoreAssist

```bash
uv run streamlit run app/CoreAssist.py
```

The application will be available at:

```
http://localhost:8501
```

To stop the application, return to the terminal where Streamlit is running and press:

```text
Ctrl + C
```

When prompted:

```text
Terminate batch job (Y/N)?
```

Type:

```text
Y
```

and press **Enter**.

---

## 7. Stop PostgreSQL

When finished:

```bash
docker compose stop postgres
```

---

# 🛠 Troubleshooting

## PostgreSQL Connection Timeout

If you encounter an error such as:

```
psycopg.errors.ConnectionTimeout
```

ensure PostgreSQL is running:

```bash
docker compose up -d postgres
```

---

## PostgreSQL Port 5432 Already in Use

If Docker displays an error such as:

```text
Bind for 0.0.0.0:5432 failed: port is already allocated
```

another PostgreSQL service or Docker container is already using port `5432`.

Check running containers:

```bash
docker ps
```

You can either:

- Stop the existing PostgreSQL container, or
- Change the host port mapping in `docker-compose.yml`:

```yaml
ports:
  - "5433:5432"
```

After making the change, restart the containers:

```bash
docker compose down
docker compose up --build
```

## OpenAI API Connection

Verify network connectivity:

Windows

```powershell
Test-NetConnection api.openai.com -Port 443
```

Linux/macOS

```bash
curl https://api.openai.com
```

---

## Slow First Startup

The first startup may take several minutes because CoreAssist:

- generates document chunks
- creates vector embeddings
- initializes PostgreSQL
- downloads the reranker model
- creates monitoring tables

Subsequent startups are significantly faster.

---

## Slow First Response

The first question submitted after launching the application may take longer because the cross-encoder reranker model is loaded into memory.

Subsequent responses are typically much faster.

---

## Docker Build Issues

If Docker images become outdated or corrupted:

```bash
docker compose down
docker compose build --no-cache
docker compose up
```

---

# 💬 Example Questions

Try asking questions such as:

- What is the purpose of the AMF?
- How does the SMF communicate with the UPF?
- Explain the N2 interface.
- What services are provided by the NRF?
- Describe the UE Registration procedure.
- What is the role of the AUSF?
- Explain the PDU Session Establishment procedure.
- How does network slicing work in the 5G Core?
- What is the difference between the SMF and the UPF?
- Which network functions communicate over the N11 interface?

---

# 📸 Screenshots

## Home Page

![Home Page](screenshots/home.png)

---

## Question Answering

![Question Answering](screenshots/question-answer.png)

---

## Monitoring Dashboard

![Monitoring Dashboard](screenshots/dashboard.png)

---

# 🚀 Future Improvements

Future enhancements may include:

- Hybrid BM25 + vector retrieval
- Support for additional 3GPP specifications (TS 23.502, TS 29.xxx)
- Source citations in generated responses
- Streaming responses
- Multi-document knowledge bases
- Authentication and user management
- Kubernetes deployment
- CI/CD using GitHub Actions
- GPU inference support
- Advanced retrieval analytics


---

# 🎯 Learning Objectives

This project demonstrates practical implementation of modern AI engineering concepts, including:

- Retrieval-Augmented Generation (RAG)
- Vector databases
- Semantic search
- Cross-encoder reranking
- Prompt engineering
- LLM evaluation
- Operational monitoring
- Containerized deployment
- Reproducible AI workflows

These concepts are commonly used in production AI assistants and enterprise knowledge retrieval systems.


---

# 🤝 Contributing

Contributions, bug reports, and suggestions are welcome.

If you would like to contribute:

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Submit a Pull Request.

Please open an issue first if you plan to make significant changes.

---

# 📚 References

- 3GPP TS 23.501 – System Architecture for the 5G System
- OpenAI API Documentation
- PostgreSQL
- pgvector
- Streamlit
- Sentence Transformers
- Hugging Face
- OpenTelemetry
- Docker
- DataTalks.Club LLM Zoomcamp

---

# 🙏 Acknowledgements

This project was developed as the capstone project for **LLM Zoomcamp** by **DataTalks.Club**.

Special thanks to the instructors and contributors for creating an outstanding hands-on course that emphasizes practical AI engineering, Retrieval-Augmented Generation, evaluation, monitoring, and reproducible deployment.

The open-source AI community—including contributors to PostgreSQL, pgvector, Hugging Face, Streamlit, OpenTelemetry, Docker, and OpenAI—provided the tools and inspiration that made this project possible.

---

# 📄 License

This project is licensed under the **MIT License**.

See the LICENSE file for additional information.

---

## ⭐ If you found this project useful...

If this repository helped you learn about Retrieval-Augmented Generation, consider giving it a ⭐ on GitHub.

Feedback and suggestions are always welcome!