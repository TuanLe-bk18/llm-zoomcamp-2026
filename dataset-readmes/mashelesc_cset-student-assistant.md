# 🎓 UNISA CSET Student Assistant

A Retrieval Augmented Generation (RAG) application that answers questions about
UNISA's College of Science, Engineering and Technology (CSET) — qualifications,
admissions, modules, fees, and registration.

Built as the capstone project for the [LLM Zoomcamp 2026](https://github.com/DataTalksClub/llm-zoomcamp) by DataTalks.Club.

---

## 📌 Problem Statement

UNISA's CSET website contains a large amount of information spread across many pages.
Students frequently struggle to find clear answers to common questions about:

- Admission requirements for specific qualifications
- Module structures and credit requirements
- Registration deadlines and procedures
- Fees and funding options
- Postgraduate application processes

This assistant provides a conversational interface that retrieves the most relevant
information from the CSET knowledge base and generates accurate, grounded answers
using an LLM — without hallucinating content that isn't there.

---

## 🏗️ Architecture

```
UNISA CSET Website
        ↓
  Web Scraper (requests + BeautifulSoup)
        ↓
  raw_pages.json
        ↓
  Cleaner + Chunker (regex + custom Python)
        ↓
  cset_documents.json
        ↓
  Embeddings (OpenAI text-embedding-3-small)
        ↓
  PGVector (PostgreSQL + pgvector extension)
        ↓
  RAG Pipeline
        ├── search()      → cosine similarity via <=> operator
        ├── build_prompt() → context injection
        └── llm()    → GPT-5.4-mini
        ↓
  Streamlit Chat Interface
        ↓
  Evaluation (Hit Rate, MRR, LLM-as-a-Judge)
        ↓
  Monitoring Dashboard (query log + feedback)
```

---

## 🛠️ Tech Stack

| Component | Tool |
|---|---|
| Web scraping | `requests`, `BeautifulSoup4`, `lxml` |
| Data cleaning | `pandas`, `re` |
| Embeddings | OpenAI `text-embedding-3-small` (1536 dims) |
| Vector database | PostgreSQL + `pgvector` extension |
| Vector index | HNSW (cosine similarity) |
| LLM | OpenAI `gpt-5.4-mini` |
| Interface | `Streamlit` |
| Monitoring | Streamlit multi-page + PostgreSQL `query_log` |
| Containerization | Docker + Docker Compose |
| Language | Python 3.12 |

---

## 📁 Project Structure

```text
cset_student_assistant/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .env
├── notebooks/
│   ├── cset_scraping.ipynb
│   ├── embeddings.ipynb
│   ├── monitoring.ipynb
│   ├── rag_evaluation.ipynb
│   └── rag_pipeline.ipynb
├── scripts/
│   ├── cset_documents.json
│   ├── data_cleaning.py
│   ├── embeddings.py
│   ├── rag_evaluation.py
│   ├── rag_pipeline.py
│   ├── raw_pages.json
│   └── web_scraping.py
└── streamlit/
    ├── app.py
    └── pages/
        └── monitoring.py
```

---

## 🚀 Reproducing the Project

### Prerequisites

- Docker and Docker Compose installed
- Python 3.12+
- An OpenAI API key ([platform.openai.com](https://platform.openai.com))
- Internet access for the scraping step

### Step 1 — Clone the repository

```bash
git clone https://github.com/mashelesc/cset-student-assistant.git
cd cset_student_assistant
```

### Step 2 — Set up environment variables

Create a `.env` file in the project root and add your API key:

```env
OPENAI_API_KEY=sk-...
```

You can also define the PostgreSQL values used by the Docker setup if needed:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydb
DB_USER=myuser
DB_PASSWORD=mypassword
```

### Step 3 — Install Python dependencies

The project uses standard Python packages for scraping, embeddings, Streamlit, and PostgreSQL access. Install them with:

```bash
pip install openai python-dotenv psycopg2-binary streamlit requests beautifulsoup4 lxml pandas tqdm
```

### Step 4 — Start the PostgreSQL + pgvector database

```bash
docker compose up -d db
```

### Step 5 — Scrape and prepare the knowledge base

Run the scripts in order:

```bash
python scripts/web_scraping.py
python scripts/data_cleaning.py
```

This produces the raw and cleaned document data used by the retrieval workflow.

### Step 6 — Embed documents and ingest them into PGVector

```bash
python scripts/embeddings.py
```

This embeds the prepared documents and stores them in PostgreSQL using pgvector.

### Step 7 — Run the Streamlit app

```bash
streamlit run streamlit/app.py
```

Visit [http://localhost:8501](http://localhost:8501)

---

## 🐳 Running with Docker Compose (Full Stack)

To run the database and the app together:

```bash
docker compose up --build
```

This starts:
- `db` — PostgreSQL + pgvector on port 5432
- `app` — the Streamlit interface on port 8501

> **Note:** Run the ingestion steps first so the database contains the vectorized documents before using the app.

---

## 📊 Evaluation

Evaluation is handled by the script in [scripts/rag_evaluation.py](scripts/rag_evaluation.py).

### Retrieval Evaluation

The script generates a synthetic evaluation dataset and measures:

| Metric | Description |
|---|---|
| **Hit Rate** | Percentage of questions where the correct document appears in the top results |
| **MRR** | Mean Reciprocal Rank — rewards finding the correct document earlier |

Results are written to `retrieval_eval_results.csv`.

---

## 📈 Monitoring

The monitoring dashboard is implemented in [streamlit/pages/monitoring.py](streamlit/pages/monitoring.py) and is available from the Streamlit app sidebar.

It is intended to help review:
- query history
- feedback patterns
- frequently referenced sources
- app usage trends

---

## ⚙️ Environment Variables

Create a `.env` file in the project root:

```env
# Required
OPENAI_API_KEY=sk-...

# Optional — defaults shown for local and Docker use
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydb
DB_USER=myuser
DB_PASSWORD=mypassword
```

> ⚠️ Never commit `.env` to Git.

---

## 📦 Dependencies

The project relies on the following core packages:

```text
openai
python-dotenv
psycopg2-binary
streamlit
requests
beautifulsoup4
lxml
pandas
tqdm
```

---

## 📝 Note on API Credits

The embedding ingestion script uses OpenAI API calls, so a funded API key is required for the full workflow.

---

## 👤 Author

**Silindile Comfort Mashele**
BSc Mathematics & Computer Science — UNISA
GitHub: [github.com/mashelesc](https://github.com/mashelesc)
X: [@mashele_sc](https://x.com/mashele_sc)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
