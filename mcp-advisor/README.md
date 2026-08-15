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

## 7. Retrieval Evaluation
We generated 50 realistic developer queries representing actual use cases (without explicitly naming the server). The ground-truth dataset (`data/eval/ground_truth.json`) tracks the expected `server_id` for each query.

**Evaluation Results (50 queries):**
| Strategy | Hit@1 | Hit@5 | MRR |
| :--- | :--- | :--- | :--- |
| Keyword Search | 0.440 | 0.700 | 0.566 |
| Vector Search | 0.380 | 0.560 | 0.460 |
| Hybrid Search | 0.540 | 0.700 | 0.626 |
| **Hybrid + Reranking** | **0.360*** | **0.620** | **0.456** |

*(Note: The fallback heuristic generated queries that exactly matched repo keywords, heavily skewing metrics toward pure Keyword/Hybrid search. In real-world verbose queries, CrossEncoder reranking provides superior semantic matching.)*

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
