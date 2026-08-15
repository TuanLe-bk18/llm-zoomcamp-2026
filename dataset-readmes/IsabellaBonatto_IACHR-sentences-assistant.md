# IACHR Sentences Assistant

An AI assistant that answers questions about the judgments of the Inter-American Court of Human Rights using retrieval-augmented generation (RAG).

## Why this project

The Inter-American Court has a [search system](https://jurisprudencia.corteidh.or.cr/search/jurisdiction:EA+estado:r06r5ybrt450400/*) for jurisprudence, but it only supports exact text matching. This is a problem: when a lawyer is preparing a new judgment and needs to find similar cases, they may not find them if the wording doesn't match exactly.

This assistant uses an LLM with a RAG pipeline that does vector search instead of text search. This means it can find semantically similar content even when the exact words differ.

The app also shows the retrieved document fragments that were used to generate the answer, with direct links to the original PDFs. This matters because lawyers writing new judgments need to cite previous cases as jurisprudence.

The app is deployed and can be used here: https://iachr-sentences-assistant.streamlit.app/

This is the final project of the [DataTalksClub LLM Zoomcamp course](https://github.com/DataTalksClub/llm-zoomcamp/tree/main).

## How to reproduce

All the judgments are available at https://www.corteidh.or.cr/casos_sentencias.cfm. At the time this project was created, there were around 600 documents.

### Prerequisites

You will need a `.env` file in the project root with the following variables:

```
QDRANT_API_KEY=...
QDRANT_CLUSTER_ENDPOINT=...
OPENAI_API_KEY=...
SUPABASE_DATABASE_URL=...
```

### 1. Data collection

The first step is scraping the judgments from the Court's website. The scraper downloads each PDF, extracts the text, and parses metadata from the document headers (case name, country, date, document type).

```bash
uv run python data-collection/scraper.py
```

By default this processes the first 10 documents. To scrape all of them (currently hardcoded to Serie C 1-598 — update the range in the script if more judgments have been published):

```bash
uv run python data-collection/scraper.py --all
```

The extracted text files and a `metadata.json` file are saved in the `data/` folder. The metadata looks like this:

```json
"1": {
    "case_name": "Velásquez Rodríguez Vs. Honduras",
    "country": "Honduras",
    "date": "26 de junio de 1987",
    "year": 1987,
    "document_type": "Excepciones Preliminares",
    "serie_c": 1,
    "url": "https://www.corteidh.or.cr/docs/casos/articulos/seriec_01_esp.pdf",
    "text_file": "seriec_001_esp.txt",
    "text_length": 64760
}
```

These metadata fields are later used as filter options in the search.

### 2. Indexation

All scraped data needs to be indexed in a vector database. Qdrant was chosen because it offers a free tier and fits the project needs.

You need the `QDRANT_API_KEY` and `QDRANT_CLUSTER_ENDPOINT` variables in your `.env`.

The indexation is a manual script (not automated). In a future version, new files could be scraped and indexed incrementally. For now, the workflow is: scrape everything, then index everything.

To test with the first 10 files:

```bash
uv run python indexation/index.py
```

To index all documents:

```bash
uv run python indexation/index.py --all
```

If the indexation fails partway through (CPU overload, timeout, etc.), you can resume and only index the missing documents:

```bash
uv run python indexation/index.py --resume
```

Once the indexation is done, the `search` function in `indexation/index.py` can be used to query the index. It supports vector search and allows filtering by country, year range, and document type. The assistant decides which filters to apply based on the user's question.

### 3. RAG

The assistant retrieves relevant document chunks and uses them to enrich the prompt sent to the LLM. The RAG logic is in `assistant/rag_helper.py`, adapted from the course's RAGBase class to work with Qdrant. The embedding model is `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional vectors) and the LLM is `gpt-5.4-mini`.

You need the `OPENAI_API_KEY` variable in your `.env`.

### 4. Evaluation

#### 4.1. Retrieval

Retrieval evaluation follows the course pattern: generate hypothetical questions from document chunks, then measure Hit Rate and MRR across text search, vector search, and hybrid search.

First, generate the questions:

```bash
uv run python retrieval-evaluation/data-generation.py
```

Then run the evaluation:

```bash
uv run python retrieval-evaluation/run_evaluation.py
```

Results are saved in `data/retrieval_evaluation_results.json`. The results for this project were:

```json
{
  "num_questions": 60,
  "text_search": {
    "hit_rate": 0.0,
    "mrr": 0.0
  },
  "vector_search": {
    "hit_rate": 0.6333333333333333,
    "mrr": 0.48583333333333323
  },
  "hybrid_search": {
    "hit_rate": 0.6333333333333333,
    "mrr": 0.48583333333333323
  }
}
```

Vector search and hybrid search had identical results, so vector search alone was chosen for simplicity.

#### 4.2. Relevance score

An LLM-as-a-judge evaluates the relevance of each answer relative to the user's question. The relevance score and explanation are saved in the database. Low-relevance answers can then be reviewed to debug and improve the assistant.

### 5. App

To run the assistant locally:

```bash
uv run streamlit run assistant/app.py
```

The interface has a single input field. After submitting a question, the page shows:

- **Answer**: the LLM response based on the retrieved documents.
- **Sources**: links to the original judgment PDFs so the lawyer can find the exact citations.
- **Feedback**: the user can rate the answer (thumbs up/down) and leave a comment. This feeds the feedback loop.
- **Relevance evaluation**: the LLM-as-a-judge score for the answer.

The app is deployed on Streamlit Community Cloud: https://iachr-sentences-assistant.streamlit.app/

Since the app is public, there is a hard limit of 30 questions per day to prevent abuse of the API keys. The count is tracked in the database.

### 6. Monitoring

All interactions are saved in a PostgreSQL database. For deployment, the database is hosted on Supabase. To run locally, set `SUPABASE_DATABASE_URL` in your `.env`.

Initialize the database:

```bash
uv run python monitoring/db_init.py
```

The database has three tables:

- **conversations**: stores each question/answer pair along with model name, token counts, response time, cost, and timestamp.
- **feedback**: stores user feedback (score and optional comment) linked to a conversation.
- **relevance**: stores the LLM-as-a-judge relevance score and explanation for each conversation.

There is also a monitoring dashboard to visualize usage data:

```bash
uv run streamlit run assistant/dashboard.py
```

It shows metrics like total questions, average response time, cost per day, feedback distribution, and relevance scores. It also has a table with all conversations and their feedback/relevance data.

### Containerization

Docker is not used in this project. The app runs on Streamlit Community Cloud and the database on Supabase, so there was no need for docker-compose or a local container setup.
