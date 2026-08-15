# Asylum Seekers Assistant

> An AI-powered Retrieval-Augmented Generation (RAG) application that helps asylum seekers understand the **Dublin Regulation** by answering questions using official documentation.

**Status:** ✅ Complete

---

# Overview

Understanding asylum procedures can be difficult because legal documents are often lengthy and written in complex language.

The **Asylum Seekers Assistant** uses Artificial Intelligence and Retrieval-Augmented Generation (RAG) to provide clear, simple answers based only on official Dublin Regulation documents.

Instead of relying solely on a language model, the application first searches a vector database for the most relevant document sections before generating an answer. This improves accuracy and reduces hallucinations.

---

# Features

## 🤖 AI Question Answering

Ask natural language questions about the Dublin Regulation and receive easy-to-understand answers.

Example questions:

- What is the Dublin Regulation?
- Which country is responsible for my asylum application?
- How long does the Dublin transfer process take?
- Can I appeal a transfer decision?

---

## 📚 Retrieval-Augmented Generation (RAG)

The application follows the RAG workflow:

1. User asks a question.
2. The question is converted into embeddings.
3. ChromaDB retrieves the most relevant document chunks.
4. The retrieved context is sent to OpenAI GPT-4.1-mini.
5. The model generates an answer using only the retrieved context.

---

## 🔍 Source References

Every generated answer includes the pages used from the official documents.

Example:

```
Answer:
The transfer procedure generally takes up to six months.

Sources:
Page 9
Page 11
```

---

## 🐳 Docker Containerization

The application is fully containerized using **Docker** and **Docker Compose**, allowing it to run consistently across different environments without requiring a local Python installation.

---

# System Architecture

```
                 User
                  │
                  │
                  ▼
         Streamlit Web Interface
                  │
                  ▼
            User Question
                  │
                  ▼
      Hugging Face Embeddings
                  │
                  ▼
             ChromaDB
       (Vector Similarity Search)
                  │
                  ▼
      Relevant Document Chunks
                  │
                  ▼
          OpenAI GPT-4.1-mini
                  │
                  ▼
          Generated Response
                  │
                  ▼
       Answer + Source Pages
```

---

# Technology Stack

| Category | Technology |
|----------|------------|
| Programming Language | Python 3.13 |
| User Interface | Streamlit |
| AI Framework | LangChain |
| Large Language Model | OpenAI GPT-4.1-mini |
| Embedding Model | BAAI/bge-small-en-v1.5 |
| Embedding Framework | Hugging Face Sentence Transformers |
| Vector Database | ChromaDB |
| Document Processing | PyPDF |
| Environment Variables | python-dotenv |
| Containerization | Docker |
| Container Orchestration | Docker Compose |

---

# Project Structure

```
Asylum-seekers-assistant/
│
├── app.py
├── rag.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .gitignore
├── README.md
├── .env.example
│
├── chroma_db/
│
├── data/
│
└── .venv/
```

---

# Installation (Local Development)

## Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/Asylum-seekers-assistant.git

cd Asylum-seekers-assistant
```

---

## Create a virtual environment

Windows

```powershell
python -m venv .venv
```

Activate

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## Install dependencies

```powershell
python -m pip install -r requirements.txt
```

---

## Configure environment variables

Create a `.env` file:

```
OPENAI_API_KEY=your_openai_api_key
```

---

## Run the application

```powershell
python -m streamlit run app.py
```

Open your browser:

```
http://localhost:8501
```

---

# Docker Deployment

This application can also be run entirely inside a Docker container.

## Build the Docker image

```bash
docker compose build
```

---

## Start the application

```bash
docker compose up
```

Open your browser:

```
http://localhost:8501
```

---

## Stop the application

```bash
docker compose down
```

---

# How the Application Works

## 1. Document Processing

The official Dublin Regulation documents are:

- Loaded from PDF files
- Split into smaller chunks
- Converted into embeddings using Hugging Face

---

## 2. Vector Storage

Embeddings are stored inside **ChromaDB**, allowing semantic search rather than simple keyword matching.

---

## 3. Question Retrieval

When a user asks a question:

```
Question
     │
     ▼
Embedding Generation
     │
     ▼
Similarity Search
     │
     ▼
Relevant Chunks
```

The three most relevant chunks are retrieved.

---

## 4. Answer Generation

The retrieved document context is sent to GPT-4.1-mini together with the user's question.

The model is instructed to answer **only using the retrieved context**.

If the answer is not contained in the documents, the assistant responds:

> "I couldn't find that information in the provided documents."

---

# Example

### Question

```
What is the Dublin Regulation?
```

### Answer

```
The Dublin Regulation determines which European country is responsible for examining an asylum application.

Sources:
Page 3
Page 5
```

---

# Skills Demonstrated

This project demonstrates experience with:

- Retrieval-Augmented Generation (RAG)
- Large Language Models (OpenAI GPT)
- Semantic Search
- Vector Databases
- LangChain
- Hugging Face Embeddings
- Streamlit
- Docker
- Docker Compose
- Environment Variable Management
- Git & GitHub

---

# Future Improvements

Possible future enhancements include:

- 🌍 Multilingual support
- 💬 Conversation memory
- 📄 Support for multiple legal documents
- 🔎 Highlight retrieved document passages
- ☁️ Cloud deployment (Azure / AWS / GCP)
- 🔐 User authentication
- 📊 Admin dashboard
- 📝 Chat history export

---


# Author

**Yohana**

AI & Machine Learning Developer

GitHub: https://github.com/YohanaTeweldemedhin