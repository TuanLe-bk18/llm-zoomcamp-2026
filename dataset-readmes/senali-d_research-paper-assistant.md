# Research Paper Q&A

Ask questions about your own research papers and get answers backed by the exact
passage, filename and page number they came from.

Upload a PDF, the app extracts its text page by page, splits it into overlapping
chunks, embeds each chunk with a sentence-transformer model and stores the
vectors in Qdrant. Ask a question and an **agent** decides what to search for,
searches as many times as it needs, and writes an answer in which every claim
carries a marker back to the passage it came from — filename and page included,
so you can go and check it yourself.

> **Status:** end to end and running, and deployed. Ingestion, hybrid retrieval
> with re-ranking, and agentic answer generation with citations are all in
> place. Evaluation and monitoring are still empty — see [Roadmap](#roadmap).

---

## Contents

- [The problem](#the-problem)
- [The data](#the-data)
- [How it works](#how-it-works)
- [Conversation history](#conversation-history)
- [Quick start (Docker)](#quick-start-docker)
- [Walkthrough](#walkthrough)
- [Screenshots](#screenshots)
- [Configuration](#configuration)
- [Local development](#local-development)
- [Deploying to Streamlit Community Cloud](#deploying-to-streamlit-community-cloud)
- [Project layout](#project-layout)
- [Troubleshooting](#troubleshooting)
- [Evaluation criteria](#evaluation-criteria)
- [Roadmap](#roadmap)

---

## The problem

Reading a stack of academic papers, the hard part usually isn't understanding any
single one — it's remembering *which* paper said the thing you half-remember, and
on which page. Full-text search only helps if you recall the exact wording; the
phrase you remember is rarely the phrase the author used.

This project makes a personal collection of papers searchable by meaning rather
than by keyword. You ask "how do they handle class imbalance?" and it finds the
passage that discusses it, even if the words "class imbalance" never appear
together on the page.

The design constraint that shapes everything else is **traceability**. A tool that
paraphrases a paper without telling you where the claim came from is worse than
useless for research work, because you cannot verify it. So every chunk carries
its filename and page number from extraction all the way through to the answer,
and every result is shown with its source.

## The data

There is no fixed dataset — **you supply the corpus**. The app accepts:

| Format | Handling |
| --- | --- |
| `.pdf` | Text extracted per page with PyMuPDF, in reading order |
| `.txt` | Treated as a single page |
| `.md` | Treated as a single page |

Anything text-based works — arXiv preprints, lecture notes, internal reports. The
intended case is academic PDFs, which is why page numbers are preserved and why
extraction uses reading-order sorting (without it, two-column papers interleave
their columns mid-sentence and the chunks come out as nonsense).

**Scanned PDFs with no text layer will not work.** There is no OCR step; the app
reports `no extractable text (scanned PDF?)` and skips the file.

## How it works

```
                 ┌──────────────── ingestion ─────────────────┐
  upload ─────►  extract ──► chunk ──► embed dense + sparse   ─────►  Qdrant
  (PDF/TXT/MD)   per page    1000 ch   384-dim  +  BM25               "papers"
                             /200 ov                                     │
                                                                         │
  question ──►  agent ──┬──► search_papers ──► hybrid (RRF) ──► rerank ──┘
                        │         ▲                              │
                        │         └──── searches again ──────────┘
                        ▼
              answer with [S1] [S2] markers  +  the passages they point at
```

The loop is what makes it *agentic*: the model chooses the search terms, reads
what comes back, and decides whether to search again — so a question spanning
two papers becomes two searches, and a first attempt that misses gets retried
with different wording. It is not a fixed retrieve-then-answer pipeline.

| Stage | Where | What it does |
| --- | --- | --- |
| Extract | `ingestion/extract.py` | PyMuPDF, reading-order sort, one entry per page (1-based). Blank pages dropped. |
| Chunk | `ingestion/chunking.py` | 1000 chars with 200 overlap. Splits on paragraphs first, then sentences, hard-wrapping only when a single sentence exceeds a chunk. Each page is chunked independently so a chunk never spans two pages. |
| Embed | `ingestion/embeddings.py` | `all-MiniLM-L6-v2`, 384 dimensions, L2-normalized. Model loaded once per process. |
| Sparse | `ingestion/sparse.py` | BM25 term frequencies via fastembed. Qdrant applies the IDF half server-side, so weights reflect rarity across the whole collection. |
| Store | `ingestion/store.py` | Qdrant collection `papers`, named `dense` + `sparse` vectors, keyword index on `doc_id`. |
| Search | `retrieval/search.py` | Both retrievers run as prefetches in one round trip, fused with Reciprocal Rank Fusion. Optional `doc_id` filter scopes to chosen papers. |
| Re-rank | `retrieval/rerank.py` | Cross-encoder (`ms-marco-MiniLM-L-6-v2`) rescores the top 30 down to the top 5. |
| Agent | `llm/agent.py` | Tool-calling loop over `search_papers`, capped at 5 iterations. Tracks which passages the answer actually cites. |

**Why hybrid.** Embeddings are good at meaning and weak at exact tokens — an
author's surname, `BLEU`, a symbol. BM25 is the mirror image. RRF fuses by
*rank* rather than score, which is what makes it safe to combine cosine
similarity with BM25 weights; the two are not on comparable scales.

**Why re-rank.** The dense and sparse retrievers embed query and passage
separately, so they never compare the two directly. The cross-encoder reads both
at once — far more precise, and far too slow to run over the whole collection.
Hence: retrieve wide and cheap, re-rank narrow and accurate.

Each stored point carries this payload:

```python
{"doc_id": "a3f9...", "filename": "attention.pdf", "page": 4,
 "chunk_index": 17, "text": "The encoder is composed of a stack of..."}
```

`page` is what makes citations traceable — it survives chunking because pages are
chunked one at a time.

**Cleaning.** Before chunking, each page has soft hyphens stripped, words
de-hyphenated across line breaks (`repre-\nsentation` → `representation`), and
runs of blank lines collapsed. PDF text extraction produces all three constantly
and each one corrupts an embedding if left in.

**Deduplication.** A document's ID is a SHA-256 hash of its bytes, and each point
ID is a UUIDv5 of `doc_id + chunk_index`. Re-uploading the same paper therefore
overwrites its own chunks instead of duplicating them, whether the file was
renamed or not.

## Conversation history

Every turn is written to Postgres, across three tables (`history/schema.sql`):

| Table | Holds |
| --- | --- |
| `conversations` | id, title (derived from the first question), timestamps |
| `messages` | role, text, and — on assistant turns — the agent's search queries, whether it hit the iteration cap, latency, token counts and model |
| `citations` | one row per `[Sn]` the answer actually cited: marker, doc_id, filename, page and a **copy** of the passage |

Two decisions worth knowing:

- **The passage text is copied, not referenced.** Papers can be deleted or
  re-chunked; an answer's evidence must not change retroactively.
- **Citations are a table, not a JSON blob.** Grading groundedness later is a
  join over claim→passage pairs, and `citations_doc_idx` answers "which answers
  cited this paper" even after it's gone from Qdrant.

The telemetry columns aren't read by the UI yet — they're recorded now because
they can't be reconstructed later, and monitoring is the next thing to build.
Poke around with `make psql`.

The schema is applied on every start and is fully `IF NOT EXISTS`, so there's no
migration tool to run.

## Quick start (Docker)

The app is meant to run containerised. Three services, defined in
`docker-compose.yml`:

- **`qdrant`** — the vector database (`qdrant/qdrant:v1.15.1`), storage in a
  named volume so data survives restarts
- **`postgres`** — conversation history (`postgres:17-alpine`), its own named
  volume
- **`app`** — the Streamlit UI, built from the `Dockerfile`, waits for both
  datastores to report healthy before starting

**Local development uses its own Qdrant container — it never touches Qdrant
Cloud.** Only the [Streamlit Cloud deployment](#deploying-to-streamlit-community-cloud)
points at a cloud cluster, via its own Secrets. This keeps local testing and
the deployed app on completely separate data with zero setup, and matters in
particular if you're on Qdrant Cloud's free trial, which allows only one
cluster — local dev doesn't need one at all.

### Prerequisites

Docker Desktop, or Docker Engine with Compose v2. Verify with:

```bash
docker info
```

Python, the dependencies, all three models, and Qdrant itself all live inside
this stack. The only thing you must supply is an **OpenAI API key**.

### Start it

```bash
git clone <your-repo-url>
cd research-paper-assistant
cp .env.example .env      # fill in OPENAI_API_KEY
make up
```

Without `OPENAI_API_KEY` the app still starts, uploads and indexes fine — the
sidebar shows a warning and questions are refused. `.env` is gitignored and
excluded from the image, so it's never baked into a layer.

Then open:

- **App:** http://localhost:8501
- **Qdrant dashboard:** http://localhost:6333/dashboard
- **Postgres:** `localhost:5432` — or `make psql` for a prompt

If you already run Postgres locally, port 5432 will clash. Override it:
`POSTGRES_PORT=5433 docker compose up -d`. This only changes the *host* port;
the app reaches Postgres over the compose network either way.

The first build takes several minutes and produces a ~3.4GB image: it installs
PyTorch and bakes all three models (embedding, BM25, cross-encoder) in, so
nothing is downloaded at runtime — the only network call at runtime is to
OpenAI. Later builds are cached and quick.

Confirm both services are healthy:

```bash
docker compose ps    # all three should read  Up ... (healthy)
```

### Everyday commands

| Command | Raw equivalent | What it does |
| --- | --- | --- |
| `make up` | `docker compose up --build -d` | Build and start all three services |
| `make logs` | `docker compose logs -f app` | Tail the app logs |
| `make down` | `docker compose down` | Stop everything; **both volumes survive** |
| `make reset` | `docker compose down -v` | Stop and **delete both local volumes** — indexed papers *and* chat history, local only |
| `make psql` | `docker compose exec postgres psql -U rag -d rag` | SQL prompt on the history database |
| `make rebuild` | `docker compose build --no-cache app` | Rebuild the image from scratch |
| `make shell` | `docker compose exec app bash` | Shell inside the running app container |
| `make deps` | `docker compose up -d qdrant postgres` | Start only the datastores (for local dev) |
| `make help` | — | List all targets |

## Walkthrough

**1. Upload a paper.** Use the sidebar uploader — several files at once is fine.
Each upload reports what it indexed:

```
attention-is-all-you-need.pdf: 43 chunks from 15 pages.
```

Upload the same file again and it says `already indexed` instead of duplicating
it.

**2. Ask a question.** Type into the chat box. The agent picks its own search
terms, searches, and answers.

**Input:**

```
How is positional information encoded?
```

**Output:**

```
The model has no recurrence or convolution, so position has to be injected
explicitly [S1]. It adds sinusoidal positional encodings to the input
embeddings, using sine and cosine functions at different frequencies [S1].
The authors also tried learned positional embeddings and found the two
produced nearly identical results, choosing the sinusoidal version because it
may extrapolate to longer sequences than those seen in training [S2].

▸ Sources (2)
  [S1] attention-is-all-you-need.pdf — p.6
  [S2] attention-is-all-you-need.pdf — p.6

1 search(es): positional encoding sinusoidal · 2.1s
```

Every claim carries a marker, and the **Sources** expander shows the passage
behind each one — so any sentence can be checked against the original PDF. The
search line underneath shows what the agent actually looked for and how long
the round trip took; a multi-part
question typically produces several searches.

**3. Keep the thread, or start a new one.** Follow-ups carry context — ask "and
who wrote it?" and the agent knows what *it* refers to. Everything is saved to
Postgres, so conversations survive a restart and can be reopened from the
sidebar; **➕ New conversation** starts a clean thread with no prior context.
Only the last `HISTORY_TURNS` (10) turns are resent to the model, so a long chat
doesn't grow unboundedly expensive — the full thread stays visible and stored.

**4. Scope to specific papers.** The sidebar's *Limit questions to* multiselect
restricts search to the papers you pick. Useful for "what does *this* paper say
about X" when the corpus has several papers on the same topic.

**5. Manage the corpus.** The sidebar lists every indexed document with its chunk
and page counts. `✕` removes one document; **Clear all** drops and recreates the
collection.

### Things worth knowing

- **It should say when it doesn't know.** The system prompt forbids answering
  from the model's own knowledge of the literature. If nothing relevant is
  indexed, the honest "I couldn't find this" is the correct output — and worth
  spot-checking, because it's the property that makes the tool trustworthy.
- **Markers are verified, not trusted.** Only markers the model was actually
  shown are rendered; if it invents `[S9]`, that citation is dropped rather than
  displayed as a real source.
- **The agent is capped at 5 search rounds.** On hitting the cap it answers from
  what it has and says so, rather than looping.
- **One page per chunk** means a passage split across a page break is retrieved
  as two separate chunks, each scoring lower than the whole would have.

## Screenshots

> **TODO — not yet captured.** Add these three, then paste the markdown below
> into this section. Drag-and-drop into the GitHub web editor is the easiest
> route: it uploads the image and inserts the link for you.
>
> 1. The full UI with a few papers indexed in the sidebar
> 2. A chat answer showing ranked passages with page citations
> 3. The Qdrant Cloud dashboard showing the `papers` collection
>
> ```markdown
> ![Main UI](docs/images/ui.png)
> ![Answer with citations](docs/images/answer.png)
> ![Qdrant collection](docs/images/qdrant.png)
> ```
>
> A short screen recording also works well here — Streamlit records one from the
> **⋮** menu in the app's top-right corner ("Record a screencast"), and GitHub
> accepts an `.mp4`/`.webm` dropped straight into the README editor.

## Configuration

`OPENAI_API_KEY` is the only setting required for local Docker — `QDRANT_URL`
and `QDRANT_API_KEY` are only needed if you want this container to talk to a
remote cluster instead of its own local Qdrant (see
[Deploying to Streamlit Community Cloud](#deploying-to-streamlit-community-cloud)
for where they're actually required). Everything else is an environment
variable with a working default, spread across three config modules by
concern: `ingestion/config.py`, `retrieval/config.py`, `llm/config.py`.

| Variable | Default | Notes |
| --- | --- | --- |
| `OPENAI_API_KEY` | — | **Required.** From `.env` |
| `LLM_MODEL` | `gpt-5.4-mini` | Any OpenAI model with tool-calling support |
| `MAX_ITERATIONS` | `5` | Hard cap on the agent's search rounds |
| `POSTGRES_URL` | `postgresql://rag:rag@localhost:5432/rag` | Set to the `postgres` host by compose |
| `HISTORY_TURNS` | `10` | Prior turns resent to the model on a follow-up |
| `TITLE_MAX_CHARS` | `60` | Length a conversation's auto-generated title is truncated to |
| `CONVERSATION_LIMIT` | `30` | Conversations listed in the sidebar |
| `POSTGRES_POOL_TIMEOUT` | `5` | Seconds to wait for a Postgres connection before showing an error; raise for slow cold-starts on a serverless/free-tier host |
| `QDRANT_URL` | `http://qdrant:6333` under compose | The local container by default; override to point at Qdrant Cloud instead |
| `QDRANT_API_KEY` | *(empty)* | Not needed for the local container (unauthenticated); required for Qdrant Cloud |
| `QDRANT_COLLECTION` | `papers` | Collection name |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Any sentence-transformers model |
| `EMBEDDING_DIM` | `384` | **Must match the model** |
| `SPARSE_MODEL` | `Qdrant/bm25` | fastembed sparse model |
| `CHUNK_SIZE` | `1000` | Characters, not tokens (~4 chars/token for English) |
| `CHUNK_OVERLAP` | `200` | Characters carried into the next chunk |
| `RETRIEVAL_TOP_K` | `5` | Passages handed to the agent per search |
| `RETRIEVAL_CANDIDATES` | `30` | Pulled by each retriever before fusion and re-ranking |
| `RERANK_ENABLED` | `true` | Set `false` to skip the cross-encoder |
| `RERANK_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Any sentence-transformers cross-encoder |
| `APP_PORT` | `8501` | Host port only, compose-level |

**Changing the embedding model** means changing `EMBEDDING_DIM` to match and
recreating the collection — existing vectors are the wrong shape for the new
one. `make reset` (local) or the **Clear all** button in the sidebar (any
environment) both drop and recreate the collection; re-upload your papers
afterwards. The Dockerfile also bakes the default models into the image, so a
different model gets downloaded at runtime unless that line is updated too.

**Changing chunk settings** only affects documents indexed afterwards. Re-upload
anything already indexed to re-chunk it.

## Local development

Runs Streamlit from a local virtualenv against containerised Qdrant and
Postgres. Requires [uv](https://docs.astral.sh/uv/) and Python 3.13+.

Unlike `docker compose` (which reads `.env` automatically), `make run`/`make
dev` do not. `QDRANT_URL` defaults to `http://localhost:6333` (`ingestion/config.py`)
so `make deps` is enough on its own; export anything else you need
(`OPENAI_API_KEY` at minimum) into your shell first:

```bash
set -a && source .env && set +a   # or export OPENAI_API_KEY=... etc. by hand
make deps                          # start Qdrant and Postgres
make dev                           # uv sync, then Streamlit with auto-rerun on save
```

`make dev` reruns the app on every save; `make run` is the same without the
reload. Both call `uv sync` first, so dependencies stay in step with `uv.lock`.

The first question or upload after each restart takes a few extra seconds — the
embedding model is loaded lazily, on first use, then cached for the life of the
process.

## Deploying to Streamlit Community Cloud

Streamlit Community Cloud runs `app.py` directly with `pip install` — it does
**not** run `docker-compose.yml`, so neither local container exists there.
Both datastores have to be something reachable from the public internet:

- **Qdrant Cloud**, not the local container. One free cluster is enough — it's
  used *only* by the deployment, never by local Docker (see
  [Quick start](#quick-start-docker)), so a single-cluster free trial is not a
  constraint here. [cloud.qdrant.io](https://cloud.qdrant.io): create a
  cluster, copy its **URL** and generate an **API key**.
- **A hosted Postgres**, not `docker-compose.yml`'s `postgres` service — that
  hostname only resolves inside your machine's Docker network. Reusing it
  produces exactly the error this setup does: *"Postgres unreachable...
  couldn't get a connection after 5.00 sec"* (`POSTGRES_POOL_TIMEOUT`,
  `history/config.py`). [Neon](https://neon.tech) has a free tier that works
  well: create a project, copy its connection string (it already includes
  `?sslmode=require`).

And **`.env` isn't read** — secrets go in the app's **Settings → Secrets** box,
as TOML. Root-level keys there are exposed both as `st.secrets` *and* as
`os.environ`, which is exactly what every `os.getenv(...)` call in this
project's config modules reads — so no code differs between Docker and
Streamlit Cloud, only where the values come from.

**Steps:**

1. Push this repo to GitHub and create the app on
   [share.streamlit.io](https://share.streamlit.io), pointing at `app.py`.
2. Create a Qdrant Cloud cluster and a hosted Postgres (e.g. Neon), and copy
   both connection strings.
3. In the app's **Settings → Secrets**, paste (see
   `.streamlit/secrets.toml.example` for the full template):

   ```toml
   OPENAI_API_KEY = "sk-..."
   QDRANT_URL = "https://your-cluster.cloud.qdrant.io"
   QDRANT_API_KEY = "..."
   POSTGRES_URL = "postgresql://user:password@host/dbname?sslmode=require"
   ```

4. Redeploy (or wait for the automatic restart after saving secrets).

If the sidebar still shows Postgres as unreachable right after a period of
inactivity, a free-tier/serverless database's cold start may be slower than
the 5-second default — add `POSTGRES_POOL_TIMEOUT = "15"` to the same secrets
block.

**Keeping local and deployed data apart.** Local Docker's Qdrant and Postgres
are entirely separate containers from the ones the deployment uses — nothing
you upload or ask locally ever reaches the deployed app, and nothing needs
coordinating (no shared collection names, no shared credentials). If you ever
*do* want this local app to inspect the deployed app's Qdrant Cloud data, set
`QDRANT_URL`/`QDRANT_API_KEY` in your local `.env` to override the compose
default — just remember to unset them again afterwards, or local uploads will
start landing in the cloud cluster instead of your local container.

## Project layout

```
app.py                  Streamlit UI — sidebar (upload/manage/scope) and chat
ingestion/              Write path: document → vectors
  config.py             Qdrant, embedding and chunking settings
  extract.py            PDF/text → per-page text
  chunking.py           Page text → overlapping chunks with page numbers
  embeddings.py         Dense sentence-transformers wrapper, cached per process
  sparse.py             BM25 term frequencies for the keyword half
  store.py              Qdrant client: upsert, list, delete, health
  pipeline.py           Ties the stages together; content-hash doc IDs
retrieval/              Read path: query → passages
  config.py             top-k, candidate width, re-ranking switches
  search.py             Hybrid dense + sparse, RRF fusion, document filter
  rerank.py             Cross-encoder re-ranking
  service.py            search_papers() — the only entry point the agent uses
llm/                    Answer generation
  config.py             Model, iteration cap, API key
  client.py             OpenAI client, cached per process
  prompts.py            System instructions and citation-marker formatting
  tools.py              The search_papers tool schema
  agent.py              The tool-calling loop
history/                Conversation persistence
  config.py             Postgres URL, history window, sidebar limits
  schema.sql            conversations / messages / citations — idempotent DDL
  db.py                 Connection pool; applies the schema on first use
  store.py              Create, list, load and delete conversations
docker-compose.yml      qdrant + postgres + app services (local only)
Dockerfile              Python 3.13-slim, uv, all three models baked in
Makefile                All the commands above
.streamlit/
  config.toml            Headless mode, usage-stats off
  secrets.toml.example   Template for Streamlit Community Cloud's Secrets box
evaluation/ monitoring/ Placeholders — see Roadmap
```

The split is deliberate: `ingestion/` only ever writes, `retrieval/` only ever
reads, and `llm/` reaches Qdrant solely through `retrieval.service`. The agent
has exactly one tool, so there is one place where retrieval can be changed.
`history/` touches neither — it records what happened, and the app degrades to
in-session-only chat if Postgres is unavailable.

## Troubleshooting

**Port 8501 already in use** — usually a local `streamlit run` still holding it.
Stop that process, or pick another host port:

```bash
APP_PORT=8502 docker compose up -d     # app moves to http://localhost:8502
```

**"Qdrant unreachable" in the sidebar** — check Qdrant came up healthy with
`docker compose ps`. Inside compose the app talks to `http://qdrant:6333` (the
service name), not `localhost`; the error message shows which URL it tried.
`make down && make up` clears most cases. If you've overridden `QDRANT_URL` to
point at a remote cluster instead, check that cluster is running in the
[Qdrant Cloud console](https://cloud.qdrant.io) and the API key hasn't been
revoked — `docker compose restart app` picks up a corrected `.env` (compose
doesn't re-read it into an already-running container).

**Deployed on Streamlit Cloud and this error shows there** — see
[Deploying to Streamlit Community Cloud](#deploying-to-streamlit-community-cloud);
you need `QDRANT_URL`/`QDRANT_API_KEY` set to a Qdrant Cloud cluster in that
app's Secrets, since there's no local container there at all.

**Code changes aren't showing** — the image copies the source at build time, so
rebuild with `make up` (it passes `--build`). For a tight edit loop use `make dev`
instead.

**Upload reports "no extractable text (scanned PDF?)"** — the PDF has no text
layer, only page images. There is no OCR step; run the file through OCR
externally first.

**The first upload hangs for ~30s** — the embedding model is loading. It happens
once per process; in Docker the model is already on disk, so this is a load
rather than a download.

## Evaluation criteria

This is an LLM Zoomcamp course project, scored against the standard rubric. Where
each criterion is addressed, and what is honestly still missing:

| Criterion | Status | Where |
| --- | --- | --- |
| Problem description | ✅ Done | [The problem](#the-problem) |
| Retrieval flow — knowledge base + LLM | ✅ Done | Qdrant knowledge base + agentic LLM answer generation — [How it works](#how-it-works) |
| Retrieval evaluation | ❌ Not started | `evaluation/` is empty |
| LLM evaluation | ❌ Not started | `evaluation/` is empty |
| Interface | ✅ Done | Streamlit UI — `app.py`, [Walkthrough](#walkthrough) |
| Ingestion pipeline | ✅ Done | Automated and code-driven — `ingestion/pipeline.py` |
| Monitoring | ⚠️ Partial | Per-turn latency, tokens and search queries are **captured** in Postgres; no dashboard yet |
| Containerization | ✅ Done | App, Qdrant **and** Postgres in `docker-compose.yml` (deployment uses Qdrant Cloud + hosted Postgres instead) |
| Reproducibility | ✅ Done | [Quick start](#quick-start-docker); `uv.lock` pins every dependency |
| Best practices — hybrid search | ✅ Done | Dense + BM25 fused with RRF — `retrieval/search.py` |
| Best practices — re-ranking | ✅ Done | Cross-encoder over the top 30 — `retrieval/rerank.py` |
| Best practices — query rewriting | ✅ Done | The agent writes its own search queries and re-searches — `llm/agent.py` |
| Bonus — cloud deployment | ✅ Done | Deployed on Streamlit Community Cloud — Qdrant Cloud + hosted Postgres, see [Deploying to Streamlit Community Cloud](#deploying-to-streamlit-community-cloud) |

## Roadmap

In the order it makes sense to build:

1. **Retrieval evaluation** — a small ground-truth set of question→page pairs
   over a few known papers, scored with hit-rate and MRR. This is now the most
   valuable next step: hybrid search and re-ranking are both in, but there is no
   measurement proving either helps on *this* corpus, or telling you what to set
   `RETRIEVAL_CANDIDATES` to. Lands in `evaluation/`.
2. **LLM evaluation** — grade answers for groundedness (does each `[Sn]` marker
   actually support its claim?) and for correct refusal on unanswerable
   questions. The citation registry in `llm/agent.py` already gives the harness
   the claim→passage pairs it needs.
3. **Monitoring** — the data is already being written; what's missing is a
   `feedback` table (thumbs up/down, one row per assistant message) and a
   dashboard over query volume, latency, token spend and searches per question.
   Lands in `monitoring/`.
