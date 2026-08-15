# 🩺 MedRAG AI: An Intelligent Research Assistant for Medical AI Papers

> **Final Project for DataTalksClub LLM Zoomcamp 2026**

MedRAG AI is an end-to-end **Retrieval-Augmented Generation (RAG)** application that enables researchers, students, and healthcare professionals to interact with a curated collection of Medical AI research papers using natural language.

Instead of manually searching through hundreds of pages of scientific literature, users can ask questions and receive AI-generated answers grounded in relevant research papers retrieved from a semantic vector database.

---

# 📖 Overview

MedRAG AI combines modern **Large Language Models (LLMs)** with semantic retrieval techniques to produce reliable, evidence-based answers from scientific publications.

The system integrates:

- 📚 ChromaDB for semantic document retrieval
- 🤖 Google Gemini 2.5 Flash for answer generation
- 🔍 Sentence Transformers for embedding generation
- ⚡ FastAPI as the backend REST API
- 🎨 Streamlit as the interactive web interface
- 🐳 Docker for containerized deployment

The project demonstrates a complete Retrieval-Augmented Generation (RAG) workflow, from PDF ingestion and indexing to semantic retrieval, answer generation, evaluation, and deployment.

---

# ✨ Features

- 📄 PDF document ingestion
- 📑 Automatic text extraction
- ✂️ Intelligent document chunking
- 🧠 Sentence Transformer embeddings
- 📚 ChromaDB vector database
- 🔍 Semantic similarity search
- 🔄 Hybrid retrieval support (Semantic + BM25)
- 🤖 Google Gemini integration
- 📄 Source citation with retrieved document chunks
- ⚡ FastAPI REST API
- 🎨 Streamlit web application
- 📊 Query logging dashboard
- 📥 Download generated answers
- 📈 Evaluation pipeline
- 🐳 Docker & Docker Compose deployment

---

# 🏗️ System Architecture

```text
                User
                  │
                  ▼
         Streamlit Web Interface
                  │
                  ▼
            FastAPI Backend
                  │
                  ▼
      Hybrid Document Retrieval
     (Semantic + BM25 Search)
                  │
                  ▼
             ChromaDB
                  │
                  ▼
       Relevant Document Chunks
                  │
                  ▼
         Prompt Construction
                  │
                  ▼
      Google Gemini 2.5 Flash
                  │
                  ▼
      AI-generated Answer + Sources
```

---

# 📂 Project Structure

```text
LLM-Zoomcamp2026-Final-Project/

├── app/
│   ├── main.py
│   ├── service.py
│   ├── schemas.py
│   ├── config.py
│   └── logger.py
│
├── rag/
│   ├── embedding.py
│   ├── retriever.py
│   ├── hybrid_retriever.py
│   ├── bm25.py
│   ├── prompt.py
│   ├── llm.py
│   └── vector_store.py
│
├── scripts/
│
├── ui/
│   ├── app.py
│   └── dashboard.py
│
├── evaluation/
│
├── data/
│
├── chroma_db/
│
├── logs/
│
├── docs/
│   ├── METHOD_AND_PROCEDURE.md
│   └── images/
│
├── Dockerfile.api
├── Dockerfile.ui
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# 🚀 Technology Stack

| Category | Technology |
|-----------|------------|
| Language | Python 3.12 |
| LLM | Google Gemini 2.5 Flash |
| Backend | FastAPI |
| Frontend | Streamlit |
| Embeddings | Sentence Transformers |
| Vector Database | ChromaDB |
| Hybrid Search | BM25 + Semantic Retrieval |
| PDF Processing | PyMuPDF |
| Machine Learning | PyTorch |
| Data Processing | Pandas, NumPy |
| Validation | Pydantic |
| Deployment | Docker & Docker Compose |

---

# ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/jcdumlao14/LLM-Zoomcamp2026-Final-Project.git

cd LLM-Zoomcamp2026-Final-Project
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Variables

Create a `.env` file.

```text
GEMINI_API_KEY=YOUR_GEMINI_API_KEY

MODEL_NAME=gemini-2.5-flash

CHROMA_PATH=chroma_db

API_URL=http://127.0.0.1:8000/ask
```

---

# ▶️ Running the Application

## Start the FastAPI backend

```bash
uvicorn app.main:app --reload
```

API documentation:

```
http://127.0.0.1:8000/docs
```

---

## Start the Streamlit application

```bash
streamlit run ui/app.py
```

Open:

```
http://localhost:8501
```

---

## Start the Dashboard

```bash
streamlit run ui/dashboard.py
```

---

## Docker Deployment

Build the application:

```bash
docker compose build
```

Run the containers:

```bash
docker compose up -d
```

Stop containers:

```bash
docker compose down
```

---

# 📊 Evaluation

Run the evaluation pipeline:

```bash
python -m evaluation.evaluate
```

The evaluation records:

- Response time
- Number of retrieved sources
- Average retrieval distance
- Answer length
- Generated responses

Logs are stored in:

```
logs/query_logs.csv
```

---

# 📡 API Endpoint

## POST `/ask`

### Request

```json
{
  "question": "What is deep learning in chest X-ray analysis?"
}
```

### Response

```json
{
  "question": "...",
  "answer": "...",
  "sources": [
    {
      "filename": "...",
      "chunk_id": 1,
      "distance": 0.54,
      "text": "..."
    }
  ]
}
```

---

# 📷 Application Screenshots

## 🏠 Streamlit Home Page

![](docs/images/home.png)

---

## 🤖 AI Generated Answer

![](docs/images/answer.png)

---

## 📚 Retrieved Sources

![](docs/images/sources.png)

---

## 📊 Dashboard

![](docs/images/dashboard.png)

---

## 🐳 Docker Containers

![](docs/images/docker_ps.png)

---

## 🐳 Docker Desktop

![](docs/images/docker_desktop.png)

---

# 🚧 Project Status

| Component | Status |
|-----------|--------|
| PDF Ingestion | ✅ Completed |
| Document Chunking | ✅ Completed |
| Embedding Generation | ✅ Completed |
| ChromaDB Indexing | ✅ Completed |
| Semantic Retrieval | ✅ Completed |
| Hybrid Retrieval | ✅ Completed |
| Prompt Engineering | ✅ Completed |
| Gemini Integration | ✅ Completed |
| FastAPI Backend | ✅ Completed |
| Streamlit UI | ✅ Completed |
| Dashboard | ✅ Completed |
| Query Logging | ✅ Completed |
| Evaluation Pipeline | ✅ Completed |
| Docker Deployment | ✅ Completed |
| Documentation | ✅ Completed |

---

# 🔮 Future Improvements

- Cross-encoder reranking
- Medical image question answering
- Multi-turn conversational memory
- User authentication
- Cloud deployment (Render/Azure/GCP)
- Feedback collection
- Advanced retrieval evaluation metrics
- Citation highlighting
- Streaming responses

---

# 📚 Documentation

Additional project documentation is available in the `docs/` directory.

| Document | Description |
|----------|-------------|
| `docs/METHOD_AND_PROCEDURE.md` | Development methodology and implementation process |
| `docs/API.md` | FastAPI endpoints and request/response examples |
| `docs/INSTALLATION.md` | Installation and setup guide |
| `docs/ARCHITECTURE.md` | System architecture and workflow |
| `docs/EVALUATION.md` | Evaluation methodology and performance metrics |

---

# 👩‍💻 Author

**Jocelyn Dumlao**

Independent Data Scientist | Machine Learning Engineer

Specializing in:

- Medical AI
- Machine Learning
- Natural Language Processing
- Large Language Models (LLMs)
- Retrieval-Augmented Generation (RAG)

GitHub:

https://github.com/jcdumlao14

---

# 🙏 Acknowledgements

This project was developed as the **Final Project for the DataTalksClub LLM Zoomcamp 2026**.

Special thanks to:

- Alexey Grigorev - Founder of DataTalks.Club
- Google Gemini
- ChromaDB
- Hugging Face
- Streamlit
- FastAPI
- Sentence Transformers

---

# 📄 License

This project is licensed under the **MIT License**.
