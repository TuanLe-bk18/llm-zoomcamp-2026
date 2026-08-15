# 💳 PaymentOps AI

**An end-to-end Retrieval-Augmented Generation (RAG) assistant for Digital Payments & Mobile Money Operations**

# 📖 Overview

PaymentOps AI is a production-oriented Retrieval-Augmented Generation (RAG) application designed to assist Payment Operations teams in answering operational questions related to digital payments and mobile money.

The application combines Hybrid Search, Large Language Models, Monitoring, Evaluation, Analytics, and Docker deployment into a modular architecture inspired by modern enterprise AI systems.

To ensure that the project is fully open source, **all operational documents included in the knowledge base are synthetically generated using a Large Language Model (LLM)**. No confidential business documentation or proprietary payment procedures have been used.

This repository demonstrates how to build a production-ready RAG application while respecting privacy and intellectual property constraints.


# ✨ Features

* 🔎 Hybrid Retrieval (Keyword Search + Vector Search)
* 🤖 RAG Assistant powered by Groq (Llama 3.3 70B)
* 📚 AI-generated synthetic knowledge base
* 📈 Real-time monitoring with Logfire
* 🔄 Monitoring pipeline using dlt
* 🦆 DuckDB analytical storage
* 📊 Interactive Streamlit Monitoring Dashboard
* 🎯 Built-in RAG Evaluation framework
* 🐳 Docker deployment
* ⚙️ Modular and production-ready architecture

# 🏗️ System Architecture
```text
                         User
                           │
                           ▼
                 Streamlit Chat Interface
                           │
                           ▼
                 PaymentOps Assistant
                           │
          ┌────────────────┴────────────────┐
          ▼                                 ▼
    Keyword Search                   Vector Search
          └────────────────┬────────────────┘
                           ▼
                    Hybrid Retrieval
                           ▼
                  Context Construction
                           ▼
                 Groq Llama 3.3 70B
                           ▼
                   Generated Answer
                           │
          ┌────────────────┴────────────────┐
          ▼                                 ▼
     Streamlit UI                      Logfire
                                              │
                                              ▼
                                        dlt Pipeline
                                              │
                                              ▼
                                           DuckDB
                                              │
                                              ▼
                                  Monitoring Dashboard
```
---

# 🛠️ Tech Stack

| Category       | Technology           |
| -------------- | -------------------- |
| Language       | Python 3.12          |
| Web Framework  | Streamlit            |
| LLM            | Groq - Llama 3.3 70B |
| Retrieval      | Hybrid Search        |
| Keyword Search | BM25                 |
| Vector Search  | ONNX Embeddings      |
| Analytics      | DuckDB               |
| Monitoring     | Logfire              |
| ETL Pipeline   | dlt                  |
| Visualization  | Plotly               |
| Deployment     | Docker               |

---

# 📚 Synthetic Knowledge Base

The knowledge base included in this repository is entirely **AI-generated**.

No confidential company documentation, customer data, or proprietary payment procedures have been used.

The documents simulate realistic Payment Operations topics such as:

* Wallet Creation
* Wallet Activation
* Wallet Suspension
* KYC Verification
* Transaction Failures
* P2P Transfers
* Payment FAQ
* Mobile Money Operations

This makes the entire project fully open source while preserving realistic enterprise scenarios.

---

# 📂 Project Structure

```text
paymentops-ai/

├── data/
│   ├── evaluation/
│   ├── knowledge_base/
│   └── processed/
│── image/
│
|__ models/
|
├── pages/
│   ├── 1_💬_Chat.py
│   ├── 2_📊_Monitoring.py
│   └── 3_🎯_Evaluation.py
│
├── src/
│   ├── config/
│   ├── dashboard/
│   ├── evaluation/
│   ├── monitoring/
│   ├── rag/
│   ├── retrieval/
│   |── ingestion/
|   └── generation/
│
├── streamlit_app.py
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

# 🤖 RAG Pipeline

The assistant follows the complete Retrieval-Augmented Generation workflow:

1. User submits a question.
2. Hybrid Retrieval searches the knowledge base.
3. Relevant documents are retrieved.
4. Context is assembled.
5. The prompt is sent to Groq Llama 3.3.
6. The assistant generates an answer.
7. Execution metrics are logged in Logfire.
8. Monitoring data is exported to DuckDB through dlt.

---

# 📈 Monitoring

Every interaction is automatically monitored.

Collected metrics include:

* User question
* Retrieved documents
* Model used
* Response latency
* Answer length
* Input tokens
* Output tokens

Monitoring data is visualized through the Streamlit dashboard.

---

# 🎯 Evaluation

The project includes a lightweight RAG evaluation framework.

Evaluation measures:

* Question quality
* Keyword coverage
* Average RAG score
* Retrieved documents
* Generated answers

This makes it easy to compare retrieval and prompting improvements over time.

---

# 📊 Monitoring Dashboard

The dashboard provides real-time insights including:

* Total requests
* Average latency
* Average answer length
* Request timeline
* Latency timeline
* Token consumption
* Most frequent user questions
* Most retrieved documents
* Model usage statistics

---

# 🐳 Docker

Build the project

```bash
docker compose build
```

Run the application

```bash
docker compose up
```

The application is available at:

```text
http://localhost:8501
```

---

# ⚙️ Local Installation

Clone the repository

```bash
git clone <repository-url>
cd paymentops-ai
```

Install dependencies

```bash
uv sync
```

Run the application

```bash
PYTHONPATH=. uv run streamlit run streamlit_app.py
```

---

# 📷 Screenshots

<table>
<tr>
<td align="center">
<b>Home Page</b><br>
<img src="image/homepage.png" width="300">
</td>

<td align="center">
<b>Chat Assistant</b><br>
<img src="image/chat_assistant.png" width="350">
</td>

<td align="center">
<b>Result</b><br>
<img src="image/result_search.png" width="350">
</td>
</tr>

<tr>
<td align="center">
<b>Monitoring</b><br>
<img src="image/monitoring_1.png" width="350">
</td>

<td align="center">
<b>Latency-Token</b><br>
<img src="image/latency_token.png" width="350">
</td>

<td align="center">
<b>Question-Documents</b><br>
<img src="image/Question_Doc.png" width="350">
</td>
</tr>

<tr>
<td align="center">
<b>Model Usage</b><br>
<img src="image/model_usage.png" width="350">
</td>

<td align="center">
<b>Rag Evaluation</b><br>
<img src="image/rag_eval.png" width="350">
</td>

<td align="center">
<b>LogFire</b><br>
<img src="image/logfire.png" width="350">
</td>
</tr>


</table>

# 🚀 Future Improvements

* Authentication
* Conversation memory
* Reranking models
* Automatic document ingestion
* Continuous evaluation
* CI/CD pipeline
* Kubernetes deployment
* Multi-agent architecture

---

# ⚠️ Disclaimer

The documentation contained in this repository is entirely synthetic and generated using a Large Language Model (LLM).

It is intended exclusively for educational and demonstration purposes and does **not** represent the operational procedures, internal documentation, or confidential information of any financial institution, payment provider, or mobile money operator.

---

# 👤 Author

**Tina Rakotozafy**

Data Scientist • AI Engineer

Passionate about Data Engineering, Artificial Intelligence, Retrieval-Augmented Generation (RAG), MLOps, and production-ready AI systems.
