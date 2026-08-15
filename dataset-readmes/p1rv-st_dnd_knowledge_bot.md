# Drakkenheim Lore Keeper

An in-character RAG chatbot for a tabletop RPG setting. You talk to an NPC — a weary
archivist in a ruined city — and they answer questions about the world's lore, grounded in
an actual knowledge base rather than in whatever the language model happens to remember.

Built as the final project for the [LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp)
course. See [Evaluation criteria](#evaluation-criteria) for a map of where each requirement
is implemented.

---

## Problem description

**Dungeons & Dragons** campaign settings come with a lot of lore: cities, factions, gods,
historical events, who hates whom and why. *Drakkenheim* — the setting used here — is a
gothic-horror city destroyed by a falling meteor of alien magic, and its lore is scattered
across a community wiki and the Dungeon Master's private notes.

A general-purpose chatbot solves none of these: ask ChatGPT about Drakkenheim and it will
confidently invent details, because this is niche, community-authored lore.

**This project** puts the lore into a vector database and lets players ask questions in
natural language. An LLM agent retrieves relevant passages and answers *in character*. Each
persona has its own knowledge boundary, enforced at the database level — so the novice
genuinely cannot answer questions outside their domain, rather than merely being asked not
to.

### Example

> **Question:** What happened to Drakkenheim?
>
> **The Librarian:** Fifteen years ago, Drakkenheim met its doom when a meteorite of
> delerium, a strange purple crystal, crashed into the city, erasing it in an instant. What
> was once a thriving capital of Westemar is now a ruined shell, enveloped in an eternal
> haze that deforms anything caught within it. Only a few hundred of the hundred thousand
> inhabitants survived, while the surrounding villages have turned silent.

One thing worth knowing up front: **the lore corpus itself is in Russian** — that is the
language it was written and scraped in — while the interface, prompts and personas are in
English. This works because the embedding model (`multilingual-e5-large`) matches across
languages and the agent is instructed to render what it finds in the reply language. The
cost is that proper nouns are translated on the fly and can drift between answers. The
reply language is a single environment variable (`RESPONSE_LANGUAGE`), so pointing the
whole thing back at Russian is a one-line change.

---

## Running it

### Prerequisites

- Docker and Docker Compose
- An OpenAI API key (or an OpenRouter key — see [Configuration](#configuration))

### Quick start

```bash
git clone <this-repo>
cd rpg_bartender_project

cp .env.example .env
# open .env and set OPENAI_API_KEY

docker compose up --build
```

Then open **http://localhost:8501**.

That single command starts everything:

| Service | Role |
| --- | --- |
| `qdrant` | Vector database, persisted to `./data/qdrant_storage` |
| `ingest` | One-shot: embeds `documents.jsonl` into Qdrant, then exits |
| `app` | Streamlit chat UI on port 8501, waits for `ingest` to finish |

**First run takes a few minutes** — the embedding model (~2 GB) is downloaded once into a
named volume (`fastembed_cache`). Subsequent starts take well under a minute and re-use the
cached model. Re-running ingestion is safe: chunk ids are stable, so the collection is
simply rebuilt to the same 66 points.

### Using the app

- Pick a character in the sidebar. Switching characters starts a fresh conversation,
  because the agent's instructions and knowledge boundaries change with the persona.
- Ask questions in the chat box.
- **Start over** clears the history.

Two personas ship with the project: `librarian` (Brunn, knows the whole corpus) and
`novice` (a temple acolyte restricted to faith and deities). Adding another is just another
YAML file in `personas/` — the UI picks it up automatically.

### Local development (without containerising the app)

```bash
docker compose up -d qdrant          # database only
uv sync                              # dependencies (Python >= 3.14, managed by uv)

uv run data/qdrant_ingest/ingest.py                            # build the collection
uv run data/qdrant_ingest/search.py "What happened to the city?"  # test retrieval alone
uv run agent.py librarian "What is the Amethyst Academy?"         # test the agent in a terminal
uv run streamlit run app.py                                    # the UI
```

---

## How it works

```
data/qdrant_ingest/documents.jsonl     66 pre-chunked lore documents (checked into the repo)
        │
        │  ingest.py — embeds with FastEmbed, upserts
        ▼
   Qdrant  ──  collection `drakkenheim_lore`, vector `fast-multilingual-e5-large`
        │
        │  search.py — semantic search, optional payload filters
        ▼
tools/lore_search.py                   exposed to the agent as the `search_lore` tool
        │
        ▼
   agent.py                            Pydantic AI agent; decides when to search
        │
        ▼
   app.py                              Streamlit chat UI
```

**Retrieval.** Queries are embedded with `intfloat/multilingual-e5-large` and matched
against the collection by cosine similarity. Note that embedding inference runs *locally in
the client process* via FastEmbed — the Qdrant server itself performs no inference — which
is why the application container, not the database container, carries the ~2 GB model.

**Agent, not a fixed chain.** The LLM is not handed a pre-filled prompt. It receives the
`search_lore` tool and decides when to call it, with what query, and whether to search again
before answering. Small talk costs no retrieval; a lore question triggers one or more
searches.

**Personas.** Each persona is a YAML file in `personas/` defining name, character, speech
style, an optional portrait (`avatar`), and an optional `known_type_labels` list. That list
becomes a Qdrant payload filter, so retrieval physically cannot return documents outside
the persona's domain:

```yaml
name: The Novice          # a temple acolyte who never left the sanctuary
known_type_labels:        # kept in Russian: matched verbatim against the indexed payload
  - Вера                  # faith
  - Божество              # deity
```

These two values are the one place Russian survives in the configuration, and deliberately
so — they are not prose but literal payload values in the index. Translating them would
leave the persona with an empty knowledge base.

**Grounding.** The system prompt requires the agent to answer only from retrieved passages
and to admit ignorance rather than invent lore.

---

## Dataset

`data/qdrant_ingest/documents.jsonl` — **66 chunks**, checked into the repository, so the
knowledge base is reproducible without re-scraping anything.

| Source | Chunks | Origin |
| --- | --- | --- |
| `parser_vvd` | 50 | Community wiki [drakkenheim.vvd.world](https://drakkenheim.vvd.world/), scraped per entity and split into sections |
| `notion_base` | 16 | A Dungeon Master's Notion export, split on `#` headings |

Each record carries `id` (a stable uuid5, making ingestion idempotent), `source`, `title`,
`text`, `url`, and a `metadata` object. Wiki chunks additionally carry `type_label`, which
is what persona scoping filters on — the available values are `Страна` (country, 14),
`Божество` (deity, 12), `Фракция` (faction, 9), `Вера` (faith, 7), `Город` (city, 4),
`Волшебные предметы` (magic items, 2) and `Явление` (phenomenon, 2). Note that Notion
chunks carry no `type_label` at all, so any persona that sets `known_type_labels` is
implicitly restricted to wiki content. Chunks are capped at 1800 characters, packed on
paragraph boundaries; each also stores
its full parent section under `metadata.section_text`, so search can return either the
precise chunk or the wider section for context.

The scrapers that produced this file have been removed from the repository — the chunked
JSONL *is* the knowledge base now.

---

## Configuration

All configuration lives in `.env` (template: `.env.example`).

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | — | Required unless using OpenRouter |
| `OPENROUTER_API_KEY` | — | Alternative provider |
| `LLM_MODEL` | `openai:gpt-4o-mini` | Provider prefix selects the backend, e.g. `openrouter:anthropic/claude-sonnet-4.6`. Resolved by Pydantic AI |
| `RESPONSE_LANGUAGE` | `English` | Language the assistant replies in |
| `RESPONSE_LENGTH` | short, 3–5 sentences | Length instruction injected into the prompt |
| `TEMPERATURE` | `1.0` | Deliberately high — see below |
| `FREQUENCY_PENALTY` | `0.4` | Deliberately high — see below |
| `MAX_HISTORY_TURNS` | `10` | User turns kept in context |
| `QDRANT_URL` | `http://localhost:6333` | Overridden to `http://qdrant:6333` inside Compose |

The high temperature and frequency penalty are intentional. Combined with an explicit
"never do this" block in the system prompt (no *"Certainly!"*, no *"as an AI"*, no
summarising conclusion, no em-dash tics), they push the model away from flat assistant-speak
and towards something that reads like a person in a ruined library.

---

## Project structure

```
app.py                          Streamlit UI — entry point
agent.py                        Pydantic AI agent, prompt assembly, CLI mode
persona.py                      Persona model + YAML loading
personas/*.yaml                 Character definitions (+ optional portrait images)
tools/lore_search.py            The search_lore tool given to the agent
data/qdrant_ingest/
    documents.jsonl             The knowledge base
    ingest.py                   Ingestion pipeline
    search.py                   Semantic search; owns all Qdrant coordinates
Dockerfile                      Image shared by the app and ingest services
docker-compose.yml              Full stack
```

---

## Evaluation criteria

| Criterion | Where |
| --- | --- |
| Problem description | [Problem description](#problem-description) |
| Retrieval flow | Qdrant knowledge base + LLM: `data/qdrant_ingest/search.py`, `tools/lore_search.py`, `agent.py` |
| Retrieval evaluation | **Not implemented** — see the note below |
| LLM evaluation | **Not implemented** — see the note below |
| Interface | Streamlit web UI: `app.py` |
| Ingestion pipeline | Python script: `data/qdrant_ingest/ingest.py` |
| Monitoring | **Not implemented** — see the note below |
| Containerisation | Everything in `docker-compose.yml` (Qdrant, ingestion, app) |
| Reproducibility | [Running it](#running-it); dataset committed to the repo; dependencies pinned in `uv.lock` |

Retrieval evaluation, LLM evaluation and monitoring are deliberately deferred rather than
overlooked. Closing them would require, respectively: a golden set of questions with
ground-truth chunks scored on hit rate and MRR across several retrieval strategies; a
comparison of prompts or models on that same question set, judged by an LLM or by hand; and
feedback buttons plus request/latency logging behind a dashboard.

## Known limitations

- Conversation history lives in Streamlit session state only — it is lost on refresh, and
  nothing is persisted or logged.
- Roughly 48 of the 66 chunks still contain raw cross-reference markers of the form
  `[[Label|uuid]]`, left over from the wiki scraper. They pollute both the embeddings and
  the text the model sees.
- The corpus is small (66 chunks). It covers the setting's core lore, not every entity on
  the wiki.
- The corpus is in Russian while the interface is in English, so the model translates
  passages on the fly. Proper nouns are usually stable but can vary between answers.
