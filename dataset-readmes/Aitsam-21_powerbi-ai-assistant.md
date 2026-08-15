# 📊 DAX Copilot — Power BI & DAX AI Assistant

An end-to-end RAG (Retrieval-Augmented Generation) application that answers Power BI and DAX questions using official Microsoft documentation as its knowledge base — not just an LLM's memory, but real, cited, up-to-date sources.

**Live demo:** *[add your Streamlit Cloud link here once deployed, or note "run locally / via Docker" below]*

**Demo video:** *[add link or embed here]*

---

## The problem

DAX (Data Analysis Expressions) is the formula language behind Power BI, and it's notoriously easy to get subtly wrong — LLMs asked generic DAX questions frequently hallucinate incorrect syntax or invent functions that don't exist. Power BI developers (myself included) need fast, **accurate**, **source-grounded** answers, not confident-sounding guesses.

DAX Copilot solves this by retrieving relevant passages from official Microsoft documentation before generating an answer, and always cites which sources were used — so answers are traceable and verifiable rather than black-box.

---

## How it works

```
User question
     │
     ▼
Embed question (sentence-transformers, local, free)
     │
     ▼
Search ChromaDB vector store (545 chunks of Microsoft DAX docs)
     │
     ▼
Retrieve top-5 most relevant chunks
     │
     ▼
Build prompt: question + retrieved context + instructions
     │
     ▼
Groq API (Llama 3.3 70B) generates grounded answer
     │
     ▼
Answer + cited sources shown to user
     │
     ▼
Interaction logged (question, answer, sources, feedback) → SQLite
```

### Knowledge base

- **386 chunks** — every function in the official [DAX function reference](https://learn.microsoft.com/en-us/dax/dax-function-reference) (syntax, parameters, examples)
- **159 chunks** — conceptual documentation (DAX overview, queries, variables, operators, syntax rules, user-defined functions), split by section for precise retrieval
- **545 chunks total**, scraped directly from learn.microsoft.com, cleaned of navigation/footer noise, and embedded locally with `sentence-transformers` (`all-MiniLM-L6-v2`)

Adding conceptual docs alongside function references improved retrieval accuracy from **70% → 90%** on a 10-question test set — see [`evaluation.md`](evaluation.md) for full methodology and results.

---

## Tech stack

| Component | Tool | Why |
|---|---|---|
| LLM | Groq API (Llama 3.3 70B) | Free tier, fast inference |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Local, free, no API cost |
| Vector store | ChromaDB | Simple, file-based, no server needed |
| Interface | Streamlit | Fast to build, familiar chat UI |
| Monitoring | SQLite + Streamlit dashboard | Zero-setup persistent logging |
| Containerization | Docker | Reproducible, portable deployment |

**Cost to run: $0** — every component uses a free tier or runs locally.

---

## Evaluation

Two experiments were run and documented in [`evaluation.md`](evaluation.md):

1. **Retrieval evaluation** — compared a functions-only knowledge base vs. functions+concepts on 10 test questions. Functions+concepts won, 90% vs 70% accuracy.
2. **LLM evaluation** — compared a minimal prompt vs. a structured prompt (with explicit instructions and a request for code examples) on 3 questions. The structured prompt consistently produced more precise, example-driven answers.

See [`evaluation.md`](evaluation.md) for full test-by-test breakdowns and reasoning.

---

## Screenshots

*(Add 2–3 screenshots here: the main chat interface answering a question, and the Analytics dashboard. Screenshots make it much easier for reviewers to quickly understand what the app does.)*

---

## Project structure

```
powerbi-ai-assistant/
├── App.py                      # Main Streamlit chat interface
├── pages/
│   └── 1_Analytics.py          # Monitoring dashboard (5 charts + feedback stats)
├── rag_pipeline.py             # Core RAG logic: retrieve → prompt → generate
├── logger.py                   # SQLite logging for questions/answers/feedback
├── build_index.py              # Builds the ChromaDB vector index
├── discover_urls.py            # Finds all DAX function page URLs
├── scrape_content.py           # Scrapes + cleans function reference pages
├── scrape_concept.py           # Scrapes + cleans conceptual doc pages
├── chunk_concept.py            # Splits long concept pages into chunks
├── evaluate_retrieval.py       # Retrieval evaluation script
├── evaluate_prompt.py          # LLM/prompt evaluation script
├── evaluation.md               # Written evaluation results
├── Dockerfile                  # Container definition
├── .dockerignore
├── requirements.txt
└── chroma_db/                  # Persisted vector database (generated)
```

---

## Setup & installation

### Prerequisites
- Python 3.12
- A free [Groq API key](https://console.groq.com)
- (Optional) [Docker Desktop](https://www.docker.com/products/docker-desktop/) if running via container

### 1. Clone the repository
```bash
git clone https://github.com/Aitsam-21/powerbi-ai-assistant.git
cd powerbi-ai-assistant
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your Groq API key
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_key_here
```

### 5. Build the knowledge base
This scrapes Microsoft's docs and builds the vector index (takes a few minutes; only needs to be run once):
```bash
python discover_urls.py
python scrape_content.py
python scrape_concept.py
python chunk_concept.py
python build_index.py
```

### 6. Run the app
```bash
streamlit run App.py
```
Open **http://localhost:8501** in your browser.

---

## Running with Docker

Once the knowledge base is built (steps above), you can containerize and run the whole app:

```bash
docker build -t dax-copilot .
docker run -p 8501:8501 --env-file .env dax-copilot
```

Open **http://localhost:8501** in your browser.

---

## Example usage

**Q: How do I calculate year-over-year growth in DAX?**

> To calculate year-over-year growth, use `SAMEPERIODLASTYEAR` to get the prior year's value, then compare:
> ```dax
> YoY% =
> VAR Sales = SUM(Sales[Sales Amount])
> VAR SalesLastYear = CALCULATE(SUM(Sales[Sales Amount]), SAMEPERIODLASTYEAR('Date'[Date]))
> RETURN
>     IF(Sales && SalesLastYear, DIVIDE((Sales - SalesLastYear), SalesLastYear))
> ```
> *Sources: VAR, DAX overview, PREVIOUSYEAR*

---

## Monitoring & feedback

Every question is logged (timestamp, question, answer, sources cited) to a local SQLite database. Users can rate answers 👍/👎, and the **Analytics** page (accessible from the app sidebar) shows:

1. Questions per day
2. Feedback breakdown (positive/negative/unrated)
3. Helpfulness rate over time
4. Most-cited documentation sources
5. Question length distribution
6. A searchable table of recent interactions

---

## Known limitations

- Pure vector search is sensitive to query phrasing — some conceptual questions (e.g. "how do I use variables in DAX") don't reliably surface the right chunk even when it exists in the knowledge base. See `evaluation.md` for details. Hybrid search (keyword + vector) or query rewriting would likely close this gap.
- The knowledge base currently covers DAX function reference + core conceptual docs only; it does not include community forum content or SQLBI articles, which could add troubleshooting-style coverage.

---

## Author

Built by **Muhammad Aitsam Zulfiqar** — Power BI Developer & Data Analyst.
[GitHub](https://github.com/Aitsam-21)
