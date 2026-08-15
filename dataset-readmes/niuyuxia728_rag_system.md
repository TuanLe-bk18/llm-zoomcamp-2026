# RAG Evaluation Demo

## Overview

This project demonstrates a Retrieval-Augmented Generation (RAG) application with an evaluation workflow. It includes knowledge base generation, retrieval evaluation, user feedback collection, and LLM-based evaluation, all presented through a Streamlit web application.

## Tech Stack

* **minsearch** – Text-based retrieval engine for the RAG pipeline
* **PostgreSQL** – Stores RAG interactions and evaluation results
* **Streamlit** – Web application for chatbot interaction and evaluation history
* **OpenAI LLM** – Generates ground truth data and performs automatic response evaluation
* **Grafana** – Dashboard for monitoring RAG usage and evaluation metrics

---

## Project Workflow

### 1. Build the Knowledge Base

A small knowledge base containing **30 records** is generated with python and LLM and stored in:

```
ground-truth-retrieval.csv
```

These records serve as the reference documents for retrieval.

---

### 2. Generate and Evaluate Ground Truth

Using the knowledge base, an LLM generates:

* User questions
* Ground truth answers

Two retrieval approaches are evaluated:

* **Text index (minsearch)**
* **Vector index**

Because the dataset is intentionally small, the **text index consistently produces better retrieval performance** than the vector index. Therefore, the final RAG system is built using the text index.

---

### 3. RAG Pipeline

For each user question:

1. Retrieve the most relevant document(s) using **minsearch**.
2. Provide the retrieved context to the LLM.
3. Generate the final response.
4. Store the interaction in PostgreSQL.

Each record includes information such as:

* User question
* RAG answer
* Timestamp

---

### 4. Evaluation Ad-hoc

The application supports two types of evaluation.

#### User Evaluation

Users can manually rate each response, for example:

* RELEVANT
* PARTLY_RELEVANT
* NON_RELEVANT

#### LLM Evaluation

An LLM automatically evaluates each RAG response by comparing it with the generated ground truth and provides:

* Evaluation label
* Explanation for the evaluation

Both evaluation results are stored in PostgreSQL.

---

### 5. Streamlit Application

The Streamlit application provides two main features.

#### Chatbot

Users can:

* Ask questions
* Receive RAG-generated responses
* Submit manual evaluations

#### Evaluation History

Displays all previous interactions, including:

* Question
* RAG response
* User evaluation
* LLM evaluation
* LLM explanation

This allows comparison between human judgments and automated LLM assessments.

### 6. Monitoring Dashboard

A simple Grafana dashboard is built on top of the PostgreSQL database to monitor the RAG system.

The dashboard provides an overview of:

Total number of RAG requests
Tocken usage and cost
User evaluation and LLM evaluation distribution


This provides a centralized view of system usage and response quality, making it easier to monitor the performance of the RAG application.

### 7. Docker Containerization

The application is fully containerized using Docker Compose, allowing the entire RAG system to be started with a single command.

The Docker environment includes:

* **Streamlit** for the web application.
* **PostgreSQL** for storing application data, feedback, and monitoring metrics.
* **Grafana** for visualizing system usage and evaluation dashboards.

Docker Compose automatically creates a shared network between the services and manages persistent volumes so that PostgreSQL and Grafana data are retained across container restarts.

To build and start the application:

```bash
docker compose up --build
```

To run the services in the background:

```bash
docker compose up --build -d
```

The application is available at:

* **Streamlit:** http://localhost:8501
* **Grafana:** http://localhost:3000

Containerization provides a reproducible development environment and serves as the foundation for future cloud deployment using Infrastructure as Code tools such as Terraform.


---

## Project Architecture

```
Knowledge Base (30 records)
            │
            ▼
ground-truth-retrieval.csv
            │
            ▼
Ground Truth Generation (LLM)
            │
            ▼
Text Index (minsearch)
            │
            ▼
      RAG Pipeline
            │
            ▼
      PostgreSQL Database
     ├── RAG Results
     └── Evaluation Results
            │
            ▼
      Streamlit Web App
     ├── Chatbot
     └── Evaluation History
```

---

## Database

The PostgreSQL database stores:

### `rag_results`

Stores each chatbot interaction.

Example fields:

* id
* question
* answer
* prompt_tockens
* created_at

### `rag_feedback`

Stores evaluation information.

Example fields:

* question_id
* user_evaluation
* llm_evaluation
* llm_explanation
* created_at

---

## Purpose

This project demonstrates an end-to-end RAG workflow, including:

* Knowledge base creation
* Retrieval evaluation
* RAG implementation
* Human feedback collection
* Automated LLM evaluation
* Result visualization through a web interface

