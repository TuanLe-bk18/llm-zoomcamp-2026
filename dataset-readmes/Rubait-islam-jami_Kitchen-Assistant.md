# 🍽️ Kitchen Assistant – RAG Powered Recipe Recommendation System

## Overview
<p align="center">
  <img src="images/first impression.png" width="100%">
</p>

<h1 align="center">🍳 Kitchen Assistant RAG System</h1>

<p align="center">
Kitchen Assistant is an end-to-end Retrieval-Augmented Generation (RAG) application developed as the final project for the DataTalks.Club LLM Zoomcamp.

</p>

The application answers users' cooking and recipe-related questions by retrieving relevant recipes from a recipe dataset and generating responses using Google's Gemini LLM.

It also logs every interaction, collects user feedback, and visualizes usage statistics in Grafana.

---

# Problem Description

Finding suitable recipes based on ingredients, dietary preferences, or natural language questions can be challenging because traditional keyword search often returns irrelevant or incomplete results.

This project addresses that problem by using a Retrieval-Augmented Generation (RAG) pipeline. Instead of querying a Large Language Model (LLM) directly, the system first retrieves the most relevant recipes from a recipe knowledge base, improves retrieval through query rewriting and document re-ranking, and then provides the retrieved context to the LLM.

This approach reduces hallucinations and produces more accurate, relevant, and context-aware recipe recommendations.

---

# Features

- Recipe Retrieval (RAG)
- Gemini LLM Integration
- Flask REST API
- SQLite Conversation Logging
- User Feedback Collection
- Grafana Monitoring Dashboard
- Docker & Docker Compose Support
- Streamlit User Interface

---
## System Architecture

```text
        ┌────────────────────┐
        │   User Question    │
        └─────────┬──────────┘
                  ▼
        ┌────────────────────┐
        │ Query Rewriting    │
        └─────────┬──────────┘
                  ▼
        ┌────────────────────┐
        │ Recipe Retrieval   │
        │   (MinSearch)      │
        └─────────┬──────────┘
                  ▼
        ┌────────────────────┐
        │ Document Re-ranking│
        └─────────┬──────────┘
                  ▼
        ┌────────────────────┐
        │ Prompt Construction│
        └─────────┬──────────┘
                  ▼
        ┌────────────────────┐
        │ Google Gemini LLM  │
        └─────────┬──────────┘
                  ▼
        ┌────────────────────┐
        │ Generated Answer   │
        └─────────┬──────────┘
                  ▼
        ┌────────────────────┐
        │ SQLite Logging     │
        └─────────┬──────────┘
                  ▼
        ┌────────────────────┐
        │ Grafana Dashboard  │
        └────────────────────┘
```

# Tech Stack
```

| Component         | Technology        | Purpose                     |
| ----------------- | ----------------- | --------------------------- |
| Language          | Python            | Core application            |
| Backend           | Flask             | Web interface               |
| LLM               | Google Gemini API | Answer generation           |
| Retrieval         | MinSearch         | Recipe retrieval            |
| Database          | SQLite            | Conversation logging        |
| Data Processing   | Pandas            | Dataset preprocessing       |
| Monitoring        | Grafana           | Performance monitoring      |
| Containerization  | Docker            | Application container       |
| Orchestration     | Docker Compose    | Multi-container management  |
```
## Dataset

This project uses the **RAW Recipes** dataset from Kaggle. The dataset was preprocessed into `recipes_documents.csv`, where each recipe is converted into a searchable document and indexed using **MinSearch** for the RAG pipeline.

## Evaluation

The retrieval pipeline was evaluated using different **Top-K** values to determine the best retrieval configuration. Based on the results, **Top-10** was selected for the final RAG pipeline.

### Retrieval Evaluation
```
- Top-3 Hit Rate: **5%**
- Top-5 Hit Rate: **5%**
- Top-10 Hit Rate: **20%** *(Selected for the final system)*
```

### LLM Evaluation

Two evaluation prompts were tested using **Gemini 3.1 Flash Lite** as the LLM Judge.
```
- **Judge Prompt V1**
  - Accuracy: **85%**

- **Judge Prompt V2**
  - Accuracy: **100%**
  - **Selected as the final evaluation prompt**
```
The improved Judge Prompt V2 produced more consistent evaluation results and was selected for the final evaluation pipeline.
## Monitoring

The application records every user interaction in a **SQLite** database, including the user query, generated response, token usage, selected model, and API cost.

A **Grafana** dashboard is connected to the database to monitor the application's performance and usage in real time.

The dashboard includes:

- Total Conversations
- Average Cost
- Total Tokens Used
- Questions Over Time
- Model Usage Distribution

### Monitoring Dashboard

<p align="center">
  <img src="images/grafana-dashboard.png" width="900">
</p>

## Project Structure

```text
Kitchen-Assistant/
│
├── app.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── Pipfile
├── Pipfile.lock
├── README.md
├── kitchen.db
│
├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_minsearch.ipynb
│   ├── 03_rag.ipynb
│   ├── 03_evaluating_rag.ipynb
│   └── 04_evaluation.ipynb
│
├── src/
│   ├── db.py
│   ├── evaluate.py
│   ├── ingest.py
│   ├── llm.py
│   ├── monitor.py
│   ├── query_rewriter.py
│   ├── rag.py
│   └── reranker.py
│
├── test.py
├── test_evaluate.py
├── test_requests.py
│
└── images/
    ├── >>>>
    └── >>>>

```
## User Interface

![UI]<p align="center">
  <img src="images/example.png" width="1000">
</p>

## Installation & Usage

### 1. Clone the Repository

```bash
git clone https://github.com/Rubait-islam-jami/Kitchen-Assistant.git
cd Kitchen-Assistant
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

### 4. Run the Application

```bash
python app.py
```

The application will be available at:

```text
http://127.0.0.1:5000
```

### Run with Docker

```bash
docker compose up --build
```

The Docker deployment also exposes the application on:

```text
http://localhost:5000
```
## Future Improvements

The current system can be extended with several additional features:

- Implement hybrid search by combining keyword and vector search.
- Build a user-friendly web interface using Streamlit.
- Improve document reranking using advanced reranking models.
- Add user authentication and personalized recipe recommendations.
- Deploy the application on a cloud platform for public access.
## Acknowledgements
```
This project was developed as the final project for the **LLM Zoomcamp** organized by **DataTalks.Club**.

The application uses:

- Google Gemini API for answer generation
- MinSearch for document retrieval
- Grafana for monitoring
- SQLite for logging conversations
```