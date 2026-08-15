# AI-Philosopher: Multi-Author RAG System 🏛️

A production-ready RAG application that serves as an AI Mentor. It provides grounded philosophical and existential advice by drawing context from diverse historical and modern personas (Marcus Aurelius, Friedrich Nietzsche, Seneka and others).

Chat is available at https://ai-philosopher-chat.streamlit.app/

Dashboard monitoring is available at https://ai-philosopher-dashboard.streamlit.app/

---

## 1. 🎯 Problem Description
Modern life exposes people to burnout, stress, and complex decision-making. Philosophy and sharp life wisdom offer tools for maintaining clarity of mind. 
This project implements a modular **Hybrid RAG System** that translates modern user queries into core abstract concepts or characteristic slang, retrieves the most relevant context from selected authors, and generates direct, context-grounded responses without unnecessary fluff.

---

### Philosophical Schools & Authors

#### 1. Stoicism
* **Marcus Aurelius** — *Meditations*
* **Seneca** — *Letters from a Stoic* (*Epistulae Morales ad Lucilium*)

#### 2. Existentialism
* **Friedrich Nietzsche** — *Thus Spoke Zarathustra*
* **Søren Kierkegaard** — *The Sickness Unto Death*

#### 3. Life Philosophy
* **Jason Statham** — *Quotes & Aphorisms*

#### 4. Marginalism / Outcast Philosophy
* **Arthas (Papich)** — *Quotes & Iconic Sayings*

## 2. 🛠️ Tech Stack & Architecture


The codebase is structured into clean, decoupled modules (`ingest.py`, `rag.py`, `app.py`, `dashboard.py`):
* **Language & Manager:** Python 3.10+, `uv` (fast dependency management).
* **LLM (Generation):** Google `gemini-3.1-flash-lite` (via OpenAI-compatible API client).
* **Embedder:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
* **Search / Vector Store:** `minsearch` (Hybrid BM25 + Vector Search with metadata filtering).
* **Ranking:** Reciprocal Rank Fusion (**RRF**) combining dense and sparse search scores.
* **UI & Analytics:** `streamlit` (Dual-service: Chat App & Observability Dashboard).
* **Monitoring:** `OpenTelemetry` + local SQLite database (`traces.db`).
* **Automation & Testing:** `Makefile`, `pytest`.

![Graph TD](data/pics/image-graph.png)

```markdown
### 💡 Important switch:  Query Rewriting
Standard vector search fails on idiomatic queries. Our pipeline automatically routes and rewrites modern everyday problems into persona-matched search terms:
* **User Query:** *"I crashed my car today, how should I react?"*
* **Rewritten Concept (Marcus Aurelius):** *"loss of external material goods and practicing emotional equanimity..."*
* **Result:** Precise retrieval of relevant Stoic passages without modern vocabulary noise.
```
---

## 3. 🔄 Data Pipeline & ETL
* **Strategy Pattern ETL:** Uses custom strategy-based parsing (`AUTHOR_PARSER_MAP` in `prepare_data.py`) tailored to each author's format:
  * **Philosophers:** Parsed with `RecursiveCharacterTextSplitter`.
  * **Quotes (Statham for example):** Regex-cleaned to strip list indices, win-rates, and quote symbols.
  * **Raw files** are txt located in `data/source` with naming `Name_Book_School.txt` separated by `_`
* **Storage:** Extracted chunks and pre-computed embeddings are serialized to `data/processed/knowledge_base.pkl` for fast, zero-ML initialization during container startup (`@st.cache_resource`).
* **Ground Truth Dataset Creation:** To evaluate retrieval quality on historical texts (e.g., Marcus Aurelius, Zarathustra), a custom ground-truth dataset was manually curated (`data/ground_truth/...`). For each representative text chunk/quote, realistic user queries—ranging from modern everyday problems to philosophical inquiries—were written and paired with the exact target `chunk_id`.

---

## 4. 📊 Evaluation & Benchmarking

We evaluated retrieval strategies on human-curated Ground Truth datasets using **Hit Rate@5** and **MRR@5**, followed by an **LLM-as-a-Judge** assessment.

### Retrieval Metrics
| Dataset / Author | Strategy | Hit Rate@5 | MRR@5 | Key Insight |
| :--- | :--- | :---: | :---: | :--- |
| **Marcus Aurelius** | Text Search (BM25) | 38.46% | 0.2788 | Keyword baseline |
| | Vector Search (MiniLM) | **46.15%** | 0.2225 | Highest recall |
| | **Hybrid Search (RRF)** | 38.46% | **0.3462** | **Best precision (highest MRR)** |
| **Zarathustra** | Text Search (BM25) | **71.43%** | 0.3224 | Strong keyword matching |
| | Vector Search (MiniLM) | 38.10% | 0.2952 | Weak on archaic terms |
| | **Hybrid Search (RRF)** | 61.90% | **0.4071** | **Best overall ranking** |

> **Key Takeaway:** Hybrid Search with RRF consistently yields the highest **MRR**, ensuring the most precise chunk is positioned at Rank 1 for LLM generation.



### LLM-as-a-Judge Evaluation
Using `gemini-3.1-flash-lite` as a judge to verify context relevance:
* **Marcus Aurelius Test Set:** 13/13 RELEVANT (100% precision)
* **Zarathustra Test Set:** 20 RELEVANT, 0 PARTLY, 1 NON_RELEVANT

---

## 5. 👁️ Observability & Feedback Loop
* **Tracing:** `RAGPipeline` captures spans for query rewriting, hybrid retrieval, and LLM generation using `OpenTelemetry`. Exact token usage and cost estimations are extracted from response metadata.
* **Custom Exporter:** Traces are saved to a local SQLite database (`traces.db`) using a zero-overhead `SQLiteSpanExporter`.
* **User Feedback:** Interactive 👍 / 👎 buttons in the Streamlit UI immediately log feedback scores to the `feedback` table.
* **Analytics Dashboard:** A dedicated app (`dashboard.py`) visualizes 4 core KPIs (Total Cost, Latency, Token Usage, Rating) and 5 distribution charts.

---

## 6. 🐳 Containerization & Optimization
* **Docker Compose:** Spawns two isolated services: `chat` (port 8501) and `dashboard` (port 8502).
* **Gigabyte-level Image Optimization:** Separated heavy ML dependencies from pure analytics. By switching to CPU-only PyTorch and cached BuildKit mounts (`uv`), total container image size was reduced from **~14 GB to ~3.4 GB**.
* **Persistence:** Named volumes keep SQLite traces (`traces.db`) and precomputed vector data intact across container restarts.
* **Access** deployed on remote server and avaliable by URL https://ai-philosopher-chat.streamlit.app/ and https://ai-philosopher-dashboard.streamlit.app/

---

## 7. 🚀 Quick Start

1. Clone the repository, cd ai-philosopher and set your GEMINI_API_KEY* by creating .env file:
2. `cd ai-philosopher`
3. create `.env` with gemini key
4. Auto version: `make up`
5. Manually you may install dependencies rapidly using uv:

   `uv venv'

   `.venv\Scripts\activate`

   `make install`
6. Prepare the knowledge base (runs ETL & builds indices):
   `make prepare`
7. Run tests:
   `make test`
8. Start the Application and Dashboard via Docker Compose:
   `make up`

If you face some problems with making venv, you may just `make up` and 2 services will work at certain ports.

*Note: The app will be available at http://localhost:8501 and the dashboard at http://localhost:8502 (or as configured in docker-compose.yml).*

To stop the services, run:
`make down`

*GEMINI provides free API tier 

Just follow  https://aistudio.google.com/api-keys

And put your GEMINI_API_KEY="..." whereever you want
![alt text](data/pics/image-api.png)

---

## 8. 📸 Screenshots  Chat + Monitoring
### Chat screenshot

- serious question - serious stoic advice
![Aurelius](data/pics/image-aurelius.png)
- modern problem and brutal truth
![Zaratustra](data/pics/image-zaratustra.png)
### Dashboard screenshots
- general metrics and last responses
![Dashboard 1](data/pics/image-dash1.png)
- performance charts (time, tokens, costs, feedbacks)
![Dashboard 2](data/pics/image-dash2.png)
- step by step span analysis
![Dashboard 3](data/pics/image-dash3.png)
![Dashboard 4](data/pics/image-dash4.png)

---

## 📋 Evaluation Rubric Checklist (For Reviewers)

| Criteria | Implementation Status | Location in Project |
| :--- | :---: | :--- |
| **Problem Description** | ✅ Yes | Section 1 & Killer Feature example |
| **RAG Flow (Hybrid + RRF)** | ✅ Yes | Section 2 & `rag.py` |
| **Retrieval & LLM Evaluation** | ✅ Yes | Section 4 (Hit Rate, MRR, LLM-as-a-Judge) |
| **Monitoring & Tracing** | ✅ Yes | Section 5 (`traces.db`, OpenTelemetry, Streamlit Dashboard) |
| **Data Ingestion & Ground Truth** | ✅ Yes | Section 3 (`prepare_data.py`, custom GT dataset) |
| **Containerization & Reproducibility**| ✅ Yes | Section 6 & 7 (`docker-compose.yml`, `Makefile`) |
| **Best Practices & Testing** | ✅ Yes | `pytest` included (`make test`), `uv` manager |
| **Cloud deployment** | ✅ Yes | `chat` https://ai-philosopher-chat.streamlit.app/ `Dashboard` https://ai-philosopher-dashboard.streamlit.app/ |



```mermaid
graph TD
    A[User Query] --> B[Query Router / Rewriter]
    B -->|Translates to Abstract Concept / Slang| C[Hybrid Retriever]
    C -->|BM25 Sparse Search| D[minsearch Index]
    C -->|MiniLM Dense Search| D
    D -->|Top Candidates| E[RRF Ranker]
    E -->|Context Chunks| F[LLM Generator Gemini]
    F --> G[Final Response + Streamlit UI]
    G -->|User Thumb Up/Down| H[SQLite Feedback DB]
    F -->|Tracing Spans| I[OpenTelemetry Exporter]
