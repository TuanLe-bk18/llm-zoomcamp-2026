# 🤖 ROS 2 Assistant

A RAG-based question-answering assistant for ROS 2 documentation, built as the final project for the [LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp) course.

---

## 📋 Problem Description

ROS 2 (Robot Operating System 2) has extensive documentation spread across hundreds of pages, making it difficult for beginners and intermediate users to quickly find answers to specific questions.

This project builds an end-to-end RAG (Retrieval-Augmented Generation) application that allows users to ask natural language questions about ROS 2 and receive accurate, context-grounded answers based on the official documentation.

**Example questions the assistant can answer:**
- How do I create a ROS 2 node in Python?
- What is the difference between a topic and a service?
- How do I use ros2 launch to start multiple nodes?
- What is the DDS middleware in ROS 2?

---

## 🏗️ Architecture
User Question
→ Embedding (all-MiniLM-L6-v2, local)
→ Hybrid Search in PGVector (vector + keyword, RRF fusion)
→ Top-5 relevant documentation chunks
→ LLM prompt (Groq / llama-3.3-70b-versatile)
→ Answer with sources
→ Saved to PostgreSQL for monitoring

**Stack:**
- **Knowledge base:** PostgreSQL + PGVector (384-dim embeddings)
- **Embedding model:** `all-MiniLM-L6-v2` (sentence-transformers, runs locally)
- **LLM:** `llama-3.3-70b-versatile` via Groq API
- **Retrieval:** Hybrid search (vector + keyword) with Reciprocal Rank Fusion
- **UI:** Streamlit
- **Monitoring:** Grafana dashboard
- **Containerization:** Docker Compose

---

## 📊 Dataset

The knowledge base is built from the official ROS 2 Jazzy documentation scraped from [docs.ros.org](https://docs.ros.org/en/jazzy/index.html).

- **298 pages** scraped
- **4,399 chunks** indexed in PGVector
- The scraping script is included and can be re-run to update the knowledge base

---

## 🔍 Retrieval Evaluation

Three retrieval methods were evaluated using LLM-as-a-Judge (scored 0-20):

| Method | Avg Score | Notes |
|--------|-----------|-------|
| Hybrid (vector + keyword) | **19.2/20** | Best overall, consistent across all question types |
| Keyword (BM25-style) | 19.2/20 | Strong on exact terminology |
| Vector (semantic) | 18.6/20 | Weaker on specific/niche questions |

**Winner: Hybrid search** — used as the default method in the app.

---

## 🤖 LLM Evaluation

Two system prompts were compared using LLM-as-a-Judge:

| Prompt | Style | Avg Score |
|--------|-------|-----------|
| Prompt A | Concise, strict context adherence | 18.8/20 |
| Prompt B | Detailed, beginner-friendly with step-by-step examples | 19.1/20 |

**Winner: Prompt B** — provides more practical, actionable answers for ROS 2 beginners.

---

## 🚀 Running the Project

### Prerequisites
- Docker and Docker Compose
- Groq API key (free at [console.groq.com](https://console.groq.com))

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/ros2-assistant.git
cd ros2-assistant
```

### 2. Configure environment variables
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 3. Start the infrastructure
```bash
docker compose up -d postgres grafana
```

### 4. Initialize the database
```bash
python data/init_db.py
```

### 5. Run the ingestion pipeline
```bash
# Scrape ROS 2 documentation (takes ~8 minutes)
python data/scraper.py

# Generate embeddings and index into PGVector (takes ~3 minutes)
python data/ingest.py
```

### 6. Start the app
```bash
docker compose up -d app
```

### 7. Access the services
- **ROS 2 Assistant:** http://localhost:8501
- **Grafana Dashboard:** http://localhost:3000 (admin/admin)

---

## 📁 Project Structure

```
ros2-assistant/
├── app/
│   └── main.py              # Streamlit UI
├── data/
│   ├── init_db.py           # Database initialization
│   ├── scraper.py           # ROS 2 docs scraper
│   └── ingest.py            # Embedding generation and indexing
├── rag/
│   ├── retrieval.py         # Vector, keyword and hybrid search
│   └── llm.py               # LLM integration (Groq)
├── notebooks/
│   └── evaluation.py        # Retrieval and LLM evaluation
├── monitoring/
│   └── grafana/
│       └── provisioning/    # Grafana dashboard config
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 📈 Monitoring

The Grafana dashboard at http://localhost:3000 includes:

1. **Total Conversations** — total number of questions asked
2. **Avg Response Time** — average response time in seconds
3. **Positive Feedback %** — percentage of thumbs up ratings
4. **Conversations Without Feedback** — unanswered feedback count
5. **Conversations Over Time** — usage timeline
6. **Retrieval Method Usage** — breakdown by search method
7. **Feedback Distribution** — positive vs negative vs no feedback
8. **Response Time Over Time** — latency trends
9. **Recent Conversations** — latest questions and answers table

---

## 🔑 Environment Variables

Create a `.env` file based on `.env.example`:

```env
POSTGRES_DB=ros2assistant
POSTGRES_USER=ros2user
POSTGRES_PASSWORD=ros2pass
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

GROQ_API_KEY=your_api_key_here

LLM_MODEL=llama-3.3-70b-versatile
LLM_MODEL_FAST=llama-3.3-70b-versatile
```