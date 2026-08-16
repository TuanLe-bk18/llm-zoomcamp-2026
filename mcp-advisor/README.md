# MCP Advisor: RAG-based Model Context Protocol Recommendation System

## 1. Problem
As the Model Context Protocol (MCP) ecosystem grows, developers struggle to find the right MCP server for their specific needs. Manually browsing registries or Github repositories is time-consuming, and keyword searches often fail to capture complex constraints (e.g., "I need local browser automation without relying on a cloud API key").

**MCP Advisor** solves this by providing a Retrieval-Augmented Generation (RAG) application that understands natural language requirements, searches through actual MCP server documentation, and recommends the best-fit servers based strictly on retrieved evidence.

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

## 5. Retrieval Strategy (First-Stage Optimization)
After rigorous diagnostic benchmarking, we identified that standard Top-30 chunk retrieval suffers from significant "Candidate Generation Failure" (failing to retrieve the correct server into the reranking pool). To solve this, the system uses **Oversampling + Server-level RRF Fusion**:
1. **Heading-based Chunking**: Documents are split into chunks based on Markdown headings (e.g., `## Authentication`, `## Configuration`).
2. **Vector Oversampling**: Retrieves Top-200 chunks via dense vector search (k-NN) and deduplicates them to find the Top-50 unique servers.
3. **BM25 Oversampling**: Retrieves Top-200 chunks via sparse keyword search and deduplicates them to find the Top-50 unique servers.
4. **Reciprocal Rank Fusion (RRF)**: Merges the two server lists at the server level (k=60) to produce a highly robust Top-5 candidate list for the LLM.

*(Note: CrossEncoder reranking was evaluated but ultimately discarded as it introduced 7x latency without significantly improving MRR@5 on this specific dataset).*

---

## 6. RAG Flow
The LLM integration operates in two strict phases to ensure high-quality, grounded recommendations:
1. **Query Rewriting**: The user's natural language input (plus selected constraints like "Local Execution") is rewritten by Gemini into a dense, keyword-rich search query optimized for Elasticsearch.
2. **Strict Grounded Generation**: Gemini is provided with the aggregated server documents. It is strictly instructed via system prompt to **only** recommend servers present in the context, and to explicitly state "Not documented" if a capability or security property is missing from the evidence.

---

## 7. Evaluation & Metrics

### Dataset & Coverage
- **Corpus**: Rebuilt to cover 3243 / 3391 registered servers (95.64% success rate).
- **Benchmark Set**: 60 strictly frozen, realistic user queries (Independent Validation v1), categorized into `simple_intent`, `constraint_heavy`, and `ambiguous_realistic`. Includes 7 abstention "no match" queries to test hallucination resistance.

### First-Stage Retrieval Optimization
Through our diagnostic benchmark, we evaluated several candidate generation configurations. By moving from standard Hybrid search to **Oversampling + RRF Fusion**, we achieved:
- **Candidate Recall@50**: ~68% (A 2x improvement over the baseline 34%).
- **Hit@5**: 22.6%
- **MRR@5**: 0.122
- **Latency**: ~69ms (p50)

*Limitations*: While RRF effectively pushes relevant servers up the ranking (especially for constraint-heavy queries), **ambiguous queries** remain a significant limitation, often failing to recall the correct server in the Top 50 pool.

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
