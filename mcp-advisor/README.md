# MCP Advisor

A Retrieval-Augmented Generation (RAG) system that recommends Model Context Protocol (MCP) servers based on natural language requirements.

## 1. Problem
Developers spend significant time manually searching registries and GitHub repositories to find MCP servers. Keyword searches often fail to capture complex constraints (e.g., "I need local browser automation without relying on a cloud API key").

**MCP Advisor** solves this by searching directly through server documentation and recommending the best-fit servers based on retrieved evidence.

---

## 2. Dataset
The dataset is dynamically built from two primary sources:
1. **Primary**: Official Model Context Protocol Registry (`modelcontextprotocol/servers`)
2. **Supplemental**: Community Curated List (`awesome-mcp-servers`)

For each server, the system fetches the `README.md` directly from its source repository, ensuring the recommendation engine has access to the most accurate, up-to-date documentation regarding capabilities, installation, and security permissions.

---

## 3. Architecture
The system consists of the following components:
- **Ingestion Engine**: Python scripts to fetch registries and crawl GitHub for documentation.
- **Search Engine**: Elasticsearch (v8.11.1) running locally via Docker.
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).
- **Reranking Model**: `cross-encoder/ms-marco-MiniLM-L-6-v2`.
- **LLM / Generator**: Google Gemini API (`gemini-3.1-flash-lite`).
- **Monitoring**: Local SQLite database capturing requests, latency, and feedback.
- **UI**: Streamlit web interface with interactive feedback and a monitoring dashboard.

---

## 4. Ingestion
The ingestion pipeline is completely reproducible and automated:
1. `fetch_registry.py`: Parses the raw markdown from official and community registries to extract stable metadata (`server_id`, `name`, `description`, `repository`).
2. `fetch_readmes.py`: Uses concurrent threads to safely download the `README.md` for the top 500 servers directly from GitHub.

---

## 5. Retrieval Strategy
Standard Top-30 chunk retrieval suffers from candidate generation failure. The system uses **Oversampling + Server-level RRF Fusion** to improve recall:
1. **Chunking**: Documents are split based on Markdown headings (e.g., `## Authentication`).
2. **Vector Oversampling**: Retrieves Top-200 chunks via dense vector search (k-NN), deduplicates to Top-50 unique servers.
3. **BM25 Oversampling**: Retrieves Top-200 chunks via sparse keyword search, deduplicates to Top-50 unique servers.
4. **Reciprocal Rank Fusion (RRF)**: Merges the two server lists at the server level (k=60) to produce the Top-5 candidate list.

---

## 6. RAG Flow
1. **Query Rewriting**: The user's input (plus constraints like "Local Execution") is rewritten by an LLM into a dense search query.
2. **Grounded Generation**: The LLM evaluates the Top-5 aggregated server documents. It is instructed to only recommend servers present in the context and to state "Not documented" for missing information.

---

## 7. Evaluation

### Dataset & Coverage
- **Corpus**: 3243 / 3391 registered servers (95.64% success rate).
- **Benchmark Set**: 60 frozen user queries (Independent Validation v1), categorized into `simple_intent`, `constraint_heavy`, and `ambiguous_realistic`. Includes 7 abstention queries.

### Retrieval Performance (RRF Fusion)
- **Vector Oversample CR@50**: 67.9%
- **RRF Candidate Recall@30**: 60.4%
- **RRF Candidate Recall@50**: 64.2%
- **RRF Hit@5**: 22.6%
- **RRF MRR@5**: 0.122
- **Latency**: ~69ms (p50)

*Limitations*: Ambiguous queries remain a challenge, often failing to recall the correct server in the Top 50 pool.

---

## 8. Future Work
1. **Enriched Metadata Embeddings**: To solve the ambiguous query limitation, future iterations will concatenate the Server Name, Description, and Heading into every chunk before embedding, injecting global context into local chunk vectors.
2. **Agentic Tool Retrieval**: Moving beyond RAG, wrapping the Elasticsearch queries into an MCP tool itself so an orchestrator agent can dynamically formulate and iterate on queries.
3. **Automated Server Testing**: Dynamically spinning up Docker containers to test if an MCP server's advertised tools actually compile and run before recommending them.

---

## 9. Monitoring
The application includes a built-in monitoring module (`src/monitoring/db.py`) backed by SQLite.
- Every interaction logs the `timestamp`, `user_query`, `latency_ms`, and `recommended_server`.
- Users can provide explicit 👍 / 👎 feedback in the UI.
- The **Dashboard** tab in Streamlit visualizes Total Requests, Average Latency, Feedback Ratios, and Top Recommended Servers.

---

## 10. How to Run

1. **Clone the repository**
2. **Set your API Key**
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key"
   ```
3. **Start the system via Docker Compose**
   ```bash
   docker compose up --build
   ```
   *Note: The `init-index` container will automatically start first, wait for Elasticsearch to boot, download the registry/READMEs, and index them. The `web` interface will only start once indexing is completely finished.*
4. **Access the Application**
   Open your browser to `http://localhost:8501`.

---

## 11. Example Recommendation

**User Query**: "I need to automate local browser tasks without relying on cloud APIs."
**Authentication**: No Auth Required
**Environment**: Local execution

**System Output**:
> **Recommended:** browser-use-mcp-server
> **Why:** This server is specifically designed to control a local browser instance using the browser-use library, allowing AI agents to navigate web pages and interact with DOM elements directly on your machine without needing external cloud APIs.
> **Alternatives:** mcp-playwright
> **Authentication:** Not documented.
> **Local/Remote:** Local execution (runs browser instances on the host machine).
> **Permissions / Security:** Requires local execution environment.
> **Sources:** https://github.com/browser-use/browser-use-mcp-server
