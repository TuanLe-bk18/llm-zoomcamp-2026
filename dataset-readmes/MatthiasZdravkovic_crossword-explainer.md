# Crossword Explainer

![Crossword Explainer app](docs/screenshots/streamlit-example.png)

Crossword platforms give you the answer but never explain *why* it's the
answer. This app takes a `(clue, answer)` pair the user already has and
returns a grounded explanation of the wordplay behind it.

- It is an Explainer, not a Solver: input is `clue + answer`, not `clue` alone.
- Cryptic clues have real mechanical wordplay - anagrams,
  hidden words, charades, homophones, definition-by-example - that genuinely needs explaining.

Here's an example :

**Clue:** "Not fresh, tired joke (4)"  
**Answer:** "STALE"

* "Not fresh" → stale (like old bread)
* "tired joke" → a stale joke is a joke you've heard too many times

This project is part of the [llm-zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp/tree/main) taught by Alexey Grigorev.

## Dataset

[`mexwell/cryptic-crossword-clues`](https://www.kaggle.com/datasets/mexwell/cryptic-crossword-clues)
on Kaggle (v2 = the georgeho.org cryptic dataset), 660,613 rows, **ODbL
licensed**. Downloaded via `kagglehub`, not committed to the repo - only the
download/ingestion script is checked in.

- `nytimes` source rows are filtered out (`df[df['source'] != "nytimes"]`) —
  that subset carries has copyrights issues.
- Row shape: `clue`, `answer`, `definition`, `clue_number`,
  `puzzle_date`, `puzzle_name`, `source_url`, `source`.

**Provenance note:** Full
puzzles (grid + curated clue set) *are* copyrighted and are never
reproduced here - only individual clue/answer/definition fields from a
published, ODbL-licensed dataset. *(Not legal advice.)*  

I chose to cut down the dataset to the 200k first rows of those cryptic clues, as the memory usage became excessive. 
The resultant file is saved in [data/clues.csv](data/clues.csv)

Naturally when trying out this project, the first thing I thought about was embedding my dataset to use Vector Search, in order to do Semantic Search.

The embeddings themselves are computed once, offline, by [`utilities/embed.py`](utilities/embed.py)
- The app never runs `embed.py` itself - at ingestion time, [`utilities/fetch_embeddings.py`](utilities/fetch_embeddings.py) downloads that precomputed array from my Hugging Face dataset repo: [tiasmawip/cryptic-crossword-embeddings](https://huggingface.co/datasets/tiasmawip/cryptic-crossword-embeddings/tree/main), so anyone running this project doesn't need a GPU or wait
on embedding 200k clues from scratch.

Those embeddings match exactly the dataset of 200k rows - regenerate them with `embed.py`
whenever `data/clues.csv` changes, or the two will drift out of sync.

## Running it


**1. Environment variables** - create a `.env` in the project root (never committed):

```bash
TYPESENSE_API_KEY=<self-chosen>
OPENAI_API_KEY=<your OpenAI key>
```

You can choose anything for typesense's api key, as the project runs locally.

You have an example in [.env.example](.env.example)

**2. Start all the services** :

```bash
docker compose up -d --build
```

The whole application is ready to use after about 5 minutes — `typesense` is the
bottleneck here, since every other service depends on it. You'll also want at
least **8 GB RAM** free.

This starts:

```bash
Service: typesense
Purpose: Clue/answer knowledge base
(search)
Port: 8108
───────────────────────────────────────
Service: ingest-flow
Purpose: One-shot: downloads + indexes
the dataset
Port: —
───────────────────────────────────────
Service: postgres
Purpose: Conversations + feedback store
Port: 5432
───────────────────────────────────────
Service: db-init
Purpose: One-shot: creates Postgres
tables
Port: —
───────────────────────────────────────
Service: streamlit
Purpose: The app itself
Port: http://localhost:8501
───────────────────────────────────────
Service: grafana
Purpose: Monitoring dashboard (login:
admin/admin unless
GF_SECURITY_ADMIN_PASSWORD is set)
Port: http://localhost:3000
```

`ingest-flow` and `db-init` run to completion and exit.

**Resetting the KB** - stop the container before touching
the volume :

```bash
docker compose down
rm -rf typesense-data/*      # wipes the KB
docker compose up -d --build
```

`--build` option forces a rebuild, meaning you get a fresh dataset and application.

## Stack

- **Prefect** - a popular open-source workflow orchestration and data pipeline framework for Python. Used here for ingestion.
- **Typesense** - search/retrieval layer over the clue KB.
- **sentence-transformers** (`all-MiniLM-L6-v2`) - embeds clues for vector search.
- **OpenAI** (`gpt-5.4-mini`) - generation, and the LLM-as-judge.
- **Postgres** - primary store for conversations + feedback (see Architecture).
- **Streamlit** - the app's interface.
- **Grafana** - monitoring dashboard.
- **Docker Compose** - orchestrates every service above (see Running it).

## Architecture

Two stores, deliberately not conflated:

- **Typesense** (`crosswords` collection) - the clue/answer knowledge base, fully rebuildable
  from `flow/ingest_flow.py`. The resultant KB seats in memory, and on disk.
- **Postgres** - the primary store for everything the app produces:
  - `conversations`: `id, clue, answer, explanation, model, instructions, prompt, prompt_tokens,
    completion_tokens, total_tokens, response_time, cost, timestamp`
  - `feedback`: `id, conversation_id (FK), source ('user'|'judge'), relevance, eval_explanation,
    score, timestamp`

The ingestion and the request flows are separated. Reloading the KB once the data has been imported becomes much quicker.

Request flow: retrieve (Typesense, `answer_filtered_vector_search` - filter by exact `answer`,
rank siblings by clue-vector similarity) → generate (grounded in retrieved context) → save to
Postgres → show + live metrics → automated judge scores it → user can also 👍/👎.

## General performance of the application

Typesense is an in-memory datastore optimized for fast, low-latency retrieval. The entire search index is in-memory and a copy of the raw data seats on the disk.
The startup of the app needs up to 10 min to set up the whole indexing for text, and vector search.
The vector embedding is imported in the background in the setup which is quite heavy (200k vectors * 384 floats)  

Your computer might need at least **8 GB of RAM** for the application to run smoothly.

## Retrieval evaluation

This app takes a `clue` **and** an `answer`, not just a question - which makes evaluation
different from the course's original FAQ dataset. Evaluating retrieval on `answer` alone is
meaningless here: every row with that exact answer matches trivially, so Hit Rate and MRR would
sit near 1 regardless of search quality.

So my plan was to evaluate in multiple ways : 

1. clue only
2. clue + definition
3. vector on clue
4. vector on clue + definition
5. vector on definition

That was the initial plan. However quickly enough the reality stroke me and I noticed that indexing on 3 vector fields demands 3x times more computing time.   
*Vector on clue + definition* is a vector that is quite similar to embeddings on clue individually and definition probably, so for optimizing purposes I dropped it

I also tried **hybrid search** (Typesense's keyword + vector combo, weighted with `alpha`) and
**hybrid + reranking**. Reranking helped a bit, but not much.

All of these search for "clues similar to this clue." But `answer` is a free, exact join key - any clue sharing the same answer is a perfect grounding example. So the best fit here is
**`answer_filtered_vector_search`**: filter by exact `answer`, then rank by clue-vector
similarity.

| Approach | Hit rate | MRR |
|---|---|---|
| clue only (text) | 0.019 | 0.019 |
| clue + definition (text) | 0.193 | 0.168 |
| vector on clue | 0.372 | 0.278 |
| vector on definition | 0.146 | 0.082 |
| hybrid (text + vector) | 0.406 | 0.284 |
| hybrid + reranking | 0.411 | 0.293 |
| **answer-filtered vector** | **0.995** | **0.962** |

(200-row sample, see `notebooks/rag-test.ipynb`.)

Either way, evaluating cryptic crosswords is genuinely hard for an LLM - the wordplay needs exact
letter-level reasoning, and a model can sound confident while getting the mechanism wrong. That's
part of why the LLM-judge results below "partly relevant" rather than a clean pass/fail: the
judge is an LLM facing the same weakness it's judging.

## LLM evaluation

LLM-as-judge on a 200-row sample (`gpt-5.4-mini`, same model as generation):

| Relevance | Share |
|---|---|
| RELEVANT | 4.5% |
| PARTLY_RELEVANT | 85.5% |
| NON_RELEVANT | 10.0% |

Mostly "partly relevant," almost never a clean "relevant." In hindsight, that's the dataset
talking, not just the prompt: cryptic crosswords need exact letter-level reasoning (anagram
letters, hidden-word spans, homophones) that LLMs just aren't reliable at yet.

## Monitoring

The Monitoring on Grafana charts :
- Explanations generated over time
- Average response time (s)
- Token usage over time
- Pie charts : User feedback (👍 vs 👎) and LLM judge relevance distribution

All of those charts configuration sit in [grafana/dashboards/main.json](grafana/dashboards/main.json).

Here's an example of what you might have :

![Grafana dashboard](docs/screenshots/grafana-example.png)

## Reproducibility

Everything is pinned, not left to float:

- Python deps: [`requirements.txt`](requirements.txt) - exact versions (`streamlit==1.58.0`,
  `openai==2.43.0`, `typesense==2.0.0`, `sentence-transformers==5.6.0`, `psycopg[binary]==3.3.2`,
  `pydantic==2.13.4`, etc.), pulled straight from the environment this project was built and
  tested in.
- Base image: `python:3.14.6` ([`Dockerfile`](Dockerfile)).
- Service images: `typesense/typesense:30.2`, `postgres:17`, `grafana/grafana:11.4.0`
  ([`docker-compose.yml`](docker-compose.yml)) - no `latest` tags.
- Env vars: [`.env.example`](.env.example) documents every variable the stack needs.

To reproduce from a clean checkout:

```bash
cp .env.example .env   # fill in OPENAI_API_KEY and TYPESENSE_API_KEY
docker compose up -d --build
```
