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

## 5. Retrieval
The system uses a **Hybrid Search + CrossEncoder Reranking** strategy:
1. **Heading-based Chunking**: Documents are split into chunks based on Markdown headings (e.g., `## Authentication`, `## Configuration`) rather than arbitrary paragraphs.
2. **Hybrid Search**: The user's rewritten query is executed against Elasticsearch using both sparse (BM25 keyword) and dense (k-NN vector) search to retrieve the top 30 candidate chunks.
3. **Aggregation**: Chunks are grouped and aggregated by their `server_id` to form complete contextual profiles for each candidate server.
4. **Reranking**: The aggregated server profiles are paired with the user's query and scored by the CrossEncoder to return the Top 5 most relevant unique servers.

---

## 6. RAG Flow
The LLM integration operates in two strict phases to ensure high-quality, grounded recommendations:
1. **Query Rewriting**: The user's natural language input (plus selected constraints like "Local Execution") is rewritten by Gemini into a dense, keyword-rich search query optimized for Elasticsearch.
2. **Strict Grounded Generation**: Gemini is provided with the Top 5 aggregated server documents. It is strictly instructed via system prompt to **only** recommend servers present in the context, and to explicitly state "Not documented" if a capability or security property is missing from the evidence.

---

## 7. Evaluation & Monitoring

### Retrieval Benchmark (50 Stratified Semantic Queries)
*We evaluated retrieval performance by fetching exactly 30 candidates for each method before reranking, and scoring the Top-5 unique servers.*
- **Vector Search**: Hit@1: 0.180 | Hit@5: 0.380 | MRR: 0.276 *(Best Performer)*
- **Hybrid + CrossEncoder**: Hit@1: 0.100 | Hit@5: 0.300 | MRR: 0.177
- **Keyword Search**: Hit@1: 0.100 | Hit@5: 0.180 | MRR: 0.149
- **Hybrid Search**: Hit@1: 0.080 | Hit@5: 0.180 | MRR: 0.141

*Note: Vector Search outperforms other methods on this dataset because the queries were deliberately designed to be highly verbose and semantic without exact server names.*

### LLM-as-a-Judge Evaluation (gemini-3.5-flash)
*Results based on 20 stratified cases, graded specifically on evidence-groundedness and constraint satisfaction.*
- **Relevance**: 3.45/5.0
- **Groundedness**: 1.35/5.0 *(Note: The system aggressively scores down if the LLM hallucinates constraints not present in the chunk. We also observed several `503 UNAVAILABLE` API rate-limits dropping the average).*
- **Constraint Satisfaction**: 3.40/5.0
- **Usefulness**: 3.65/5.0

---

## 8. LLM Evaluation (LLM-as-a-Judge)
To evaluate the final generation quality, we use `llm_eval.py` where Gemini acts as an expert judge evaluating its own RAG pipeline outputs on 4 criteria (Scale 1-5):
- **Relevance**: Does the server solve the problem?
- **Groundedness**: Are claims strictly based on the provided evidence?
- **Constraint Satisfaction**: Were constraints (e.g., Local only) respected?
- **Usefulness**: Was the format strictly adhered to?

*(Run `python src/evaluation/llm_eval.py` with your `GEMINI_API_KEY` to populate these exact metrics).*

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
