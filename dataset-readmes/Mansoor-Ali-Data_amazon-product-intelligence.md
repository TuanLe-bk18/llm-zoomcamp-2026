# 🛍️ Amazon Fashion Product Intelligence System

> An end-to-end Retrieval-Augmented Generation (RAG) application that enables Product Managers, Brand Managers, Category Managers, and E-commerce Analysts to explore Amazon Fashion products using natural language instead of manually analyzing thousands of product listings and customer reviews.

The system combines **Hybrid Retrieval (Dense + BM25)**, **Large Language Models**, **Monitoring**, and **Evaluation** to generate accurate, grounded answers from Amazon Fashion product data.

---

🎯 Business Problem
Product managers and brand managers often need to analyze hundreds of product listings and thousands of customer reviews to understand customer sentiment, compare competitors, identify product strengths and weaknesses, and make pricing or merchandising decisions. Manual analysis is time-consuming and difficult to scale.

The Amazon Fashion Product Intelligence System addresses this challenge by combining Retrieval-Augmented Generation (RAG) with hybrid search to provide accurate, evidence-grounded answers from product metadata and customer reviews using natural language.
---

# ✨ Project Highlights

- End-to-End Production-style RAG Pipeline
- Hybrid Retrieval (Dense Embeddings + BM25 + Reciprocal Rank Fusion)
- Semantic Search using Sentence Transformers
- Chroma Vector Database
- Gemini-powered Answer Generation
- Modular & Maintainable Architecture
- Prompt Strategy Framework
- LLM-as-a-Judge Evaluation
- Monitoring Dashboard with Telemetry Metrics
- Interactive Streamlit Chat Interface

---

# ✅ Evaluation Criteria Mapping

This project was developed following the LLM Zoomcamp evaluation rubric. The table below maps each evaluation criterion to its implementation in this repository.

| Evaluation Criterion | Score | Repository Location | Description |
|----------------------|:----:|---------------------|-------------|
| **Problem Description** | ✅ **2/2** | `README.md` | Clearly defines the business problem and target users (Product Managers, Brand Managers, Category Managers, and E-commerce Analysts). |
| **Retrieval Flow** | ✅ **2/2** | `src/pipeline/`<br>`src/retrieval/`<br>`src/vector_store/`<br>`src/context_builder/`<br>`src/llm/` | Complete Retrieval-Augmented Generation (RAG) pipeline combining a knowledge base with Google Gemini for grounded answer generation. |
| **Retrieval Evaluation** | ✅ **2/2** | `src/retrieval/`<br>`src/evaluation/ground_truth/`<br>`src/evaluation/evaluator/` | Evaluates Dense Retrieval, BM25 Retrieval, and Hybrid Retrieval (Reciprocal Rank Fusion), selecting the best-performing approach. |
| **LLM Evaluation** | ✅ **2/2** | `src/evaluation/llm/` | Compares multiple prompt strategies and evaluates generated answers using an LLM-as-a-Judge evaluation framework. |
| **Interface** | ✅ **2/2** | `ui/app.py`<br>`ui/components/` | Interactive Streamlit application for natural language querying of Amazon Fashion products. |
| **Ingestion Pipeline** | ⚠️ **1/2** | `src/scripts/preprocess_data.py`<br>`src/indexing/run.py` | Automated preprocessing and indexing through Python scripts. No orchestration framework (Airflow, Prefect, dlt, etc.) is used. |
| **Monitoring** | ⚠️ **1/2** | `src/monitoring/`<br>`ui/monitoring.py` | Telemetry collection and interactive monitoring dashboard with multiple visualizations. |
| **Containerization** | ❌ **0/2** | — | Docker support is not included. |
| **Reproducibility** | ✅ **2/2** | `README.md`<br>`pyproject.toml`<br>`config/` | Complete setup instructions, dependency management using `uv`, configuration files, and execution commands are provided. |

---

## ⭐ Best Practices

| Best Practice | Status | Repository Location |
|---------------|:------:|---------------------|
| Hybrid Search (Dense + BM25 + Reciprocal Rank Fusion) | ✅ | `src/retrieval/` |
| Document Re-ranking | ❌ | Not Implemented |
| User Query Rewriting | ❌ | Not Implemented |

---

> **Note:** This table is a self-assessment based on the published LLM Zoomcamp evaluation rubric. Final scoring is determined by the project reviewers.

---

# 🏗️ System Architecture

![System Architecture](docs/architecture/system-architecture.png)

---

# 📂 Repository Structure

```text
amazon-product-intelligence/
│
├── config/                 # Application configuration
│
├── data/
│   ├── raw/                # Original dataset
│   ├── processed/          # Cleaned dataset
│   └── chroma/             # Vector database
│
├── docs/
│   ├── architecture/       # System diagrams
│   └── adr/                # Architecture decisions
│
├── outputs/
│   ├── evaluation/         # Evaluation reports
│   ├── monitoring/         # Telemetry logs
│   └── ground_truth/       # Generated benchmark dataset
│
├── src/
│   ├── preprocessing/      # Data cleaning pipeline
│   ├── document_builder/   # Product document generation
│   ├── chunking/           # Document chunk creation
│   ├── embeddings/         # Embedding generation
│   ├── indexing/           # Knowledge base indexing
│   ├── retrieval/          # Hybrid retrieval engine
│   ├── context_builder/    # Context assembly
│   ├── prompt_builder/     # Prompt construction
│   ├── llm/                # Gemini integration
│   ├── pipeline/           # End-to-end RAG workflow
│   ├── monitoring/         # Telemetry collection
│   ├── evaluation/         # Retrieval & LLM evaluation
│   ├── scripts/            # Utility & setup scripts
│   └── vector_store/       # ChromaDB management
│
├── ui/
│   ├── app.py              # Chat application
│   └── monitoring.py       # Monitoring dashboard
│
└── README.md               # Project documentation
```

---

# ⚙️ Quick Start

## Clone the Repository

```bash
git clone <repository-url>
cd amazon-product-intelligence
```

## Install Dependencies

```bash
uv sync
```

## Configure Environment Variables

Create a `.env` file.

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

## 1. Preprocess the Dataset

```bash
python -m src.scripts.preprocess_data
```

This cleans and standardizes the raw Amazon Fashion dataset.

---

## 2. Build the Vector & BM25 Indexes

```bash
python -m src.indexing.run
```

This:

- Generates product documents
- Chunks documents
- Creates embeddings
- Builds the Chroma vector database
- Builds the BM25 index

> **Note:** This step only needs to be run once or whenever the dataset changes.

## 4. Launch the Chat Application

```bash
PYTHONPATH=. uv run streamlit run ui/app.py
```

---

## 5. Launch the Monitoring Dashboard

```bash
PYTHONPATH=. uv run streamlit run ui/monitoring.py
```

### Evaluation
## Generate Ground Truth

```bash
python -m src.evaluation.ground_truth.run
```

---

## Run LLM Evaluation

```bash
python -m src.evaluation.llm.run
```

---

## Generate Evaluation Report

```bash
python -m src.evaluation.evaluator.run
```

---

# 📚 Documentation

| Document | Description |
|-----------|-------------|
| `docs/architecture/system-architecture.png` | Complete system architecture |
| `docs/architecture/system-design.md` | High-level design and component interactions |
| `docs/architecture/rag-pipeline.md` | End-to-end RAG pipeline workflow |
| `docs/adr/ADR-001-Hybrid-Retrieval.md` | Architectural Decision Record for Hybrid Retrieval |
| `docs/adr/ADR-002-Embedding-Model.md` | Embedding model selection rationale |

---

# 🛠️ Technologies

### Programming

- Python 3.12

### LLM

- Google Gemini

### Embeddings

- Sentence Transformers
- BAAI/bge-small-en-v1.5

### Retrieval

- ChromaDB
- BM25
- Reciprocal Rank Fusion

### User Interface

- Streamlit

### Data Processing

- Pandas
- NumPy

### Monitoring & Visualization

- Plotly
- Streamlit Dashboard

### Evaluation

- LLM-as-a-Judge
- Prompt Strategy Evaluation

### Development

- uv
- Git
- VS Code