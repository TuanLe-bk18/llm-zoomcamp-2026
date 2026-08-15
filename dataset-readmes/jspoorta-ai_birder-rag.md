# Birder RAG

RAG assistant for birders, especially beginners. Describe what you saw (size, colors, markings, behavior, location) and get grounded identification help plus facts.

## Problem statement

A beginner gets a few seconds with an unfamiliar bird, then has to work from
fragments: sparrow-sized, brown, rusty-red cap, hopping under a hedge in an
Amsterdam park. Turning that into a species name is where beginners get stuck.

Why the existing options don't help:

- **Field guides** are organised taxonomically - you need to know the family
  first, which is exactly what a beginner doesn't.
- **Photo and sound apps** (Merlin, ObsIdentify) work well, but only if the bird
  stayed put long enough to capture.
- **Asking an LLM directly** gives fluent, sourceless answers biased toward North
  American species, because that's what dominates English birding text online.

**What this does.** You describe the bird in free text. The system retrieves
matching passages from Wikipedia species accounts for the regularly occurring
birds of the Netherlands, and an LLM answers using only those passages, with
links to the sources. It also answers direct questions about a named species:
diet, breeding, habitat, migration.

**Why RAG and not just an LLM:**

- **Grounding**: every claim traces to a retrieved passage, and the system can
  say the corpus doesn't cover something instead of inventing a field mark.
- **Scoping**: the knowledge base holds only species recorded in the
  Netherlands, ruling out confident suggestions of American birds that have never
  occurred here.

**What this version does not do** (yet):

- No ID from photos or audio, text descriptions only.
- No illustrations.
- No live sightings yet, and its sense of seasonality is only as good as what the
  source articles state.
- The output is a shortlist to check against a proper guide, not a determination.

**Planned extension.** A live sightings lookup (eBird API) would let the
assistant weight candidates by what has actually been reported near you recently,
and give it a real sense of season, a bird plausible in October may be absent in
May. That turns the flow agentic: retrieve from the knowledge base, then call out
for current observations. Deliberately out of scope for the first version.

### Example queries

```
Small brown bird with a rusty red cap, hopping on the ground under a hedge in a
city park. About sparrow-sized.

Black and white wading bird with a long orange bill, on the mudflats, very noisy.

Do bearded reedlings stay in the Netherlands over winter?

What's the difference between a marsh tit and a willow tit?
```

## Setup and running

Requirements: Python 3.10+, [uv](https://docs.astral.sh/uv/), Docker, an OpenAI API key.

```bash
cp .env.example .env   # fill in OPENAI_API_KEY
uv sync --frozen
```

The ingestion outputs (`data/birds_chunks.json`, `data/species_traits.json`) and
both vendored trait xlsx files are committed, so a fresh clone can go straight
to running the app. To regenerate the ingestion outputs from scratch instead:

```bash
uv run python -m ingestion.pipeline --limit 120
uv run python -m retrieval.build
```

### Full stack (app + Qdrant + Postgres + Grafana + Tempo)

```bash
docker compose up -d --build
```

- App: http://localhost:8501
- Grafana: http://localhost:3000 (admin/admin), feedback/cost/latency dashboard, plus a Tempo data source for trace exploration
- Qdrant: http://localhost:6333
- Tempo: http://localhost:3200

### Running pieces individually (no Docker)

```bash
uv run streamlit run app.py                    # UI, embedded local Qdrant store by default
uv run python -m rag.pipeline "your question"   # CLI
uv run pytest tests/                            # 42 tests, no network/Docker needed
```

### Evaluation

```bash
uv run python -m eval.ground_truth --limit 200   # synthetic Q&A -> data/ground_truth.json
uv run python -m eval.retrieval_eval             # hit-rate/MRR: keyword vs vector vs hybrid
uv run python -m eval.llm_eval --sample-size 30   # LLM-as-judge: concise vs detailed prompts
```

## Data Sources
- Wikipedia, starting from [List of birds of the European Netherlands](https://en.wikipedia.org/wiki/List_of_birds_of_the_European_Netherlands), fetched live, no setup needed.
- [BIRDBASE: A Global Dataset of Avian Biogeography, Conservation, Ecology and Life History Traits](https://www.nature.com/articles/s41597-025-05615-3), with its associated [xlsx file](https://springernature.figshare.com/ndownloader/files/55634729), figshare blocks automated downloads, so this file is vendored at `data/raw/birdbase.xlsx` for reproducibility.
- [IOC World Bird List v15.2, Multilingual Version](https://worldbirdnames.org/Multiling%20IOC%2015.2.xlsx) (scientific/English/Dutch name crosswalk), fetched live, no setup needed.
- [AVONET: morphological, ecological and geographical data for all birds](https://opentraits.org/datasets/avonet) (Tobias et al. 2022), beak/wing/tail/tarsus morphology. Also figshare-hosted and blocked from automated download, so also vendored at `data/raw/avonet.xlsx`.

### Data licensing / attribution

- **BIRDBASE**, Neate-Clegg et al. (2025). *BIRDBASE: A Global Dataset of Avian Biogeography, Conservation, Ecology and Life History Traits.* Scientific Data. https://doi.org/10.1038/s41597-025-05615-3. Licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Vendored file is unmodified; the ingestion pipeline reads only a subset of columns (body mass, primary habitat, primary diet, migratory status, clutch size, nest type).
- **AVONET**, Tobias et al. (2022). *AVONET: morphological, ecological and geographical data for all birds.* Ecology Letters. https://doi.org/10.1111/ele.13898. Licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Vendored file is unmodified; the pipeline reads only morphology columns (beak, wing, tail, tarsus measurements).
- **IOC World Bird List**, Gill, F., D. Donsker & P. Rasmussen (Eds). *IOC World Bird List (v15.2).* https://doi.org/10.14344/IOC.ML.15.2. Licensed [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/).
- **Wikipedia**, species article text, licensed [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Per-species source links are shown alongside any answer that draws on them.

## Chosen tech-stack and features

See the [working notes](birder-rag-project-context.md) why certain tools and tech was chosen, driven primarily by the [project assignment](project_assignment.md) of the [LLM Zoomcamp 2026](https://courses.datatalks.club/llm-zoomcamp-2026/).

| Feature | What this project does |
|---|---|
| Problem description | See "[Problem statement](#problem-statement)" above. |
| Retrieval flow | Both a knowledge base (`retrieval/`: minsearch, Qdrant, and a hybrid RRF fusion) and an LLM (`gpt-4o-mini` via `rag/pipeline.py`) are used together. |
| Retrieval evaluation | Keyword, vector, and hybrid retrieval are all evaluated against 600 synthetic ground-truth questions (`eval/retrieval_eval.py`; results in `data/retrieval_eval_report.txt`). Qdrant (vector) won on both hit-rate and MRR and is the default retriever. |
| LLM evaluation | Two prompt variants (`concise`, `detailed`) are compared via LLM-as-judge over 30 sampled questions (`eval/llm_eval.py`; results in `data/llm_eval_report.txt`). `detailed` won 17-9 (4 ties) and is the default. |
| Interface | Streamlit UI (`app.py`). |
| Ingestion pipeline | Automated via `dlt`, not a bare script (`ingestion/pipeline.py`), see "Data Sources" for the four joined sources. |
| Monitoring feedback | User feedback (👍/👎) captured to Postgres (`monitoring/db.py`), plus a 5-panel Grafana dashboard (`docker/grafana/dashboards/birder_rag.json`): feedback split, queries over time, avg response time, cost per query, and relevance (top match score) distribution. |
| Monitoring traces | OpenTelemetry tracing (`monitoring/tracing.py`, instrumented in `rag/pipeline.py`) exports retrieval/generation latency spans to Grafana Tempo. |
| Containerization | Full stack in `docker-compose.yml`: app, Qdrant, Postgres, Grafana, Tempo, `docker compose up -d --build` runs everything. |
| Reproducibility | `uv sync --frozen` against the committed `uv.lock` pins every dependency version. Ingestion outputs and both vendored trait xlsx files are committed, so a fresh clone needs no manual steps. |
| Best practices: hybrid search | `retrieval/hybrid.py` implements Reciprocal Rank Fusion over minsearch + Qdrant, evaluated alongside the other two approaches in `eval/retrieval_eval.py`. |

