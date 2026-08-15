# Codebase Q&A - RAG-Powered Code Assistant

A Retrieval-Augmented Generation (RAG) application that lets you ask natural language questions about Python codebases. It uses AST-based chunking to understand code structure, stores embeddings in ChromaDB for semantic search, and generates answers using the Claude API.

## Features

- **AST-Based Code Chunking** - Parses Python files into semantically meaningful chunks (functions, classes, methods, module-level code) using Python's `ast` module
- **Hybrid Search (Vector + BM25)** - Combines ChromaDB semantic similarity with BM25 keyword matching on symbol names for accurate retrieval
- **Claude-Powered Answers** - Uses Anthropic's Claude API to generate contextual answers grounded in your actual code
- **Incremental Indexing** - Tracks file hashes in SQLite so re-indexing only processes changed files
- **Conversation History** - Maintains chat sessions with context, stored in SQLite
- **Feedback & Monitoring** - Thumbs up/down rating on answers with a dashboard showing usage analytics
- **Streamlit UI** - Clean web interface with sidebar controls, chat, and analytics dashboard

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| UI | Streamlit |
| Vector Database | ChromaDB |
| Keyword Ranking | rank-bm25 (BM25Okapi) |
| Metadata Store | SQLite |
| LLM | Claude API (Anthropic) |
| Code Parsing | Python `ast` module |
| Embeddings | Sentence-Transformers (via ChromaDB default) |

## Project Structure

```
Capstone LLm/
├── app.py              # Streamlit UI - chat, feedback buttons, dashboard
├── chunker.py          # AST-based Python code chunker
├── config.py           # Configuration settings (paths, API keys, parameters)
├── db.py               # SQLite metadata store (repos, files, conversations, feedback)
├── indexer.py          # ChromaDB embedding & indexing logic
├── retriever.py        # Hybrid search (vector + BM25) + Claude Q&A engine
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── eval_golden_set.py  # 15 golden Q&A pairs for evaluation (psf/requests)
├── eval_retrieval.py   # Retrieval eval: vector vs hybrid search comparison
├── eval_llm.py         # LLM eval: system prompt comparison via Claude-as-judge
├── eval_results.md     # Retrieval evaluation results documentation
├── eval_llm_results.md # LLM evaluation results documentation
└── data/               # Auto-created at runtime
    ├── metadata.db     # SQLite database
    └── chroma_store/   # ChromaDB persistent storage
```

## Installation

### Prerequisites

- Python 3.10 or higher
- An Anthropic API key ([get one here](https://console.anthropic.com/))

### Setup

1. **Clone or navigate to the project directory:**

   ```bash
   cd "Capstone LLm"
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set your Anthropic API key:**

   Windows (PowerShell):
   ```powershell
   $env:ANTHROPIC_API_KEY = "your-api-key-here"
   ```

   Windows (CMD):
   ```cmd
   set ANTHROPIC_API_KEY=your-api-key-here
   ```

   Linux/macOS:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

   Alternatively, you can enter the API key directly in the app's sidebar.

## Usage

### Running the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

### Workflow

1. **Index a Repository** - Enter the path to a Python project in the sidebar and click "Index Repository"
2. **Ask Questions** - Type natural language questions about the code in the chat input
3. **View Context** - Expand the "Retrieved code context" section under any answer to see which code chunks were used
4. **Manage Conversations** - Create new conversations or revisit previous ones from the sidebar

### Example Questions

- "What does the `chunk_file` function do?"
- "How is the database initialized?"
- "Explain the retrieval pipeline"
- "What classes are defined in this project?"
- "How are embeddings stored and queried?"

## Architecture

### How It Works

```
User Question
     │
     ▼
┌─────────────────────┐
│  Hybrid Search      │ ── Vector similarity + BM25 keyword reranking
│  (retriever.py)     │
└────────┬────────────┘
         │ Top-K relevant code chunks
         ▼
┌─────────────────┐
│   Claude API    │ ── Generate answer with code context
│  (retriever.py) │
└────────┬────────┘
         │
         ▼
   Answer + Sources
```

### Indexing Pipeline

```
Python Files (.py)
     │
     ▼
┌─────────────────┐
│  AST Parsing    │ ── Parse into functions, classes, methods
│  (chunker.py)   │
└────────┬────────┘
         │ CodeChunk objects
         ▼
┌─────────────────┐
│  ChromaDB       │ ── Generate embeddings & store vectors
│  (indexer.py)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SQLite         │ ── Track file hashes, chunk counts, repos
│  (db.py)        │
└─────────────────┘
```

### AST Chunking Strategy

The chunker extracts semantically meaningful units from Python source:

| Chunk Type | Description |
|-----------|-------------|
| `function` | Top-level function definitions |
| `class` | Entire class bodies |
| `method` | Individual methods within classes |
| `module` | Remaining module-level code (imports, constants, assignments) |

Each chunk includes metadata: file path, line numbers, parent class (for methods), and docstrings.

## Configuration

All settings are in `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Claude model to use |
| `MAX_TOKENS` | `4096` | Max tokens in Claude response |
| `TOP_K_RESULTS` | `10` | Number of chunks retrieved per query |
| `MIN_CHUNK_LINES` | `3` | Minimum lines for a chunk to be indexed |
| `MAX_CHUNK_LINES` | `200` | Maximum lines per chunk |
| `SUPPORTED_EXTENSIONS` | `{".py"}` | File extensions to index |
| `CHROMA_COLLECTION_NAME` | `codebase_chunks` | ChromaDB collection name |

## Evaluation

The retrieval and generation components were evaluated using a golden set of 15 questions about the `psf/requests` library (see `eval_golden_set.py`).

### Retrieval Evaluation

Compared pure vector search vs. hybrid search (vector + BM25) using `eval_retrieval.py`:

| Metric | Vector Search | Hybrid Search |
|--------|--------------|---------------|
| File Hit Rate | 100.0% | 93.3% |
| Symbol Hit Rate | 66.7% | **73.3%** |
| Combined | 83.3% | 83.3% |

**Decision:** Hybrid search was chosen as the default because symbol-level accuracy (73.3% vs 66.7%) matters more for a code Q&A tool where users ask about specific functions and classes. The BM25 component matches on symbol names, file paths, and docstrings to surface the right code unit. Full details in `eval_results.md`.

### LLM Response Evaluation

Compared two system prompts via `eval_llm.py` using Claude-as-judge (1-5 scoring):

| Metric | Prompt A (Current) | Prompt B (Strict/Citations) |
|--------|-------------------|----------------------------|
| Avg Faithfulness | **2.43**/5 | 2.36/5 |
| Avg Relevance | **4.50**/5 | 4.00/5 |
| Valid Evaluations | **14/15** | 11/15 |

**Decision:** The current prompt (A) was kept as default. It scored higher on both faithfulness and relevance, and produced more reliable outputs. The stricter citation-required variant caused refusals and malformed answers in practice. Full details in `eval_llm_results.md`.

## Monitoring

The app includes built-in monitoring and feedback collection:

### Feedback Buttons

Every assistant response in the chat displays **thumbs up/down buttons** (👍/👎). Clicking one records a rating to the `feedback` table in SQLite, linked to the specific message and conversation. Once rated, the button is replaced with a confirmation indicator.

### Analytics Dashboard

The **Dashboard** tab (accessible via the tabs at the top of the main area) shows five charts:

1. **Queries Over Time** — Line chart of daily query count
2. **Feedback Breakdown** — Bar chart of thumbs up vs. thumbs down counts, plus positive rate metric
3. **Most Active Repositories** — Bar chart of query count per indexed repo
4. **Indexed Chunks per Repository** — Bar chart of total chunks stored per repo
5. **Conversation Length Distribution** — Histogram of messages per conversation with summary stats (total, average, longest)

All data is pulled from SQLite and updates in real-time as the app is used.

## Data Storage

- **ChromaDB** (`data/chroma_store/`) - Persists vector embeddings and documents for semantic search
- **SQLite** (`data/metadata.db`) - Stores:
  - Indexed repository metadata
  - File hashes (for incremental re-indexing)
  - Conversation history and messages
  - User feedback (thumbs up/down ratings)

Both are auto-created on first run. Delete the `data/` folder to reset everything.

## Limitations

- Currently only indexes Python (`.py`) files
- Requires an active internet connection for the Claude API
- Large repositories may take time to index initially

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| API key error | Set `ANTHROPIC_API_KEY` environment variable or enter it in the sidebar |
| Slow indexing | Normal for large repos; subsequent re-indexes skip unchanged files |
| Port already in use | Run `streamlit run app.py --server.port 8502` |
| Empty answers | Ensure the repository has been indexed first |

## License

This project is for educational/capstone purposes.
