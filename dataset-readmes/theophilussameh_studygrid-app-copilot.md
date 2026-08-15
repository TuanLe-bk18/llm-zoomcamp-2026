# 🧠 GridMind — AI Copilot for StudyGrid

> An **Agentic Retrieval-Augmented Generation (RAG)** assistant built for the StudyGrid mobile application, enabling students to instantly find accurate information about app features, workflows, and frequently asked questions through intelligent retrieval, tool calling, and LLM reasoning.

<p align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red?logo=streamlit)
![SQLite](https://img.shields.io/badge/SQLite-Vector%20Store-003B57?logo=sqlite)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Monitoring-blue?logo=postgresql)
![Groq](https://img.shields.io/badge/LLM-Groq-orange)
![License](https://img.shields.io/badge/License-MIT-green)

</p>

---

# 📖 Project Overview

GridMind is an intelligent AI assistant designed for **StudyGrid**, a collaborative learning platform that helps students organize class materials, manage study groups, communicate with teammates, and stay on top of academic tasks.

Instead of manually browsing documentation or asking other students, users can simply ask questions in natural language. GridMind retrieves the most relevant knowledge from the application's FAQ knowledge base, reasons over the retrieved information, and generates concise, context-aware responses.

Unlike a traditional RAG chatbot, GridMind follows an **Agentic RAG** architecture. Rather than sending every user question directly to the language model, the agent decides when retrieval is needed, invokes tools to search the knowledge base, gathers relevant context, and only then produces the final answer.

The project also includes an end-to-end evaluation pipeline, an automated monitoring system, quality assessment using an LLM-as-a-Judge, and a dashboard for tracking latency, token usage, cost, and user feedback.

---

# 🚀 Demo

<p align="center">
<img src="images/chat-ui.png" width="900">
</p>

The chat interface allows users to interact with GridMind using natural language while the system automatically:

- Retrieves relevant information from the knowledge base.
- Uses tool calling when retrieval is required.
- Generates context-aware responses.
- Records execution metrics.
- Evaluates answer relevance using an LLM judge.
- Collects explicit user feedback through 👍 / 👎 reactions.

---

# 🎯 Problem Statement

StudyGrid provides numerous features for collaboration, communication, and study management. As the application grows, users frequently need help understanding how specific features work, such as creating teams, inviting members, joining groups, or managing study materials.

Traditional support options have several limitations:

- Searching documentation is slow.
- Users may not know the correct keywords.
- Static FAQ pages require manual browsing.
- Human support is not always available.

GridMind addresses these challenges by allowing users to ask questions naturally while automatically retrieving the most relevant information and generating accurate answers grounded in the application's knowledge base.

---

# ✨ Key Features

- 🤖 Agentic Retrieval-Augmented Generation (Agentic RAG)
- 🔍 Persistent semantic retrieval using SQLite
- 🛠 Tool Calling for dynamic knowledge retrieval
- 🧩 Modular architecture separating agent, retrieval, search, and prompting
- 📊 Offline evaluation for both retrieval quality and complete agent performance
- 📈 Built-in monitoring dashboard
- ⚖️ Automatic answer quality evaluation using LLM-as-a-Judge
- 👍 User feedback collection
- 💰 Token, latency, and cost tracking
- 💬 Interactive Streamlit chat interface

---

# 🏗️ System Architecture

> *(Architecture diagram will be inserted here.)*

The system is organized into independent components, making it easy to extend, test, and maintain.

- **Agent** orchestrates the reasoning process.
- **Retriever** searches the persistent knowledge base.
- **Search Tool** exposes retrieval as a callable tool.
- **Prompt Builder** constructs the final prompt.
- **LLM** generates grounded responses.
- **Monitoring Layer** records execution metrics and feedback.
- **Dashboard** visualizes operational statistics.
---

# 🔄 End-to-End Workflow

GridMind processes each user question through an agentic workflow instead of a single retrieval-and-generation step.

> *(Workflow diagram will be inserted here.)*

The execution pipeline consists of the following stages:

1. **User Question**

   The user submits a natural language question through the Streamlit interface.

2. **Agent Reasoning**

   The GridMind Agent analyzes the request and determines whether external knowledge retrieval is required.

3. **Tool Calling**

   If additional context is needed, the agent invokes the Search Tool rather than answering immediately.

4. **Knowledge Retrieval**

   The retriever searches the persistent SQLite knowledge base and returns the most relevant FAQ documents.

5. **Context Construction**

   Retrieved documents are combined into a structured context that is injected into the final prompt.

6. **LLM Response Generation**

   Using the retrieved knowledge, the language model generates a grounded response.

7. **Monitoring**

   During execution, the system records latency, token usage, LLM calls, and estimated cost.

8. **Quality Assessment**

   The generated response is automatically evaluated using an LLM-as-a-Judge, while users can also provide explicit feedback through 👍 / 👎 reactions.

---

# 🛠 Technology Stack

| Category | Technologies |
|-----------|--------------|
| Language | Python |
| LLM | Groq (`openai/gpt-oss-20b`) |
| Agent Framework | Custom Agent |
| Retrieval | SQLite Persistent Vector Index |
| Interface | Streamlit |
| Monitoring Database | PostgreSQL |
| Evaluation | Pydantic, Structured Outputs |
| Configuration | Python Dotenv |
| Environment | uv |

---

# 📚 Dataset

GridMind is built on a curated knowledge base extracted from the StudyGrid application's Frequently Asked Questions (FAQs).

The dataset contains information about:

- Account management
- Authentication
- Study groups
- Team management
- Invitations
- Notes
- Tasks
- Notifications
- General application usage

To support offline evaluation, a dedicated ground-truth dataset was generated automatically.

### Ground Truth Generation

Rather than manually writing evaluation questions, we generated realistic support-style questions directly from each FAQ answer using the LLM.

Each FAQ entry produced **five natural-language questions**, resulting in:

- **34 FAQ documents**
- **170 evaluation questions**

Structured outputs (via **Pydantic**) ensured every generated question followed a consistent schema while remaining faithful to the original FAQ content.

---

# 📂 Project Structure

```text
.
├── data/
├── evaluation/
├── monitoring/
├── agent.py
├── retriever.py
├── search.py
├── tools.py
├── prompts.py
├── context.py
├── main.py
└── ...
```

### Core Components

| Component | Responsibility |
|------------|----------------|
| `agent.py` | Coordinates the complete reasoning process and decides when to invoke tools. |
| `retriever.py` | Retrieves relevant documents from the persistent knowledge base. |
| `search.py` | Implements semantic search functionality. |
| `tools.py` | Defines callable tools available to the agent. |
| `context.py` | Builds the retrieval context supplied to the LLM. |
| `prompts.py` | Contains prompt templates used by the agent. |
| `evaluation/` | Ground-truth generation, retrieval evaluation, and agent evaluation notebooks. |
| `monitoring/` | Metrics collection, dashboard, database utilities, judge, and feedback pipeline. |

---

# 🔍 Retrieval Pipeline

The retrieval pipeline is responsible for providing the language model with reliable, grounded context.

Instead of relying on the LLM's internal knowledge alone, GridMind retrieves the most relevant FAQ entries before generating a response.

The retrieval workflow consists of:

- Persistent knowledge indexing
- Semantic search
- Top-k document retrieval
- Context construction
- Prompt augmentation

This design significantly reduces hallucinations while ensuring responses remain grounded in the StudyGrid knowledge base.

---

# 🤖 Agent Workflow

Unlike traditional RAG systems that retrieve documents for every question, GridMind follows an **agentic** approach.

The agent is responsible for:

- Understanding the user's intent.
- Deciding whether retrieval is necessary.
- Invoking the Search Tool when required.
- Integrating retrieved knowledge.
- Producing the final grounded answer.

Separating reasoning from retrieval makes the system easier to extend with additional tools in the future while keeping retrieval logic independent from the agent itself.

---

# 🛠 Function Calling

GridMind exposes retrieval through callable tools rather than embedding search directly inside the agent.

This separation provides several advantages:

- Cleaner architecture.
- Easier testing.
- Better modularity.
- Simpler future integration of additional tools.

Currently, the agent uses the Search Tool to retrieve relevant knowledge, but the same architecture can naturally support calculators, external APIs, or other domain-specific tools.

---

# 📊 Evaluation

Building an intelligent assistant is only half of the challenge—the other half is measuring how well it performs.

GridMind includes an offline evaluation pipeline covering both **retrieval quality** and **end-to-end agent performance**, following the common evaluation methodology:

```
Knowledge Base
      │
      ▼
Generate Ground Truth Questions
      │
      ▼
Run GridMind Agent
      │
      ▼
Evaluate Retrieval
      │
      ▼
Evaluate Final Answer
```

Rather than manually writing evaluation questions, realistic support-style questions were automatically generated from each FAQ answer using the LLM.

This approach ensures that evaluation remains reproducible, scalable, and closely aligned with the underlying knowledge base.

---

## Ground Truth Generation

To build a reliable evaluation dataset, every FAQ document was transformed into multiple realistic user questions.

The generation process used:

- Structured Outputs with **Pydantic**
- `openai/gpt-oss-20b` running on **Groq**
- Five questions generated for every FAQ entry

The final evaluation dataset contains:

| Item | Value |
|------|------:|
| FAQ Documents | **34** |
| Generated Questions | **170** |
| Questions per FAQ | **5** |

Because the questions were generated directly from the FAQ answers, they closely resemble real support requests while remaining faithful to the available documentation.

---

## Retrieval Evaluation

The first stage evaluates only the retrieval system.

For every generated question, the retriever searches the knowledge base and the returned documents are compared against the original FAQ document.

Two ranking metrics were used:

| Metric | Description |
|---------|-------------|
| **Hit Rate** | Whether the correct document appears within the retrieved results |
| **Mean Reciprocal Rank (MRR)** | Measures how highly the correct document is ranked |

### Results

| Metric | Score |
|---------|-------|
| **Hit Rate** | **97.1%** |
| **MRR** | **0.889** |

These results demonstrate that the retriever consistently identifies the correct knowledge source before answer generation.

---

## Improving Retrieval Through Evaluation

Evaluation was not only used to report metrics—it directly improved the retrieval pipeline.

During experimentation, the evaluation process exposed an inconsistency in the vector search configuration.

Based on these findings, the vector index was changed from **LSH** to **IVF**, which produced more stable retrieval performance for GridMind's relatively small knowledge base.

This highlights one of the primary goals of evaluation: using measurable evidence to improve system quality rather than simply reporting benchmark numbers.

---

## Agent Evaluation

Retrieval quality alone does not guarantee high-quality responses.

GridMind therefore evaluates the complete agent execution pipeline, including:

- Tool invocation
- Retrieval behavior
- Final answer generation

Instead of evaluating only the retrieved documents, the complete reasoning process is executed for every evaluation question.

The evaluation framework also records the tool-call trajectory taken by the agent, making it possible to analyze not only answer quality but also the reasoning path that produced it.

---

# 📈 Monitoring

Offline evaluation measures how well the system performs before deployment.

Monitoring focuses on understanding how the system behaves while users are actively interacting with it.

GridMind includes a lightweight monitoring stack built specifically for its **agentic architecture**.

Unlike traditional RAG applications—which often execute a single LLM call per question—GridMind may invoke the language model multiple times while reasoning and calling tools.

For this reason, all monitoring metrics are aggregated **per user question**, providing a more meaningful view of real execution cost and performance.

---

## Monitoring Architecture

> *(Monitoring architecture diagram will be inserted here.)*

The monitoring layer consists of four major components:

- **Metrics Collector**
- **PostgreSQL Storage**
- **LLM-as-a-Judge**
- **Analytics Dashboard**

Together they provide complete visibility into system behavior.

---

## Execution Metrics

Every user interaction records operational metrics including:

| Metric | Description |
|---------|-------------|
| Response Time | Total execution time per question |
| LLM Calls | Number of model invocations performed by the agent |
| Prompt Tokens | Tokens consumed by prompts |
| Completion Tokens | Tokens generated by the model |
| Total Tokens | Combined token usage |
| Estimated Cost | Aggregated execution cost |
| Judge Verdict | Automatic quality assessment |
| User Feedback | 👍 / 👎 reactions |

These metrics help analyze both application performance and operational cost.

---

## LLM-as-a-Judge

Each generated answer is automatically reviewed using an independent language model.

Instead of relying solely on user feedback, the judge classifies responses into three categories:

- ✅ Relevant
- 🟡 Partly Relevant
- ❌ Non-Relevant

This provides an additional automated quality signal that complements explicit user ratings.

Because the judge introduces an additional LLM call, it currently runs synchronously after each response. In a production environment, this component could be executed asynchronously or applied to sampled conversations to reduce latency and cost.

---

## Dashboard

The monitoring dashboard provides a high-level overview of application usage and performance.

It includes:

- Total conversations
- Average response time
- Token usage
- Estimated cost
- Average LLM calls per question
- Cost trends
- Latency trends
- Judge relevance distribution
- User feedback statistics

<p align="center">
<img src="images/dashboard-overview.png" width="900">
</p>

<p align="center">
<img src="images/dashboard-analytics.png" width="900">
</p>

<p align="center">
<img src="images/dashboard-feedback.png" width="900">
</p>

The dashboard enables continuous monitoring of both technical performance and answer quality from a single interface.

---

# ⚙️ Engineering Decisions

Several architectural decisions distinguish GridMind from a conventional RAG chatbot.

### Agentic Architecture

Rather than forcing retrieval for every request, the agent decides when external knowledge is necessary and invokes tools accordingly.

---

### Modular Design

The project separates the agent, retrieval layer, search logic, prompts, evaluation, and monitoring into independent modules, improving maintainability and future extensibility.

---

### Persistent Knowledge Base

The knowledge base is stored as a persistent SQLite index, allowing retrieval without rebuilding the index on every application startup.

---

### Evaluation-Driven Development

Offline evaluation is treated as a development tool—not merely a reporting mechanism.

Evaluation results were actively used to refine the retrieval pipeline and improve system quality.

---

### Production-Oriented Monitoring

Instead of recording only LLM responses, monitoring captures the entire execution of the agent, including multiple tool calls, execution cost, response latency, automated quality assessment, and explicit user feedback.

---

# 🚀 Getting Started

## Prerequisites

Before running GridMind, make sure you have:

- Python **3.12+**
- [uv](https://docs.astral.sh/uv/)
- Docker (for PostgreSQL monitoring)
- A Groq API Key

---

## Clone the Repository

```bash
git clone https://github.com/theophilussameh/studygrid-app-copilot.git
cd studygrid-app-copilot
```

---

## Install Dependencies

Using **uv**:

```bash
uv sync
```

or

```bash
uv pip install -e .
```

---

## Environment Variables

Create a `.env` file in the project root.

```env
GROQ_API_KEY=your_api_key

POSTGRES_HOST=localhost
POSTGRES_DB=gridmind
POSTGRES_USER=user
POSTGRES_PASSWORD=password
```

---

# 📚 Build the Knowledge Base

Generate the persistent SQLite index.

```bash
uv run python ingest.py
```

This step only needs to be executed once (or whenever the FAQ dataset changes).

---

# 💬 Run the Chat Application

```bash
uv run python main.py
```

or, if using the monitoring interface:

```bash
uv run streamlit run monitoring/app.py
```

---

# 📈 Run the Monitoring Dashboard

Start PostgreSQL:

```bash
docker network create gridmind-net

docker run -d \
    --name gridmind-pg \
    --network gridmind-net \
    -e POSTGRES_USER=user \
    -e POSTGRES_PASSWORD=password \
    -e POSTGRES_DB=gridmind \
    -p 5432:5432 \
    -v pgdata:/var/lib/postgresql/data \
    postgres:17
```

Create the monitoring tables:

```bash
uv run python monitoring/db_init.py
```

Launch the dashboard:

```bash
uv run streamlit run monitoring/dashboard.py --server.port 8502
```

---

# 🧪 Run the Evaluation

Search evaluation:

```bash
evaluation/01_ground_truth_and_search_eval.ipynb
```

RAG evaluation:

```bash
evaluation/02_rag_evaluation.ipynb
```

Ground truth generation utilities:

```bash
evaluation/evaluation_utils.py
```

---

# 📷 Screenshots

## Chat Application

(image)

---

## Monitoring Dashboard

(image)

---

## Feedback & Judge

(image)

---

# 🚧 Future Improvements

- Conversation memory
- Multi-tool support
- External API integrations
- Async LLM Judge
- Docker Compose deployment
- Grafana / Prometheus integration
- Multi-user authentication
- Production deployment

---

# 🙏 Acknowledgments

This project was developed as the capstone project for the **LLM Zoomcamp** by DataTalks.Club.

Special thanks to the course instructors and the open-source community for providing the educational material that inspired parts of the evaluation and monitoring pipeline.

---

## Author

**Theophilus Sameh**

Computer and Control Systems Engineering student passionate about Artificial Intelligence, Large Language Models, Information Retrieval, and Mobile Application Development.

This repository documents my journey toward becoming an LLM Engineer by applying every concept learned in the LLM Zoomcamp to a real-world project instead of simply reproducing the course notebooks.

- GitHub: https://github.com/theophilussameh
- LinkedIn: https://www.linkedin.com/in/theophilussameh