# 🚀 Productivity Advisor

A RAG application that provides personalized productivity guidance by combining a curated productivity knowledge base with a large language model. built as a project for Datacamp(llm-zoomcamp)

## Overview

Productivity Advisor is an assistant designed to help users become more productive by recommending appropriate productivity frameworks, suggesting tasks, improving planning, and reducing overwhelm.

Instead of relying only on a language model's general knowledge, the application retrieves relevant examples and productivity strategies from a structured dataset before generating a response. This produces recommendations that are more consistent, explainable, and grounded in the project's knowledge base.

---

# Problem Statement

Many people struggle with questions such as:

- Where should I start?
- What task should I do next?
- How can I stay focused?
- Which productivity technique fits my situation?
- How can I break a large task into manageable steps?
- How should I plan my day?

Traditional chatbots provide generic advice that may not follow a consistent productivity methodology. Productivity Advisor addresses this problem by retrieving relevant productivity examples and frameworks from a curated dataset before generating recommendations.

The goal is to deliver practical, context-aware productivity advice that users can immediately apply.

---

# Project Goals

The system helps users:

- Find suitable productivity techniques
- Discover tasks that match available time
- Break large tasks into smaller actionable steps
- Improve focus during work or study
- Reduce decision fatigue
- Organize daily and weekly plans
- Receive explanations for why a specific productivity framework is recommended

---

# Dataset

The project uses a custom productivity dataset generated with ChatGPT and stored in the `data/` directory.

The dataset contains 250 productivity task records, where each record represents a task paired with an appropriate productivity framework and implementation guidance.

Each row contains the following fields:

| Column              | Description                                                          |
| ------------------- | -------------------------------------------------------------------- |
| `task`              | The task or activity                                                 |
| `category`          | Task category (Work, Study, Home, Fitness, Personal, Creative, etc.) |
| `difficulty`        | Estimated task difficulty                                            |
| `duration_estimate` | Estimated completion time (minutes)                                  |
| `framework_name`    | Recommended productivity framework                                   |
| `reasoning`         | Why the framework fits the task                                      |
| `instructions`      | Step-by-step guidance                                                |
| `tags`              | Keywords describing the task                                         |

Example:

| Task                          | Category | Framework          |
| ----------------------------- | -------- | ------------------ |
| Write a project summary       | Work     | Time Blocking      |
| Organize pantry shelves       | Home     | Task Decomposition |
| Review study notes            | Study    | Spaced Repetition  |
| Practice breathing meditation | Personal | Habit Stacking     |

The dataset serves as the knowledge base for the RAG pipeline.

---

# How It Works

The application follows a Retrieval-Augmented Generation workflow:

1. The user asks a productivity-related question.
2. The system converts the query into an embedding.
3. Similar productivity records are retrieved from the dataset.
4. The retrieved context is provided to the language model.
5. The language model generates a personalized, grounded response based on the retrieved information.

This approach combines semantic search with natural language generation to produce relevant and explainable recommendations.

---

# Example Questions

Users can interact with Productivity Advisor using natural language, for example:

- "I only have 20 minutes. What should I work on?"
- "How can I improve my focus?"
- "Suggest some quick productivity tasks."
- "I'm feeling overwhelmed. Where should I start?"
- "Help me plan today's work."
- "Which productivity framework should I use for writing?"
- "How can I organize my study session?"
- "Give me tasks that fit into a 30-minute break."
- "How do I break a large project into smaller steps?"

---

# Features

- Retrieval-Augmented Generation (RAG)
- Semantic search over productivity tasks
- Productivity framework recommendations
- Personalized task suggestions
- Step-by-step task instructions
- Context-aware productivity advice
- Explainable recommendations with supporting reasoning

---

# 🏗️ System Architecture

```
                ┌────────────────────┐
                │   CSV Dataset      │
                └─────────┬──────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  Prefect Ingestion    │
              │ • Load data           │
              │ • Chunk Documents     │
              │ • Generate Embeddings │
              └─────────┬─────────────┘
                        │
                        ▼
              ┌──────────────────────┐
              │   SQLite Vector DB   │
              └─────────┬────────────┘
                        │
                        ▼
                 User Question
                        │
                        ▼
             ┌────────────────────────┐
             │ Query Rewriting (LLM)  │
             └─────────┬──────────────┘
                       ▼
          ┌────────────────────────────┐
          │ Hybrid Retrieval           │
          │ • Semantic Search          │
          │ • Metadata Filtering       │
          └─────────┬──────────────────┘
                    ▼
         ┌─────────────────────────────┐
         │ LLM Document Re-ranking     │
         └─────────┬───────────────────┘
                   ▼
          ┌────────────────────────────┐
          │ Context Assembly           │
          └─────────┬──────────────────┘
                    ▼
           ┌──────────────────────────┐
           │ LLM Response Generation  │
           └─────────┬────────────────┘
                     ▼
              Streamlit Interface
```

---

# 📂 Project Structure

```
productivity-advisor/
│
├── app/
│   └── app.py
│
├── db/
│   ├── db_prep.py
│   └── db.py
│
├── data/
│   ├── raw_data.csv
│   ├── rag-eval-gpt-4o-mini.csv
│   ├── ground-truth-retrieval.csv
│   └── cleaned_data.csv
│
├── ingestion/
│   └── ingest.py
│
├── rag/
│   ├── rag.py
│   └── search.py
│
├── notebooks/
│   ├── cleaning.ipynb
│   ├── eval-generated-data.ipynb
│   └── rag.ipynb
│
├── README.md
├── requirements.txt
├── pyproject.toml
└── uv.lock
```

---

# ⚙️ Installation

Clone the repository

```bash
git clone https://github.com/thepassant/productivity-advisor.git
```

## Installation

### 1. Create a virtual environment

```bash
uv venv
```

### 2. Activate the virtual environment

#### Windows

```bash
.venv\Scripts\activate
```

#### Linux / macOS

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
uv pip install -r requirements.txt
```

### 4. Copy the environment file

#### Linux / macOS

```bash
cp .env.example .env
```

#### Windows (PowerShell)

```powershell
Copy-Item .env.example .env
```

#### Windows (Command Prompt)

```cmd
copy .env.example .env
```

### 5. Configure environment variables

Open the `.env` file and add your API keys and any required configuration values.

# 🚀 Running the Project

---

### 1. Run the Ingestion Pipeline

```bash
python ingestion/ingest.py
```

---

### 2. Launch the Application

```bash
streamlit run app/app.py
```

# 🔍 Retrieval Pipeline

The retrieval process consists of:

1. User submits a question
2. LLM rewrites the query
3. Hybrid retrieval searches ChromaDB
4. Retrieved documents are re-ranked
5. Relevant context is assembled
6. LLM generates the final recommendation

---

# 📊 Evaluation

for the code of evaluating the system, you can find it in notebooks/rag.ipynb

### Retrieval Evaluation

The basic approach - using minsearch without boosting gave:

- hitrate: 80%
- MRR: 60%

### RAG flow

I used LLM-as-a-Judge scoring

The best-performing configuration is used in the final application.

for gpt-4o-mini, among 200 records , we had:

- 156 (75%) RELEVANT
- 33 (18%) PARTLY_RELEVANT
- 11 (7%) NON_RELEVANT

We also tested gpt-4o same results as gpt-5.4-mini , among 200 records , we had:

- 156 (78) RELEVANT
- 36 (18%) PARTLY_RELEVANT
- 8 (4%) NON_RELEVANT

### MONITORING

---

# 🛠️ Tech Stack

- Python
- Streamlit
- OpenAI API
- Sentence Transformers
- SQLite

---

# 📜 License

This project is licensed under the **MIT License**.

---

# 🙏 Acknowledgements

Built as the final project for LLM Zoomcamp.

Special thanks to the Zoomcamp instructors and the open-source community for providing the learning resources that inspired this project.
