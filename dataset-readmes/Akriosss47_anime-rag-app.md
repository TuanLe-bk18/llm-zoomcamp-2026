# AniRec — anime recommendation agent

Capstone project: an LLM app that recommends anime based on the
[Top 15000 Ranked Anime](https://www.kaggle.com/datasets/quanthan/top-15000-ranked-anime-dataset-update-to-32025)
dataset from Kaggle. It's basically a RAG/agent hybrid: the LLM decides
whether to search for similar anime by meaning (semantic search) or filter
by hard constraints (genre, score, episode count), and sometimes both at once.

## Why it's built this way

I started with plain RAG (just embeddings + search), but quickly noticed
that requests like "show me something short, under 15 episodes" don't work
well with vector search alone — the model finds things that are
semantically similar, but it's bad at filtering on actual numbers. So I
added a second tool, `filter_anime`, which does a normal structured filter
over the metadata (score, episodes, genre, type), and the LLM decides via
function calling which one to call. That gives you an actual agentic flow,
instead of just stuffing the top-5 results into a prompt.

For the LLM I went with Groq — fast, and the free tier is generous enough
for testing, plus the official `groq` python package works almost exactly
like the openai one. For embeddings I used
`sentence-transformers/all-MiniLM-L6-v2` — small, runs fine on CPU, no API
key needed.

The store originally was Chroma (pure vector), but it didn't handle exact
title/name queries well — if someone typed a specific title with a typo or
only part of it, vector search would sometimes miss the obvious match,
because "meaning" matters more to an embedding than exact wording. I moved
to **Elasticsearch** and built an honest hybrid search: BM25 (keyword) + kNN
(vector similarity) over the same index, with results merged via
**Reciprocal Rank Fusion (RRF)** — that gets you the strengths of both
instead of betting on just one.

Hit an annoying one after that switch: Groq started throwing `413 Request
too large` / `rate_limit_exceeded` errors on the free tier (12,000 TPM).
Turned out every search result coming back from Elasticsearch still carried
its raw 384-dim embedding vector along with it — completely useless to the
LLM, but it was getting serialized into the tool-call response and sent
straight into the prompt anyway. On 8 results that's ~11,000 tokens on its
own, just from vectors the model never needed to see. Fixed it two ways:
excluded the `embedding` field at the Elasticsearch query level
(`_source.excludes`), and added a second trim step before anything goes back
to the LLM (only title/type/episodes/score/genres/studio + a 250-char
synopsis — no raw scores, no member counts, nothing it doesn't need to write
a recommendation). Dropped the worst-case payload by about 92%.

## How it's structured

```
User query
   │
   ▼
LLM (function calling) — decides which tool to call
   ├─▶ semantic_search   — hybrid search in Elasticsearch:
   │                         BM25 (keyword) + kNN (vector) → merged via RRF
   └─▶ filter_anime      — structured filter on score/episodes/genre/type
   │
   ▼
Retrieved anime + metadata
   │
   ▼
LLM writes an answer, grounded only in what was actually retrieved (no
made-up titles — that's spelled out directly in the system prompt)
   │
   ▼
Everything gets logged to SQLite (query, which tools fired, what was
retrieved, the answer, latency)
   │
   ▼
Streamlit UI: answer + list of sources + 👍/👎 buttons
```

| What                                          | File          |
| --------------------------------------------- | ------------- |
| Config (paths, models, keys)                  | `config.py`   |
| Elasticsearch: index mapping, bulk loading    | `es_store.py` |
| Loading the dataset into Elasticsearch        | `ingest.py`   |
| Agent: tools, hybrid search, prompt, LLM call | `rag.py`      |
| Evaluation                                    | `evaluate.py` |
| Interface                                     | `app.py`      |
| Feedback logging                              | `db.py`       |

## Running it

Using `uv` — faster and more reliable than plain pip, and it manages the
venv for you.

```bash
cd anime-rag-app
uv sync
```

### Elasticsearch

```bash
docker compose up -d
```

Spins up a local single-node Elasticsearch 8.15 on `localhost:9200` (no
auth — fine for local dev, not for production). First run takes 20-30
seconds to come up. `ingest.py` waits for it automatically now (up to 60s,
polling with backoff) instead of just failing on the first connection
attempt — but if it never comes up, check:

```bash
docker compose ps
docker compose logs elasticsearch --tail=50
curl http://localhost:9200/_cluster/health
```

On Windows/Mac specifically: Docker Desktop needs enough memory allocated
(Settings → Resources) or Elasticsearch can silently get OOM-killed right
after starting — I'd give it at least 4GB if you can spare it, or drop
`ES_JAVA_OPTS` in `docker-compose.yml` to something like `-Xms512m -Xmx512m`
if you can't.

If you already have your own ES (e.g. a managed instance), just set
`ES_HOST` in `.env` instead of using docker.

### Dataset

The real file (`data/top_15000_anime.csv`, MyAnimeList schema: `name`,
`score`, `genres`, `synopsis`, `type`, `episodes`, `studios`, `premiered`,
`rank`, `popularity`, `members`, etc.) is already in the repo. Column names
get mapped to a single canonical schema through `COLUMN_ALIASES` at the top
of `ingest.py`.

One thing I tripped over: the dataset has a `rating` column — but that's not
a score, it's the age rating (PG-13, R-17+, etc). I originally had an alias
rule `rating → score` (built for datasets that call the score column
"rating"), and it clobbered the real `score` column with this one instead.
Had to drop that alias and add an explicit `premiered → aired` mapping.

### Groq key

```bash
cp .env.example .env
```

then paste in `GROQ_API_KEY` (free key at https://console.groq.com/keys).
`.env` gets auto-loaded by `python-dotenv` in `config.py`, so you don't need
to `export` anything every time — I got burned by this myself once, when the
key was exported in one terminal session and Streamlit was started from
another.

**Heads up on the free tier's rate limit:** it's capped at 12,000 tokens per
minute for `llama-3.3-70b-versatile`, which is tight for an agent that
stuffs retrieved anime into the context on every tool call. I actually hit
this myself — turned out Elasticsearch was returning the raw 384-dim
`embedding` vector alongside every result, which got serialized straight
into the prompt and alone ate ~11k tokens for just 8 results. Fixed it by
excluding `embedding` at the query level (`_source.excludes`) and trimming
what actually goes to the LLM down to title/type/episodes/score/genres/
studio + a 250-char synopsis snippet (see `_compact_for_llm` in `rag.py`).
If you still hit 429/413 errors, `HYBRID_CANDIDATE_POOL` and `DEFAULT_TOP_K`
in `config.py` are the first knobs to turn down.

### Let's go

```bash
uv run python ingest.py       # embeddings + indexing into Elasticsearch, ~15000 rows
uv run streamlit run app.py
```

The first `ingest.py` run takes a bit longer — it downloads the embedding
model (~90MB) and computes vectors for every row.

Queries that work well:

- "Recommend something similar to Death Note"
- "Short comedy anime, under 15 episodes"
- "Emotional drama anime with a score above 8.5"
- "Anime like Attack on Titan but with romance instead of horror"

Each answer has a collapsible list of sources (what was actually found) and
👍/👎 buttons. The **Monitoring** tab shows aggregates (feedback rate,
satisfaction rate, average latency) and a table of recent interactions, plus
a separate view of 👎-flagged ones to go through.

### Evaluation

```bash
uv run python evaluate.py --skip-generation --sample-size 300   # quick sanity check, ~1-2 min
uv run python evaluate.py --skip-generation                     # full retrieval eval, all 15k anime
uv run python evaluate.py                                       # + LLM-as-judge
```

Heads up on the full retrieval eval: each anime does a _hybrid_ search (BM25 +
kNN = 2 Elasticsearch round-trips + 1 embedding call), so the full 15k run is
~30k+ requests to Elasticsearch. It has a progress bar now (it didn't
originally — first time I ran it, it just sat there silently for so long I
genuinely thought it had hung). It can still genuinely take a long time
depending on your machine/Docker resources, so run with `--sample-size 300`
first to confirm everything's wired up before committing to the full run.

Retrieval eval — I didn't have ground truth (nobody hands you a labeled
"similarity" dataset), so I built a proxy metric instead: for each anime,
search "similar to `<title>`" and check whether the genres of the top-k
results overlap with the seed anime's own genres. Not perfect, but better
than nothing.

Generation eval — an LLM judge (same Groq model) scores the agent's answers
on three scales: relevance, groundedness (did it make up any titles),
usefulness. The eval set is 26 queries covering different categories:
similar-to-a-specific-title, mood/vibe-based search, structured constraints
(episodes/score/type), combined semantic+structured, specific genres, and a
few "honesty" edge cases (requests where nothing great might actually exist
in the dataset — checking that the agent doesn't just make something up to
have an answer).

## Results

**Retrieval eval, hybrid search (Elasticsearch, BM25+kNN via RRF)** — sanity
check on a 300-anime sample (`--sample-size 300`), top_k=5:

| Metric      | Value |
| ----------- | ----- |
| Hit-rate@5  | 0.94  |
| MRR (proxy) | 0.833 |

Solid jump from the old pure-vector numbers below (0.847 / 0.703 on a
10,000-anime sample) — consistent with what you'd expect from adding BM25
into the mix: exact title/keyword matches that pure vector search sometimes
missed now get caught. That said, 300 is still just a sanity-check sample,
not the full 15k dataset, so treat this as "the hybrid approach is clearly
working" rather than a final number. Still outstanding: the full 15k
retrieval eval, and the generation eval (26 queries, LLM-as-judge) on this
backend.

<details>
<summary>Old results (Chroma, pure vector, before hybrid search)</summary>

**Retrieval eval** (top_k=5, n=10,000):

| Metric      | Value |
| ----------- | ----- |
| Hit-rate@5  | 0.847 |
| MRR (proxy) | 0.703 |

**Generation eval** (LLM judge, Groq `llama-3.3-70b-versatile`, 6 test queries):

| Metric       | Average (1-5) |
| ------------ | ------------- |
| Relevance    | 4.5           |
| Groundedness | 5.0           |
| Usefulness   | 4.33          |

</details>
