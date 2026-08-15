# Dutch Reading Assistant

LLM Zoomcamp capstone project. A RAG + agent application for practicing Dutch reading at an A1-A2
level: it surfaces real, current Dutch news for a learner to read, answers their questions about it
using grounded lookups (a real dictionary, a real encyclopedia) instead of the model's own guesses, and
quizzes them on what they just read.

## The problem

This app is a **reading companion**: it surfaces real, current,
simple-register Dutch text (not synthetic exercises), and grounds any explanation it gives in actual
retrieved sources rather than the model's own (possibly wrong, possibly hallucinated) knowledge.

**Target user:** an A1-A2 Dutch learner who wants daily reading practice with support for unfamiliar
words and background concepts, plus a comprehension check.

## Data sources

| Source | Access | Role |
|---|---|---|
| [NOS Jeugdjournaal](https://jeugdjournaal.nl) | RSS feed (`feeds.nos.nl/jeugdjournaal`) | Reading material. Short, current, simple-register Dutch news for children |
| [WikiKids](https://www.wikikids.nl) | MediaWiki API | Background knowledge base for the `search_background` tool |
| [Wiktionary (NL)](https://nl.wiktionary.org) | MediaWiki API | Grounded dictionary lookups for the `lookup_word` tool |

Only the RSS title/summary is used from NOS. WikiKids ingestion is scoped to 6 categories (Dieren, Natuur, Geschiedenis, Aardrijkskunde, Sport, Wetenschap), not its full ~49k articles.

## How it works

```
Ingestion (NOS RSS + WikiKids API + Wiktionary API, on a schedule)
        ↓
Vector store (pgvector) + keyword index (minsearch) + hybrid (RRF)
        ↓
Reading session (Streamlit): 5 random recent articles, pick one
        ↓
Agent, routes each question to:
    • lookup_word         (grounded dictionary lookup, Wiktionary)
    • search_background   (semantic retrieval over WikiKids)
    • no tool             (answer directly — article is already in context)
        ↓
Quiz generation (6 MCQs, grounded in the article) → grading
        ↓
Logging (chat, quiz responses, feedback, token usage) → monitoring dashboard
```

The reading pane itself is **not** agentic, it's a static pull from the vector store, keeping cost/latency down. Quiz generation is a separate, deterministic call. `lookup_word` never fabricates a definition: if Wiktionary has no entry, it returns `found: false` and the agent has to say so before it's allowed to answer from its own knowledge.

## Evaluation criteria mapping

| Rubric line | Where it's satisfied |
|---|---|
| Problem description | This section, above |
| Retrieval flow | `rag/tools.py` (`search_background`, grounded in `rag/retriever.py`) + `rag/agent.py` (tool-calling loop). Both a knowledge base and an LLM are used |
| Retrieval evaluation | `eval/retrieval_eval.py`. Minsearch vs pgvector vs hybrid, crossed with 3 chunk sizes; winner written to `retrieval_config.yaml` and actually read by `rag/retriever.py`/`ingestion/chunk.py` at runtime, not just reported |
| LLM evaluation | `eval/llm_eval.py`. 3 quiz-generation prompt variants (`rag/prompts.py`), scored by an external judge (`gpt-4o-mini`, a different provider than the Groq model being evaluated); see Evaluation results below |
| Interface | Streamlit app (`app/streamlit_app.py`) |
| Ingestion pipeline | `ingestion/run_ingestion.py`, automated on a schedule via the `cron` service in `docker-compose.yml` (`ingestion/run_ingestion_loop.py`) |
| Monitoring | `app/pages/1_dashboard.py. 6 charts — plus 👍/👎 feedback collection wired into the chat UI |
| Containerization | `docker-compose.yml`. Postgres, app, and cron, all three services |
| Reproducibility | See Setup below; dependency versions pinned via `uv.lock` |
| Best practices: hybrid search | `rag/retriever.py:HybridRetriever` (reciprocal rank fusion over minsearch + pgvector), included as a third arm in `eval/retrieval_eval.py` |

Supporting signal not directly scored by the rubric: `eval/routing_eval.py` (tool-choice accuracy against hand-labeled examples in `eval/golden_routing.json`).

## Evaluation results

### Retrieval (`eval/retrieval_eval.py`)

`eval/golden_retrieval.json` has 30 hand-written Dutch questions, each paired with the WikiKids article
title(s) that should answer it, e.g. `{"query": "Wat veroorzaakt een aardbeving?", "relevant_titles":
["Aardbeving"]}`. Each query is run through 3 search methods at 3 chunk sizes (128/256/512 words, ~15%
overlap, 9 combinations total), scored two ways:

- **Hit Rate@5** — did the correct article show up *anywhere* in the top 5 results? (yes/no per query,
  averaged)
- **MRR (Mean Reciprocal Rank)** — *where* did it rank? Rank 1 scores 1.0, rank 3 scores 1/3 ≈ 0.33, not  in the top 5 scores 0, averaged across all 30 queries.

Hit Rate answers "did we find it at all"; MRR answers "did we put it first."

| Backend | Hit Rate@5 | MRR | (all 3 chunk sizes) |
|---|---|---|---|
| pgvector (dense) | 1.000 | 1.000 | tied across all chunk sizes |
| minsearch (keyword) | 0.967 | 0.967 | tied across all chunk sizes |
| hybrid (RRF fusion) | 1.000 | 0.617–0.686 | worse MRR than pgvector alone |

**Winner: pgvector, 128-word chunks** (smallest candidate, tie-broken first among equal MRR=1.0 results).

**pgvector selection**: semantic similarity finds the right article and ranks it #1 for all 30 queries.

**minsearch missed one**: it missed a query whose wording didn't share enough vocabulary with the target article's text.

**chunk size didn't matter**: with only ~120 short WikiKids articles, most fit inside a single
chunk regardless of size. All three sizes tied at MRR=1.0 for pgvector, so the code just kept the first one it tried (128).

**hybrid did *worse***: RRF (reciprocal rank fusion) combines the keyword ranking and the dense ranking by **rank position only**, ignoring how confident each method was: each list contributes `1/(60 + rank)` points to whatever article appears at that rank, and the points get summed across both lists. pgvector puts the correct article at rank 1 with high confidence, but minsearch (weaker) might put some *other*, wrong article at rank 1 too. RRF has no way to know pgvector's rank-1 pick is more trustworthy than minsearch's rank-1 pick; it just adds up "1st place" credit from both lists equally. So a wrong article that keyword search liked can out-score the right article that only dense search liked strongly. Hit Rate@5 stayed perfect (the right article was still *somewhere* in the combined top 5), but it got knocked down from rank 1 to rank 2-3 on average, hence MRR dropping to 0.62–0.69. Hybrid is kept in the eval and in `rag/retriever.py` as a usable option.

### Routing (`eval/routing_eval.py`, supporting signal, not directly rubric-scored)

18 hand-written questions, each with an expected tool (`lookup_word`, `search_background`, or none: meaning "answer directly from the article"). The real agent runs for each one, and we check whether it
picked the expected tool. **77.8% accuracy (14/18)**. The 4 misses are ambiguous edge cases
where it could be either a word-definition question (`lookup_word`) or a background-knowledge question (`search_background`).

### LLM / quiz (`eval/llm_eval.py`)

10 real NOS articles, 3 slightly different system prompts for quiz generation (`rag/prompts.py`), each
resulting quiz judged 1-5 on three criteria (groundedness, clarity, level-appropriateness) by a
*different* model (`gpt-4o-mini`). All 30
generations scored a perfect 5/5/5 — `{'v1': 5.0, 'v2': 5.0, 'v3': 5.0}`. That means, for this article
set, all three prompt variants produced quizzes the judge considered equally excellent. `v1` (the simplest variant) is kept as `DEFAULT_QUIZ_PROMPT_ID`.

## Setup

Requires [uv](https://docs.astral.sh/uv/), Docker Desktop, a [Groq API key](https://console.groq.com/keys) (free tier), and an OpenAI API key (only if you want to re-run the LLM eval).

### Option A: fully containerized

```bash
cp .env.example .env   # fill in GROQ_API_KEY (OPENAI_API_KEY only needed for eval/llm_eval.py)
docker compose up --build
```

This starts Postgres+pgvector, runs DB migrations, starts the Streamlit app on
[localhost:8501](http://localhost:8501), and starts a `cron` container that ingests fresh content every 6 hours. First build is slow (several minutes) since `sentence-transformers`/`torch` are large dependencies.

### Option B: local Python, containerized Postgres only

```bash
uv sync
cp .env.example .env
docker compose up -d postgres
python -m db.run_migrations
python -m ingestion.run_ingestion    # one-off manual ingestion
streamlit run app/streamlit_app.py
```

### Re-running the evaluations

```bash
python -m eval.retrieval_eval   # writes retrieval_config.yaml with the winning backend/chunk size
python -m eval.routing_eval     # tool-routing accuracy (supporting signal)
python -m eval.llm_eval         # needs OPENAI_API_KEY; writes the winning quiz prompt into rag/prompts.py
```

## Example usage

- **Word lookup**: "Wat betekent het woord duurste?" → routes to `lookup_word`, answers grounded in a   real Wiktionary definition (or says explicitly if the word isn't found there).
- **Background question**: "Wat is de Tilburgse kermis?" → routes to `search_background`, searches the   WikiKids index and says so if nothing relevant is found.
- **Article-only question**: "Waar gaat dit artikel over?" → answered directly from the article already in context, no tool call.
- **Quiz**: generates 6 grounded multiple-choice questions from the article just read, grades your answers, and explains each correct answer with a reference back to the text.

## Screenshots

**Article selection**: the home screen, with usage instructions and 5 random recent articles to pick from:

![Article selection](static/Screenshot_03.png)

**Reading + chat**: the article in full, with the hover hint showing what kinds of questions the chat accepts:

![Reading an article with the chat hint visible](static/Screenshot_04.png)

**Grounded word lookup**: a question routed to `lookup_word`, with the tool trace expanded and 👍/👎 feedback available on the reply:

![Chat exchange with a tool call and feedback buttons](static/Screenshot_02.png)

**Quiz**: 6 grounded multiple-choice questions generated from the article just read:

![Quiz screen with multiple-choice questions](static/Screenshot_01.png)

**Monitoring dashboard**: charts built from the logged sessions, chat messages, quiz responses, and feedback:

![Monitoring dashboard charts](static/Screenshot_05.png)


## Repository structure

```
app/          Streamlit UI (reading pane + chat + quiz) and the monitoring dashboard
rag/          Agent loop, tools, retrievers, prompts, quiz generation
ingestion/    NOS/WikiKids/Wiktionary fetchers, chunking, embedding, ingestion orchestration
db/           SQLAlchemy models, schema (init.sql), migrations, CRUD helpers
eval/         Retrieval / routing / LLM evaluation harnesses and golden datasets
docker-compose.yml, Dockerfile, Dockerfile.cron    Full containerized deployment
```
