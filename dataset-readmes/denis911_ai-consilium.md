# AI Consilium — Dual-Engine Consensus Research Agent

> **Spec-Driven Design (SDD)** | **Multi-Model Consensus Architecture**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Package Manager: uv](https://img.shields.io/badge/package_manager-uv-6E40C9.svg)](https://github.com/astral-sh/uv)
[![Database: DuckDB](https://img.shields.io/badge/database-DuckDB-FFF000.svg)](https://duckdb.org/)
[![UI: Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Tests: 48 Passed](https://img.shields.io/badge/tests-48%20passed-success.svg)](#-test-suite--quality-assurance)

---

## 📌 Executive Summary & Vision

**AI Consilium** is an open-source multi-model consensus research harness tailored for **solopreneurs and startup founders** acting as their own legal, accounting, and technical infrastructure teams.

### The Pain Point
Solopreneurs cannot afford $500/hr corporate retainers to cross-check architecture choices or localized tax compliance. However, relying on a single LLM response can carry blind spots, hallucinations, or biased assumptions.

### The Solution
AI Consilium transforms unpredictable LLM outputs into an **auditable multi-model consensus workflow**. Powered by **LiteLLM**, it asynchronously queries **5 frontier LLM providers** (OpenAI o3-mini, Anthropic Claude 3.5 Sonnet, Gemini 2.5 Flash, Perplexity Sonar, and DeepSeek-R1 reasoning model) with retrieved local reference context. For zero-cost local testing, it includes a 1-click fallback to 5 free models on OpenRouter (`:free`). It calculates a mathematical **Consensus Score (0–100%)** via 384-dimensional embedding distance, identifies statistical Z-score outliers, runs an LLM-as-a-Judge qualitative synthesis, renders dynamic **Mermaid.js visualizations**, logs telemetry in DuckDB, and exports structured research notes directly into a local **Obsidian vault**.

### 💡 Project Origin & Personal Motivation
While the concept of multi-LLM consensus (known in AI research as *Multi-Agent Debate (MAD)* or *Mixture-of-Agents (MoA)*) is an established architectural pattern, **AI Consilium was created out of real-world motivations:**

1. **Scratching My Own Itch:** I spent endless hours manually cross-validating code, architecture patterns, and technical decisions by copy-pasting questions across ChatGPT, Claude, and Gemini tabs back and forth. Managing scattered answers manually became unsustainable, making an automated multi-model consensus harness and local knowledge base finally inevitable.
2. **Real-World Engineering:** Synthesizing core concepts (RAG retrieval, vector search, evaluation metrics, telemetry, and LiteLLM integration) into a practical tool for daily engineering workflows.

*(For historical LLM Zoomcamp Capstone evaluation criteria and scoring matrix, see [`_docs/llm_zoomcamp_evaluation.md`](file:///c:/tmp/ai-consilium/_docs/llm_zoomcamp_evaluation.md).)*

---

## ⭐ Unique Strengths & Innovations of AI Consilium

AI Consilium goes beyond traditional single-model RAG question-answering systems by introducing a multi-model consensus harness:

- 🏛️ **Multi-LLM Consensus Engine:** Mitigates single-model hallucination risk by querying $N$ frontier LLM providers concurrently and computing an $N \times N$ pairwise cosine similarity matrix with Z-score outlier detection.
- ⚖️ **LLM-as-a-Judge Qualitative Synthesis:** Merges disparate model responses into an executive summary highlighting unanimous agreement points, explicit contradiction audit logs, and dynamic Mermaid.js workflow diagrams with automatic judge fallback chains.
- ⚡ **100% Free & Zero-Cost Developer Mode:** Features a 1-click fallback to 5 free models on OpenRouter (`:free`) and local CPU embeddings (`all-MiniLM-L6-v2`), requiring $0 API budget to test and run.
- 📂 **Native Obsidian Vault Integration:** Exports structured `.md` research notes with YAML frontmatter, tags, agreement lists, and embedded Mermaid charts directly into local knowledge bases (`OBSIDIAN_VAULT_PATH`).
- 📊 **Embedded DuckDB Telemetry & RAG:** Zero-dependency local persistence using DuckDB for both hybrid dense/sparse RAG search and execution query logging (`TIMESTAMP`, token counts, latencies, estimated costs, user ratings).
- 🧪 **Spec-Driven Software Engineering:** Built with strict Spec-Driven Design (SDD), Pydantic v2 data contracts, Hatchling, security prompt boundaries, and 48 automated unit & integration tests with 100% pass rate.

---

## 🔄 Knowledge Base Flywheel: Cold Start vs. Warm Start Modes

AI Consilium supports two flexible execution paradigms depending on whether you are starting a new research topic or working with an existing knowledge base:

```
                         +-----------------------------------+
                         |      AI CONSILIUM ENGINE          |
                         +-----------------+-----------------+
                                           |
                   +-----------------------+-----------------------+
                   |                                               |
                   v                                               v
        [❄️ COLD START MODE]                             [🔥 WARM START MODE]
  No existing vault notes found                    Vault folder contains .md notes
                   |                                               |
                   v                                               v
  User asks high-stakes queries                    Auto-scans vault via ingest.py &
  across multi-model ensemble                      indexes into DuckDB (Vector + FTS)
                   |                                               |
                   v                                               v
  Exports structured .md notes with                Grounds multi-LLM consensus
  Mermaid charts to Obsidian vault                 queries with retrieved vault notes
                   |                                               |
                   +-----------------------+-----------------------+
                                           |
                                           v
                       +---------------------------------------+
                       |    📊 RETRIEVAL EVALUATION BENCHMARK  |
                       | Calculates Hit Rate @ K & MRR @ K    |
                       | via evaluate_retrieval.py benchmark   |
                       +---------------------------------------+
```

### ❄️ Cold Start Mode (Brand New Research / Empty Folder)
- **What it is:** Ideal when you start a brand-new research topic or point `OBSIDIAN_VAULT_PATH` to an empty directory.
- **How it works:** As you ask high-stakes questions in the Streamlit UI or CLI, AI Consilium executes multi-LLM consensus scoring, synthesizes points of agreement, generates a Mermaid.js chart, and exports a structured `.md` file with YAML metadata.
- **Result:** Over days and weeks, your vault naturally populates, building a rich, organized personal knowledge base note-by-note.

### 🔥 Warm Start Mode (Existing Obsidian Vault / Folder Full of Notes)
- **What it is:** Ideal when you already have an existing Obsidian vault or a directory full of Markdown notes.
- **How it works:** You can safely point `OBSIDIAN_VAULT_PATH` to your existing vault. Running the ingestion script (`uv run python ingest.py --dir C:/ai-memory/ai-concilium`) recursively scans `.md` files, parses YAML tags and headings, computes 384-d dense embeddings (`all-MiniLM-L6-v2`), and indexes them into DuckDB (`ai_consilium.duckdb`).
### 💡 Pre-Fetch ASCII & Markdown Summarization Pattern (Cost & Consensus Integrity)

When researching high-stakes topics involving complex PDFs, contracts, financial statements, or screenshots, AI Consilium recommends the **Pre-Fetch ASCII & Markdown Summarization Pattern**:

1. **Zero-Cost Document Pre-Processing:** Rather than burning multi-modal vision API tokens across 5 separate frontier models simultaneously, users can paste complex PDFs or screenshots into standalone chat interfaces (ChatGPT, Claude, or Gemini web apps) for $0.
2. **100% Context Uniformity & Mathematical Validity:** Copy-pasting the resulting clean Markdown summary into AI Consilium's RAG context box guarantees that all 5 consensus models receive **100% identical inputs**. This eliminates representation asymmetry (where vision models see visual layouts while text models receive raw OCR text), ensuring that inter-model embedding similarity scores and Z-score outlier calculations remain strictly mathematical, unbiased, and meaningful.
3. **Optimal Context Window Size:** While frontier models support 128k–1M token context windows, the optimal range for fast multi-model consensus latency (<3s) and cost (<$0.03/query) is **500 to 2,500 words (~3,000 to 15,000 characters / ~1k–4k tokens)**.
4. **Significant API Cost Savings:** Avoids multiplying heavy multi-modal image/document payload fees across $N$ providers in parallel, keeping multi-model consensus research under **$0.02 – $0.05 per run**.

#### 📋 Recommended Copy-Paste Pre-Fetch Prompt Template:
> Copy and paste this prompt into ChatGPT, Claude, or Gemini when uploading a PDF or screenshot:
```text
Please analyze and summarize the attached document [PDF / Screenshot / File] for high-stakes decision-making. 
Output a structured Markdown summary containing:
1) Core Technical, Legal, or Financial Facts & Constraints
2) Key Numerical Values, Data Points, or Tables
3) Potential Risks, Edge Cases, or Unclear Points
Keep the summary concise (between 500 and 1,500 words) using plain text, Markdown tables, and ASCII diagrams.
```

---

## 🔒 Security, Stability & Architectural Refinements

AI Consilium incorporates production-grade engineering principles to ensure security, correctness, and reliability:

1. **Prompt Injection Boundaries (`<reference_documents>`):**
   - RAG reference context is wrapped inside `<reference_documents>...</reference_documents>` XML boundary tags with explicit instructions directing LLMs not to execute prompt overrides embedded within untrusted document text.
2. **Vault Path Traversal Protection:**
   - `ObsidianExporter` validates that target file paths resolve inside the designated vault directory (`target_file.resolve().is_relative_to(target_dir.resolve())`), preventing unsafe writes.
3. **Markdown Code Fence Escaping:**
   - Raw LLM response text containing triple backticks (` ``` `) is sanitized (`~~~`) before embedding into Markdown notes, preventing syntax corruption in Obsidian.
4. **Mermaid Syntax Validation:**
   - Generated diagram code is validated against recognized Mermaid tokens (`graph`, `flowchart`, `sequenceDiagram`, etc.) before rendering.
5. **Docker Secret Masking (`.dockerignore`):**
   - Blocks `.env`, `.git`, `*.duckdb`, `.venv`, and temporary caches from being copied into container build context.
6. **Streamlit Event Loop & Resource Isolation:**
   - Incorporates `nest_asyncio.apply()` and `@st.cache_resource` singletons for DuckDB connections and SentenceTransformer embeddings, preventing event loop conflicts, connection leaks, and duplicate memory usage.
7. **LLM Judge Fallback Chain:**
   - `LLMJudgeSynthesizer` uses a fallback chain (`Gemini 2.5 Flash` -> `o3-mini` -> `Claude Sonnet 5` -> `xAI Grok 4.5` -> `OpenRouter Free`) so qualitative synthesis succeeds even if a primary provider API is down.
8. **Dynamic API Key Detection:**
   - `LLMProviderEngine.get_effective_models()` dynamically inspects environment variables and queries only models for which active API keys exist, avoiding silent timeout errors.
9. **Z-Score Outlier Detection & Insufficient Model Warnings:**
   - Upgrades relative outlier math to statistical Z-score calculations. If fewer than 2 models respond, the UI renders a warning banner (`insufficient_responses=True`) rather than reporting a misleading 100% score.
10. **User Feedback Observability (+1 / -1 Ratings):**
    - DuckDB `query_logs` tracks thumbs up/down ratings, rendering a **User Approval Rate** metric on the Streamlit telemetry dashboard.

---

## 🏗️ System Architecture

```
                                  +-----------------------+
                                  | Local Obsidian Vault /|
                                  | Reference Documents   |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |   DuckDB RAG Engine   |
                                  | (Hybrid VSS + FTS)    |
                                  +-----------+-----------+
                                              |
                                              v
+------------------+              +-----------------------+
|  User Input Query| -----------> | Multi-Model Provider  |
|  (Streamlit/CLI) |              |  Engine (Async HTTP)  |
+------------------+              +-----------+-----------+
                                              |
                     +------------------------+------------------------+
                     |            |           |           |            |
                     v            v           v           v            v
                 OpenAI       Anthropic    Gemini     Perplexity      Grok
                     |            |           |           |            |
                     +------------------------+------------------------+
                                              |
                                              v
                                  +-----------------------+
                                  |  Hybrid Consensus &   |
                                  | Contradiction Engine  |
                                  | (Embedding + Judge)   |
                                  +-----------+-----------+
                                              |
                                   +----------+----------+
                                   |                     |
                                   v                     v
                        +--------------------+  +--------------------+
                        | Streamlit UI /     |  | Obsidian Exporter  |
                        | Audit History Tab  |  | (Human-Readable MD)|
                        +--------------------+  +--------------------+
```

---

## 📂 Project Structure

```text
ai-consilium/
├── _docs/                      # SDD Specifications & Architectural Blueprints
│   ├── mission.md              # Vision, target audience, and core pillars
│   ├── high_level_spec.md      # Detailed technical specification
│   └── knowledge_flywheel_spec.md # Flywheel design document (Cold/Warm start)
├── review/                     # Multi-Agent Code Review Specs & Analysis Reports
│   ├── claude-review.md        # Claude Structural & SonarCloud MCP review spec
│   ├── jules-review.md         # Google Jules framework & concurrency review spec
│   └── ...                     # Historical & daily versioned audit logs
├── council/                    # Core Python Package
│   ├── __init__.py
│   ├── providers.py            # Async multi-LLM API client manager
│   ├── rag.py                  # DuckDB Hybrid Vector & FTS engine
│   ├── consensus.py            # Embedding Z-score matrix & outlier detection
│   ├── synthesizer.py          # LLM-as-a-Judge with fallback chain
│   ├── exporter.py             # Obsidian Markdown & Mermaid chart exporter
│   └── telemetry.py            # DuckDB TIMESTAMP logger & user feedback ratings
├── app.py                      # Streamlit Web UI, Audit Dashboard & Feedback
├── main.py                     # CLI entrypoint
├── ingest.py                   # Bulk Obsidian Vault directory ingestion script
├── evaluate_retrieval.py       # RAG retrieval evaluation script (Hit Rate & MRR)
├── pyproject.toml              # uv project dependencies with upper bounds
├── uv.lock                     # Lockfile for reproducible builds
├── .env.example                # Environment variables template
├── .dockerignore               # Docker build isolation & secrets exclusion
├── Dockerfile                  # Multi-stage container definition
├── docker-compose.yml          # Container orchestration
└── README.md                   # Evaluator & User Documentation
```

---

## ⚙️ Quickstart Guide

### Prerequisites
- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) (recommended) or standard `pip`
- Docker & Docker Compose (optional, for containerized run)

### 1. Clone & Setup Environment
```bash
git clone https://github.com/denis911/ai-consilium.git
cd ai-consilium

# Copy environment template
cp .env.example .env
```

Edit `.env` and fill in your API keys:
```env
# Zero-Cost Free Tier (Recommended for initial testing)
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_key_here

# Or Frontier Paid Provider Keys
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
PERPLEXITY_API_KEY=your_key_here
XAI_API_KEY=your_key_here

# Local Knowledge Base / Obsidian Vault Path (Set to your local folder)
OBSIDIAN_VAULT_PATH=C:/ai-memory/ai-concilium
```

### 📁 Setting Up Your Local Obsidian Vault / Memory Folder

AI Consilium exports consensus research notes directly to your local knowledge base:
- **Windows Example:** `OBSIDIAN_VAULT_PATH=C:/ai-memory/ai-concilium`
- **macOS / Linux Example:** `OBSIDIAN_VAULT_PATH=/Users/username/Obsidian/Vault`

If the directory does not exist yet, AI Consilium automatically creates it when saving your first note!

---

### 🎨 Obsidian Mermaid CSS Magic (1-Minute Full-Width Setup)

When Obsidian renders Mermaid flowcharts, its default Markdown viewer stretches vector SVGs based on height, which can make diagram text look small on wide displays. 

To make all exported consensus flowcharts **fill 100% of your note pane** with **crisp, readable, bold text**:

1. **Open Snippets Folder:** In Obsidian, open **Settings (⚙️ bottom-left) -> Appearance -> CSS Snippets**, and click the folder icon 📁 **"Open snippets folder"**.
2. **Create CSS File:** Create a text file named **`mermaid.css`** inside that folder with this content:
   ```css
   /* Make Mermaid fill 100% width of Obsidian pane */
   .mermaid {
       display: flex;
       justify-content: center;
       width: 100%;
   }

   .mermaid svg {
       width: 100% !important;
       max-width: 100% !important;
       height: auto !important;
       max-height: 750px !important;
   }

   /* Boost node font size & weight for crisp readability */
   .mermaid .node label,
   .mermaid .nodeText,
   .mermaid .edgeLabel {
       font-size: 15px !important;
       font-weight: 600 !important;
   }
   ```
3. **Enable Snippet:** Back in Obsidian **Settings -> Appearance -> CSS Snippets**, click the 🔄 **Refresh** icon and toggle **`mermaid.css`** to **ON**.

> [!TIP]
> **Why this CSS snippet works:**
> - `width: 100% !important`: Forces SVG vectors to expand across 100% of your editor width.
> - `max-height: 750px !important`: Prevents tall multi-level flowcharts from vertical truncation.
> - `font-size: 15px !important`: Overrides default browser fonts to make decision nodes and arrow labels crisp and legible.

---

### 🔑 Zero-Cost Evaluator Setup: How to Get a Free OpenRouter API Key

To evaluate AI Consilium completely **free of charge ($0 API cost, zero credit card required)** across 5 models:

1. **Create Account:** Go to [openrouter.ai](https://openrouter.ai/) and sign up.
2. **Generate Key:** Navigate to [openrouter.ai/keys](https://openrouter.ai/keys), click **"Create Key"**, and copy your generated key (`sk-or-v1-...`).
3. **Save to `.env`:** Add `OPENROUTER_API_KEY=sk-or-v1-your-key` into your local `.env` file.
4. **Automatic Free-Tier Routing:** When only `OPENROUTER_API_KEY` is set (or when "⚡ OpenRouter $0 Free Model Tier" is toggled ON), AI Consilium automatically dispatches queries concurrently to 5 active free models:
   - ⚡ `openrouter/inclusionai/ling-3.0-flash:free`
   - 🧠 `openrouter/google/gemma-4-26b-a4b-it:free`
   - 🌐 `openrouter/nvidia/nemotron-3-nano-30b-a3b:free`
   - 💻 `openrouter/poolside/laguna-s-2.1:free`
   - 🏊 `openrouter/cohere/north-mini-code:free`

> [!NOTE]
> **Zero External API Keys for RAG & Local DuckDB Storage:** The **DuckDB RAG Engine** (`council/rag.py`) and Telemetry Logger (`council/telemetry.py`) run 100% locally using an embedded DuckDB database file (`ai_consilium.duckdb`). DuckDB automatically creates the file on first run. Database files (`*.duckdb`, `*.duckdb.wal`) are blocked by `.gitignore` to guarantee your research history and vector indices remain 100% private on your machine.

---

## 🏃 How to Run AI Consilium (Execution Commands)

### 1. Streamlit Interactive Web Application (Recommended)
Launch the full interactive web dashboard featuring live provider progress bars, interactive consensus gauges, dynamic Mermaid.js rendering, user feedback buttons, and the audit telemetry console:

```bash
# Sync dependencies
uv sync

# Launch Web UI (Access at http://localhost:8501)
# NB: please wait 20-30 sec for streamlit app to populate the screen
uv run streamlit run app.py
```

---

### 2. Command-Line CLI Interface
Execute consensus queries directly from your terminal with optional OpenRouter free tier routing, JSON output, or automated Obsidian vault export:

```bash
# Basic terminal query
uv run python main.py --query "Compare PostgreSQL vs DuckDB for desktop analytics"

# Run query using OpenRouter $0 free model tier & export note to Obsidian vault
uv run python main.py --query "Compare PostgreSQL vs DuckDB" --free-tier --export

# Run query with local DuckDB vault RAG grounding
uv run python main.py --query "Compare PostgreSQL vs DuckDB" --rag

# Output full JSON artifact payload to stdout
uv run python main.py --query "Compare PostgreSQL vs DuckDB" --json
```

---

### 3. Knowledge Flywheel: Ingesting Notes & Enabling Vault RAG (`ingest.py`)

AI Consilium implements a **Knowledge Flywheel**:
1. **Cold Start:** Perform research queries. Click **"📥 Export Note to Obsidian Vault"** to accumulate Markdown consensus notes in your local vault directory (`C:/ai-memory/ai-concilium`).
2. **Bulk Ingestion:** Once you have accumulated notes, ingest them into your persistent DuckDB vector database:
   ```bash
   uv run python ingest.py --dir C:/ai-memory/ai-concilium
   ```
3. **Hot Start (RAG Grounding):** In the Streamlit sidebar under **Engine Settings**, toggle **"🧠 Enable Vault RAG Grounding"** to **ON**. Future queries will automatically retrieve past consensus notes from `ai_consilium.duckdb` and ground the LLM panel!

> [!TIP]
> **Cold Start Default & Safety:** "Enable Vault RAG Grounding" (and the CLI `--rag` flag) is **OFF by default** so new users start clean. If toggled **ON** before running `ingest.py`, DuckDB safely returns 0 matching results without errors or prompt pollution. Toggle it **ON** once you have run `ingest.py` to unlock historical RAG grounding!

> [!IMPORTANT]
> **Cost-Conscious RAG Guardrails & Pre-Fetch Summarization Pro-Tip:**
> - **Why Context Limits Matter:** Sending massive 20–50 KB documents directly into a 5-model frontier panel will multiply API token costs by 5× and degrade response speed. To protect your wallet, AI Consilium enforces a strict cumulative **3,000 character cap (~500–750 tokens)** across all retrieved RAG snippets per query.
> - **Pro-Tip for Large Documents / Multi-Page PDFs:** If you have massive PDF specifications or multi-page documents, leave Vault RAG **OFF**. Instead, ask ChatGPT or Claude to summarize the core points into a concise 1–2 paragraph snippet first, then paste it directly into the **"📚 Optional Reference Context"** input box in Streamlit. This guarantees 100% identical, cost-efficient grounding across all 5 models without wasting API credits!

---

### 4. RAG Retrieval Evaluation Benchmark (`evaluate_retrieval.py`)
Run empirical RAG engine benchmarks calculating Hit Rate @ K and Mean Reciprocal Rank (MRR @ K):

```bash
uv run python evaluate_retrieval.py
```

> [!NOTE]
> **Evaluation Scope & Roadmap Notice:**
> - `evaluate_retrieval.py` currently runs against a synthetic baseline dataset in an **isolated in-memory DuckDB database** (`db_path=":memory:"`) to validate hybrid RRF (Vector + Keyword) retrieval accuracy without touching or mutating your local `ai_consilium.duckdb` vault index.
> - **Roadmap (Next Iteration):** Direct vault evaluation mode allowing automated relevance scoring and Hit Rate / MRR calculation against your live ingested Obsidian notes.

---

### 5. Containerized Docker Compose Deployment
Package and run the entire application inside a reproducible Docker container with persistent volume mounts for telemetry and Obsidian vault storage:

```bash
# Build and start container in 1 command
docker compose up --build
```
Access the application dashboard at `http://localhost:8501`.

---

## 💡 Frontier Model Selection & Economics Guidance

AI Consilium provides two operational model modes designed for different stages of research:

### 1. ⚡ Zero-Cost Free Model Tier (`OPENROUTER_FREE_MODELS`)
- **Ideal for:** Rapid development, dry-run testing, offline prototyping, and budget-zero experimentation.
- **Provider:** 5 verified free models on OpenRouter (`:free`) including `inclusionai/ling-3.0-flash:free`, `google/gemma-4-26b-a4b-it:free`, `nvidia/nemotron-3-nano-30b-a3b:free`, `poolside/laguna-s-2.1:free`, and `cohere/north-mini-code:free`.
- **Economics:** $0.00 total API cost.
- **Trade-off:** Free-tier endpoints may occasionally experience rate-limiting or provider queue delays during peak usage.

### 2. 🏛️ Frontier Paid Model Tier (`DEFAULT_MODELS`)
- **Ideal for:** High-stakes architectural decisions, legal/tax compliance research, contract review, and production system design.
- **Default Roster:**
  - `o3-mini` (OpenAI High-Speed Reasoning Model)
  - `anthropic/claude-sonnet-5` (Anthropic Deep Reasoning Model)
  - `gemini/gemini-2.5-flash` (Google 1M-Context Lead Judge)
  - `perplexity/sonar` (Live Web-Grounded Search Signal)
  - `xai/grok-4.5` (xAI Grok Reasoning Signal)
  - `openrouter/deepseek/deepseek-r1` (DeepSeek Reasoning Perspective)
- **Economics:** Because queries are executed asynchronously in short single-turn bursts, a typical multi-model research query costs **less than $0.02 – $0.05 per run**.
- **Recommendation:** Setting up pay-as-you-go API keys for OpenAI, Anthropic, Gemini, Perplexity, and xAI requires a tiny monthly spend (~$2–$5/month for heavy research), yielding maximum reasoning depth, zero rate limits, and professional-grade cross-validation.

---

## 🧪 Test Suite & Quality Assurance

AI Consilium features an extensive automated test suite covering unit, integration, security, stability, CLI, and end-to-end pipeline benchmarks.

```bash
# Run the complete test suite
uv run pytest
```

### Test Suite Summary:
```text
collected 48 items

tests/test_app.py .                                                      [  2%]
tests/test_basic.py ..                                                   [  6%]
tests/test_consensus.py ...                                              [ 12%]
tests/test_docker.py ..                                                  [ 16%]
tests/test_eval.py ..                                                    [ 20%]
tests/test_exporter.py ..                                                [ 25%]
tests/test_ingest.py ..                                                  [ 29%]
tests/test_main.py ...                                                   [ 35%]
tests/test_pipeline.py ..                                                [ 39%]
tests/test_providers.py ......                                           [ 52%]
tests/test_rag.py ....                                                   [ 60%]
tests/test_schemas.py .......                                            [ 75%]
tests/test_security.py ...                                               [ 81%]
tests/test_stability.py ..                                               [ 85%]
tests/test_synthesizer.py .....                                          [ 95%]
tests/test_telemetry.py ..                                               [100%]

============================= 48 passed in 32.29s =============================
```

### 🛡️ Multi-Agent Dual-Review & Quality Assurance Pipeline

Every feature and bug fix in AI Consilium passes through a rigorous **5-Step Dual-Review Pipeline** involving two independent AI reviewer personas, SonarCloud MCP static analysis enrichment, and automated test validation:

```
 1. Coding & Implementation    --->  Primary coding AI (Gemini 3.6 Flash / Antigravity) implements feature requests based on groomed issues.
 2. Automated Test Battery     --->  Full test suite (`uv run pytest`) is executed to ensure zero regressions before committing to `main`.
 3. SonarCloud & CI Scan       --->  3–5 min background window: SonarCloud scans commit; non-source noise files (`uv.lock`, `*.duckdb`) excluded.
 4. Dual-Review Audit Phase    --->  Code audited by specialized reviewer personas (Claude 3.5 Sonnet & Google Jules) with optional Sonar MCP data.
 5. Risk-Based Consensus Groom --->  Issues with `risk_score >= 3` or flagged by both reviewers are groomed into High-Priority GitHub Issues.
```

#### 🎭 Specialized Reviewer Personas & Noise Reduction Matrix

Rather than having reviewers search for generic bugs redundantly, each reviewer operates under a distinct domain rubric to maximize depth and eliminate noise. Every report includes a YAML frontmatter header (`risk_score: 1-5`, `breaking_changes`, `effort_estimate`, `sonar_status`):

| Reviewer Agent | Instruction Spec File | Target Log Location | Specialized Rubric & MCP Integration |
| :--- | :--- | :--- | :--- |
| **Claude 3.5 Sonnet** | [`review/claude-review.md`](file:///c:/tmp/ai-consilium/review/claude-review.md) | `review/YYYY-MM-DD-code-review-Claude-N.md` | **Structural Architecture, Security & Test Rigor:** Modular design, security vulnerability audit (path traversal, prompt/SQL injection via SonarCloud MCP `denis911_ai-consilium`), docstring completeness, and test assertion depth. |
| **Google Jules** | [`review/jules-review.md`](file:///c:/tmp/ai-consilium/review/jules-review.md) | `review/YYYY-MM-DD-code-review-jules-N.md` | **Framework, Concurrency & Boundary Performance:** Native Python 3.11+ patterns, DuckDB/LiteLLM alignment, multi-process resource lock safety, boundary/type safety, and algorithmic complexity. |

#### 🗳️ Risk-Based Consensus Grooming Rule
- **High-Priority Critical Items:** Any logic, security, performance, or structural flaw with `risk_score >= 3` or flagged by **both reviewers** is groomed into a high-priority GitHub issue for immediate resolution.
- **Lower-Priority Quality Refinements:** Single-reviewer nitpicks or low-risk items (`risk_score < 3`) are groomed as lower-priority backlog refinements.

---

## 🛠️ Spec-Driven Design (SDD) Methodology

This project strictly adheres to **Spec-Driven Design (SDD)** principles:
1. **High-Level Specs First:** Specs are defined, reviewed, and locked in before writing implementation code.
2. **Auditable Requirements:** Every feature maps directly to a specification file in `_docs/`.
3. **Automated Testing & DoD:** Definition of Done requires 100% unit test pass rates and empirical verification before landing features.

---

## 🐶 Dogfooding AI Consilium: Verify Our Key Architecture Decisions

We built **AI Consilium** by dogfooding our own consensus engine to evaluate every core architectural trade-off!

If you want to see **AI Consilium** in action and experience its practical value firsthand, try running these benchmark queries in the **Streamlit Web UI** (`app.py`) or **CLI Mode** (`main.py`):

| Architecture Decision Under Audit | Benchmark Consensus Query to Try | Winning Architecture Choice |
| :--- | :--- | :--- |
| **1. Embedded RAG DB** | `"Compare embedded DuckDB (VSS + FTS) vs PostgreSQL (pgvector) for zero-dependency local desktop RAG search"` | **DuckDB:** Zero server setup, fast in-process hybrid search (`vss` + `fts`), 100% local data privacy. |
| **2. Multi-Model Provider Engine** | `"Compare LiteLLM with OpenRouter fallback vs LangChain for asynchronous multi-LLM consensus querying"` | **LiteLLM:** Lightweight, clean async `litellm.acompletion()` with 1-click $0 OpenRouter free model fallback. |
| **3. Offline Embedding Engine** | `"Compare local SentenceTransformers (all-MiniLM-L6-v2) vs OpenAI text-embedding-3-small for local CPU RAG cost and privacy"` | **SentenceTransformers:** $0 API fees, 384-d dense vectors, fast offline CPU inference (<50ms). |
| **4. Note Export & Visualizations** | `"Compare Obsidian Markdown vault storage with Mermaid.js vs cloud Notion API for local-first knowledge bases"` | **Obsidian + Mermaid.js:** Clean Markdown with YAML frontmatter, zero vendor lock-in, dynamic chart rendering. |

---

## ⚠️ Legal & Usage Disclaimer

> **For full terms, see [`DISCLAIMER.md`](file:///c:/tmp/ai-consilium/DISCLAIMER.md)**

1. **Hobby Project / Personal Brainstorming Use Only:** AI Consilium is a non-commercial, personal hobby project created to assist with personal research productivity and brainstorming. Commercial or industrial deployment is prohibited.
2. **Statistical Ensembling Tool (No Guarantee of Truth):** This software acts as a statistical ensembling and outlier detection harness over third-party LLM APIs. It does **not** guarantee objective truth beyond the probabilistic outputs of underlying models.
3. **Complete Waiver of Liability:** The author and contributors waive all responsibility and liability for direct, indirect, financial, or consequential damages resulting from the use or misuse of this software. Users use this tool strictly at their own risk and agree not to seek financial compensation under any legal theory.
4. **Prohibited High-Risk & Hazardous Uses:** Use in weapons systems, military operations, hazardous chemical processing, medical diagnosis, aviation, or technologies that could cause physical harm or loss of human life is strictly prohibited.
5. **Not Financial, Legal, or Investment Advice:** This tool is **not** an investment advisor or stock trading engine and cannot evaluate financial instruments. Outputs do not constitute licensed legal, accounting, tax, or financial counsel.

### 🧪 Try it in CLI mode right now:
```bash
uv run python main.py --query "Compare embedded DuckDB (VSS + FTS) vs PostgreSQL (pgvector) for zero-dependency local desktop RAG search" --free-tier --export
```
*(This asynchronously queries 5 free models concurrently, calculates the numerical Consensus Score, generates a Mermaid.js diagram, and exports a formatted note directly to your local vault folder!)*
