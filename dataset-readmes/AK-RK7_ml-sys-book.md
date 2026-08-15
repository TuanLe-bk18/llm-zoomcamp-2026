# Harvard MLSys Study Assistant ("Zero to Hero")

A Retrieval-Augmented Generation (RAG) application for the **LLM Zoomcamp Final Project**.

The assistant answers questions about the Harvard **CS249r: Machine Learning Systems** textbook by retrieving relevant textbook passages and generating grounded answers using an LLM.

The goal is to provide students with a reliable study assistant that can search hundreds of pages of Machine Learning Systems material using natural language questions.

---

> # Disclaimer
>
> This project was developed as an educational project for the **LLM Zoomcamp Final Project**.
>
> It is **not affiliated with, endorsed by, or sponsored by Harvard University or the authors of the CS249r: Machine Learning Systems textbook**.
>
> The knowledge base is created from the publicly available Quarto and Markdown source files from  Harvard CS249r Book.
>
> Repository: https://github.com/harvard-edge/cs249r_book
>
> All rights to the original textbook content belong to their respective authors and copyright holders.
> 
> This application is intended only as a study aid. **AI-generated responses may occasionally contain inaccuracies or incomplete information**.
>
> For authoritative information, **refer to the original textbook repository**.

---

# Problem Description

Machine Learning Systems courses cover a wide range of topics including:

- Distributed training
- Model serving
- Feature stores
- Embeddings
- Vector databases
- Monitoring
- Hardware acceleration
- ML infrastructure

Students often need to search hundreds of pages of technical material to locate specific concepts, definitions, and implementation details.

Traditional keyword search struggles when different terminology is used to describe similar concepts.

Large language models provide excellent explanations but may generate incorrect information when they do not have access to the original course material.

This project solves this problem by combining:

1. Document retrieval from the CS249r textbook
2. Hybrid search using vector similarity and BM25 keyword retrieval
3. LLM generation grounded only on retrieved textbook passages

The result is a study assistant that provides natural-language answers while reducing hallucination risk.

---

# Features

## Knowledge Base

- Downloads Harvard CS249r textbook source files
- Supports Quarto (`.qmd`) and Markdown (`.md`) documents
- Processes textbook content into searchable chunks
- Preserves document metadata and source references

## Retrieval System

Hybrid retrieval pipeline combining:

- Vector similarity search for semantic understanding
- BM25 retrieval for exact keyword matching
- Weighted score fusion for final ranking

The retriever supports both:

- `text` document schema
- legacy `content` document schema

## RAG Answer Generation

The assistant:

- Retrieves relevant textbook sections
- Builds grounded context
- Generates answers using an LLM
- Returns source sections used for the response

## Interfaces

The application provides:

- Command-line interface
- Flask REST API
- Streamlit web interface

## Evaluation

Includes:

- Retrieval evaluation
- Hit Rate
- Mean Reciprocal Rank (MRR)
- LLM-as-a-Judge answer evaluation

## Monitoring

Designed to support:

- Conversation logging
- User feedback collection
- Performance monitoring dashboards

---

# Target Users

The primary users are:

- Students studying Harvard CS249r Machine Learning Systems
- Engineers learning ML infrastructure
- Developers interested in:
  - TinyML
  - Edge AI
  - Model optimisation
  - ML compiler systems
  - Production machine learning

---

# Architecture

```
                    User Question

                         |
                         v

              +--------------------+
              | Query Processing   |
              +--------------------+

                         |
                         v

              +--------------------+
              | Hybrid Retrieval   |
              |                    |
              | Vector Search      |
              | BM25 Search        |
              +--------------------+

                         |
                         v

              +--------------------+
              | Retrieved Chunks   |
              +--------------------+

                         |
                         v

              +--------------------+
              | LLM Generation     |
              | Groq / OpenAI API  |
              +--------------------+

                         |
                         v

              +--------------------+
              | Grounded Answer    |
              +--------------------+

                    /          \

                   /            \

                  v              v

          PostgreSQL        User Feedback

                  |
                  v

             Grafana Dashboard
```

---

# LLM Zoomcamp Final Project Requirements

| Requirement | Implementation |
|---|---|
| Unique dataset and ingestion | Custom ingestion pipeline processes Harvard CS249r `.qmd` and `.md` textbook sources |
| Retrieval system | Hybrid vector + BM25 retrieval over textbook chunks |
| LLM integration | RAG pipeline using Groq Llama models and OpenAI-compatible APIs |
| Evaluation strategy | Retrieval metrics and LLM-as-a-Judge evaluation |
| Monitoring | PostgreSQL logging architecture with Grafana dashboard support |

---

# Project Structure

```
ml-sys-book$ tree -L 2
.
├── cli.py
├── data
│   ├── ground_truth_retrieval.csv
│   ├── processed
│   ├── rag_evaluation_results.csv
│   ├── raw
│   └── retrieval_tuning_results.csv
├── docker-compose.yml
├── Dockerfile
├── evaluation
│   ├── evaluate_rag.py
│   ├── evaluate_retrieval.py
│   └── generate_ground_truth.py
├── grafana
│   ├── dashboard.json
│   └── init.py
├── main.py
├── ml_sys_book.egg-info
│   ├── dependency_links.txt
│   ├── PKG-INFO
│   ├── requires.txt
│   ├── SOURCES.txt
│   └── top_level.txt
├── notebook.ipynb
├── __pycache__
│   ├── cli.cpython-313.pyc
│   └── test_cli.cpython-313-pytest-9.1.1.pyc
├── pyproject.toml
├── README.md
├── study_assistant
│   ├── app.py
│   ├── config.py
│   ├── db_prep.py
│   ├── db.py
│   ├── ingest.py
│   ├── __init__.py
│   ├── minsearch.py
│   ├── prompts.py
│   ├── __pycache__
│   ├── rag.py
│   └── templates
├── test.py
└── uv.lock

11 directories, 33 files

```

---

# Installation

## Clone Project

```bash
git clone https://github.com/AK-RK7/ml-sys-book.git

cd ml-sys-book
```

## Install Dependencies

```bash
uv sync
```

## Download CS249r Textbook Source

```bash
mkdir -p data/raw

git clone https://github.com/harvard-edge/cs249r_book data/raw/cs249r_book

```

---

# Build Knowledge Base

Run ingestion:

```bash
uv run python -m study_assistant.ingest
```

This command:

- Parses the Quarto (.qmd) and Markdown (.md) textbook files
- Splits the textbook into searchable chunks
- Builds the in-memory retrieval dataset under data/processed/

---

# Running the Application

## Start the Flask API

```bash
uv run python study_assistant/app.py

## REST API

Start server:

```bash
uv run python study_assistant/app.py
```

Example request:

```bash
 curl -X POST http://localhost:5000/question \
-H "Content-Type: application/json" \
-d '{
    "question":"What is retrieval augmented generation?"
}
```

Example response:

```json
{
  "answer": "Retrieval-Augmented Generation (RAG) is a type of architecture that depends heavily on the quality of the retrieved context. It is described in the section \"Robust AI\" (vol2/robust_ai/robust_ai.qmd) as follows:\n\n\"In Retrieval-Augmented Generation (RAG) architectures (@sec-inference-scale), robustness depends heavily on the quality of the retrieved context. **Retrieval Noise**, the injection of irrelevant or conflicting documents into the prompt, can distract the model, causing it to ignore its internal parametric knowledge and propagate errors from the context.\"\n\nRAG architectures use retrieval mechanisms to fetch relevant context, which is then used to augment the generation process. The quality of the retrieved context is crucial for the robustness of RAG deployments.",
  "conversation_id": "c331cf92-07d6-449f-9e1b-48a784393a51",
  "model": "llama-3.1-8b-instant",
  "question": "What is retrieval augmented generation?",
  "response_time": 1.6115777492523193,
  "sources": [
    "vol1/backmatter/glossary/glossary.qmd",
    "vol1/data_engineering/data_engineering.qmd",
    "vol1/data_selection/data_selection.qmd",
    "vol1/model_serving/model_serving.qmd",
    "vol1/nn_architectures/nn_architectures.qmd",
    "vol2/data_storage/data_storage.qmd",
    "vol2/ops_scale/ops_scale.qmd",
    "vol2/robust_ai/robust_ai.qmd",
    "vol3/OUTLINE.md"
  ]
}
```

---

# Evaluation

The project contains two evaluation pipelines.

---

## 1. Retrieval Evaluation

Hybrid retrieval combines TF-IDF lexical similarity, SentenceTransformer semantic similarity, and BM25 keyword search. The final ranking uses weighted score fusion and down-weights low-information sections such as glossaries and appendices.

The retrieval benchmark uses questions generated from textbook chunks.

Metrics:

- Hit Rate
- Mean Reciprocal Rank (MRR)

Run:

```bash
uv run python evaluation/generate_ground_truth.py

uv run python evaluation/evaluate_retrieval.py

Best results:
    text_boost  semantic_weight  hit_rate       mrr
0         0.25              0.6  0.827982  0.689029
4         0.30              0.7  0.827982  0.688647
7         0.35              0.7  0.821101  0.688341
3         0.30              0.6  0.821101  0.688341
11        0.40              0.8  0.821101  0.688341
8         0.35              0.8  0.823394  0.687844
5         0.30              0.8  0.832569  0.686774
10        0.40              0.7  0.811927  0.686315
6         0.35              0.6  0.809633  0.684709
9         0.40              0.6  0.811927  0.684098
```
---

## 2. RAG Answer Evaluation

Generated answers are evaluated using an LLM-as-a-Judge.

The evaluator classifies responses as:

- RELEVANT
- PARTLY_RELEVANT
- NON_RELEVANT

Run:

```bash
uv run python evaluation/evaluate_rag.py


Relevance distribution:
relevance
RELEVANT           0.500
PARTLY_RELEVANT    0.325
NON_RELEVANT       0.170
UNKNOWN            0.005
Name: proportion, dtype: float64

Saved: data/rag_evaluation_results.csv
```
---

# Retrieval Improvements

The current retrieval system includes:

## Hybrid Retrieval

Combines:

- Semantic vector retrieval
- BM25 keyword matching

## Score Fusion

Retrieval results are combined using weighted scoring.

## Noise Reduction

Low-value sections such as:

- Frontmatter
- Glossary
- Appendices

receive reduced ranking weight.

---

# Current Limitations

- Single textbook knowledge base
- In-memory retrieval index
- No authentication system
- Index rebuild required after changing source documents
- Retrieval parameters require manual tuning
- Answers depend on retrieved textbook context
- No conversation memory

---

# Future Improvements

Planned improvements:

## Retrieval

- Cross-encoder reranking
- Improved chunking strategies
- Automatic retrieval parameter optimisation
- Query rewriting using LLMs

## Application

- Conversation history
- User accounts
- Personal study sessions
- Better feedback collection

## Infrastructure

- PostgreSQL conversation logging
- Grafana monitoring dashboard
- Docker deployment
- Cloud deployment

---

# Technology Stack

```
| Component       | Technology                            |
| --------------- | ------------------------------------- |
| Language        | Python                                |
| Package Manager | uv                                    |
| Retrieval       | TF-IDF + Sentence Transformers + BM25 |
| Embeddings      | sentence-transformers                 |
| LLM             | Groq (Llama 3.1 8B)                   |
| API             | Flask                                 |
| Evaluation      | LLM-as-a-Judge                        |
| Data            | Harvard CS249r textbook               |
```
---

# Conclusion

Harvard MLSys Study Assistant demonstrates how Retrieval-Augmented Generation can transform large technical textbooks into interactive learning systems.

By grounding LLM responses in retrieved textbook passages, the system provides a more reliable and transparent learning experience compared with standalone language models.

## License

This project is released for educational purposes as part of the LLM Zoomcamp Final Project.

The Harvard CS249r textbook content is not included in this repository. Users should obtain the source material from the official Harvard repository, which is subject to its own licence and copyright.
