# recipe-to-cart

*From saved recipes to a shopping list.*

> **Status:** LLM Zoomcamp final project.

```bash
docker compose up      # app :8501 · dashboard :3000 · ingestion :4200
```

Streamlit UI over a Qdrant index that a scheduled Prefect flow builds, with user
feedback in Postgres behind a Grafana dashboard — all in one compose file. Jump
to [Setup](#setup), or read on for how each piece was chosen and measured.

## Problem

Over the years I saved ~4,000 Instagram posts, including 725 food recipes.
Instagram gives me no way to search them ("that chickpea curry I saved last
year…" means endless scrolling), no way to ask questions about them, and no
way to turn the ones I pick into a grocery list.

**recipe-to-cart** is a RAG application over my own recipe bookmarks:

1. **Ask** — natural-language questions over the recipe corpus
   ("what can I cook with chicken and coconut milk?"), answered by an LLM
   grounded in retrieved recipes.
2. **Pick** — select the recipes you want to cook.
3. **Cart** — get an aggregated, deduplicated shopping list.

A distinctive twist: the corpus is **multilingual** (78% Portuguese,
12% Spanish, 10% English), while queries can come in any language — which
makes retrieval genuinely hard and interesting to evaluate. The skew is the
hard part: an English question has to reach a Portuguese recipe, and four out
of five recipes are Portuguese.

## Dataset

One file, committed in [`data/`](data/) — no external downloads or
credentials needed: **`recipes-structured-v4.json`** (the app's entire
corpus; `recipes-structured-v3.json` is the previous snapshot, kept only so
early notebooks reproduce).

**Trust story in one sentence:** every recipe is a Claude (claude-fable-5)
extraction from a raw Instagram caption — silver tier, model-extracted,
unverified — carrying that raw caption as its source of truth, enriched
only by deterministic code; **nothing in this file was produced by a small
model.** Full provenance lives in `metadata` inside the file.

### Documents

356 docs, each with a mandatory `type`:

| `type` | Count | What it is |
|---|---|---|
| `recipe` | 339 | an atomic recipe: 286 single posts + 53 **child recipes** split out of multi-recipe posts (weekly meal preps). Children have shortcode `{parent}#{n}`, a `parent_shortcode`, **no `caption`** (it lives on the parent) and their photo under the parent's shortcode |
| `meal_plan` | 17 | a multi-recipe post: raw caption, plan-level `title`, and `recipe_ids` linking its children. Has **no** `recipe`/`complete`/`grade` — filter `type == "recipe"` before touching those fields |

### Fields and provenance

| Field | Notes | Obtained by |
|---|---|---|
| `shortcode`, `url`, `owner`, `date` | post identity; child ids are synthetic `{parent}#{n}` | Instagram scrape (instaloader) |
| `caption` | **raw caption — the source of truth** everything else derives from | scrape, never modified |
| `language` | ISO 639-1 (pt/es/en) | lingua library (no LLM) |
| `has_photo` | photo exists in the data platform (photos not shipped here) | filesystem check at export |
| `recipe` | `{title, ingredients[], steps[]}` in the caption's original language; empty list = read-but-absent | **Claude extraction** (in-session, 2026-07) |
| `complete` | title + ingredients + steps all non-empty | derived |
| `grade` | `clean` (104) / `sectioned` (166) / `noted` (66). Filter `grade != "noted"` for the easy pool: **270 recipes** with reliable ingredient merge keys | deterministic (`names.py`) |
| `recipe.ingredients[].name` | clean merge key; `name_raw` keeps the extracted string verbatim | deterministic split of Claude's names |
| `recipe.ingredients[].section` | dish component ("massa", "calda") — group by this in a recipe view | same splitter |
| `recipe.ingredients[].optional` | boolean, from "(opcional)" markers | same splitter |
| `recipe.ingredients[].quantity`, `.unit` | as the caption states them: 0 = unstated, ranges lowered to their minimum, units verbatim | Claude extraction |
| `recipe.ingredients[].amount` | interpreted amount `{type: measured\|counted\|to_taste, quantity, unit}` — `to_taste` has quantity `null`, never 0: don't sum it | deterministic (`amounts.py`) |

Known caveat for evaluation: 7 pairs of recipe-level duplicates (~2% of the
easy pool — creators repost recipes), so two doc ids can both be "correct"
for one question; ids in the platform's `docs/data-quality-issues.md` §7.

The dataset was produced by a separate data platform
([`recipe-data-platform`](https://github.com/setegonz/recipe-data-platform))
that scrapes my saved posts, syncs ground-truth collection membership, and
exports versioned snapshots. That repo is not needed to run this project —
but its `docs/data-quality-issues.md` catalogs every known data problem,
and its wider exports (all 3,732 bookmarks, raw caption corpus, llama3.2:3b
reference baselines) are available there if an experiment needs them.

## Plan

Built step by step in [`notebooks/`](notebooks/), then promoted into
[`app/`](app/). Every notebook is committed with its outputs, and every one
replays from a committed cache, so they re-run to the same numbers with no API
key.

| Notebook | What it establishes | Where it's discussed |
|---|---|---|
| [`rag.ipynb`](notebooks/rag.ipynb) | the first LLM call with no retrieval (the baseline that rewrites recipes), then the prompt, then the `{answer, recipe_ids, found}` envelope the whole project is scored on | "The app", below |
| [`eval-retrieval.ipynb`](notebooks/eval-retrieval.ipynb) | builds the 135-question multilingual answer key, then scores BM25 vs. hybrid, filtered and unfiltered | "Retrieval: cross-lingual search, resolved" |
| [`eval-retrieval-llm.ipynb`](notebooks/eval-retrieval-llm.ipynb) | diagnoses *where* retrieval fails, shows BM25 was hurting, then tests query rewriting and LLM reranking against a pre-set gate | "Retrieval, part 2" |
| [`eval-generation.ipynb`](notebooks/eval-generation.ipynb) | citation accuracy and refusal rate on top of the retrieval winner | "Generation: citation accuracy, measured" |
| [`eval-generation-prompts.ipynb`](notebooks/eval-generation-prompts.ipynb) | five prompts over one fixed retrieval, scored on citation accuracy, refusal calibration **and** answer language | "Generation, part 2" |

The structured envelope in `rag.ipynb` is what makes the rest cheap to measure:
the app renders each recipe card verbatim from the trusted JSON by `recipe_ids`
and the LLM never retypes ingredients, which yields refusal rate (`found == false`)
and citation accuracy (`recipe_ids` against that question's retrieved set) as
deterministic metrics, with no LLM judge.

Then, beyond the notebooks: the app and UI ("The app: search-first, not a chat"),
and the production shape — a scheduled Prefect flow building the Qdrant index,
user feedback in Postgres behind a Grafana dashboard, all in one
`docker compose up`.

## Retrieval: cross-lingual search, resolved

`search()` used to hardcode `language='pt'`, so the ~22% of the corpus in
es/en was excluded from every query regardless of the question's
language. Even without that filter, lexical/keyword matching (minsearch)
doesn't bridge languages well on its own — a Spanish query won't score
highly against Portuguese-vocabulary text.

Options considered:
1. Per-language query translation + fan-out search — translate the
   query into each corpus language, run separate lexical searches,
   merge. Straightforward with keyword indexes, but scores across the
   fan-out searches aren't on the same scale, so "merging" ends up
   quota-based, not truly ranked.
2. Cross-lingual embeddings, single index — embed docs and query with a
   multilingual model (`multilingual-e5`, Cohere embed-multilingual,
   OpenAI `text-embedding-3`) so semantically equivalent text in any
   language lands close in vector space. One query embedding retrieves
   across all languages, no translation or fan-out needed.
3. Hybrid: lexical + dense, fused — BM25/minsearch for exact-term
   precision (ingredient names) combined with the embeddings above for
   cross-lingual recall, merged with Reciprocal Rank Fusion (rank-based,
   so no cross-search score calibration needed).
4. Reranking on top of either — a multilingual cross-encoder
   (BGE-reranker-v2-m3, Cohere rerank) or the LLM itself scoring
   candidates, producing one calibrated relevance score regardless of
   which search surfaced the candidate.

> **Superseded — see "Retrieval, part 2" below.** This section records the
> decision as it was made. A later diagnostic showed option 2 (dense alone) was
> never measured in isolation, and it beats the hybrid shipped here.

**Decision: option 3, hybrid — implemented and measured.** BM25 stays
because exact ingredient-name matches matter for this corpus and are
often language-stable (e.g. "chia", "banana"); a multilingual
`minsearch.VectorSearch` index over `BAAI/bge-m3` embeddings (public,
runs locally, no HF token needed) is added alongside the existing
`minsearch.Index`, fused with Reciprocal Rank Fusion. Both live in
`notebooks/recipe_search.py`, shared by `eval-retrieval.ipynb` (`rag.ipynb`
still has its own older `search()` copy — left alone to preserve its
history).

Built a 135-question multilingual eval set (45 recipes x pt/es/en, one
generated question per language — `data/eval-retrieval-questions.json`)
and measured hit rate / MRR for BM25 alone vs. hybrid, both with and
without a language filter (`data/eval-retrieval-results.json`):

| | own-language filter | unfiltered |
|---|---|---|
| BM25 — hit rate / MRR | 33% / 0.31 | 53% / 0.44 |
| Hybrid — hit rate / MRR | 33% / 0.32 | **76% / 0.56** |

Filtering to the (detected/assumed) query language is actively harmful:
it mathematically guarantees 0% on every cross-language pair, which is
why "own" scores identically regardless of retrieval method — the filter,
not the method, is the bottleneck once it's on. **Final decision: no
language filter at all; unfiltered hybrid search.** A second embedding
model wasn't tested — the jump was large enough that model choice isn't
the next bottleneck; deprioritized in favor of the LLM-answer eval next.

## Retrieval, part 2: the hybrid was the problem

Before adding an LLM to retrieval, I asked a cheaper question first: *where*
does retrieval fail? Two diagnostics, no API calls
(`notebooks/eval-retrieval-llm.ipynb`).

**The failure is entirely cross-lingual.** Same-language questions score 100%
(45/45). All 33 misses are queries in one language against a recipe in another,
worst against pt — the dominant corpus language.

**And recall is not the problem.** Recall climbs 79% @5 → 91% @20 → **97% @50**.
The right recipe is almost always retrieved, just ranked too low. That is a
ranking problem, not a coverage one.

**Then the uncomfortable one: BM25 was making things worse.** The original
comparison pitted hybrid against BM25 and hybrid won — but *dense alone was never
measured*. It is the best of the three:

| method @5 | hit rate | cross-lingual | MRR |
|---|---|---|---|
| BM25 | 52.6% | 28.9% | 0.441 |
| hybrid (previously shipped) | 75.6% | 63.3% | 0.559 |
| **dense only** | **84.4%** | **76.7%** | **0.735** |

BM25 rescues **1** question dense misses; dense rescues **44** that BM25 misses.
A sweep of the RRF weighting improves monotonically as BM25's weight falls, all
the way to zero. Equal-weight RRF was fusing a good ranking with a near-noise one.

The earlier rationale — that exact ingredient names like "chia" and "banana" are
language-stable and worth a lexical index — was a reasonable hypothesis that the
measurement did not support: `bge-m3` already matches those terms.

**Then the LLM experiments**, both on top of dense, gated in advance at ≥10 points
cross-lingual with no same-language regression below 95%:

| method @5 | hit rate | cross-lingual | MRR | gate |
|---|---|---|---|---|
| dense (baseline) | 84.4% | 76.7% | 0.735 | — |
| dense + query rewriting | 91.1% | 87.8% | 0.809 | passes (+11.1) |
| **dense + LLM reranking** | **92.6%** | **88.9%** | **0.897** | **passes (+12.2)** |

*Query rewriting* expands the question into ingredient vocabulary in all three
languages before embedding. *Reranking* takes 20 dense candidates and has the LLM
order them.

**Shipped: dense + reranking.** Ahead on every metric, and the MRR gap is the real
story — 0.897 vs 0.559 for the old hybrid means the right recipe sits at rank 1,
not merely somewhere in the top 5. Rewriting scored close on hit rate but nicked
same-language accuracy (100% → 97.8%): the extra terms added enough noise to break
a question that previously worked.

The worst cell, en→pt, went **40% (hybrid) → 53.3% (dense) → 86.7% (reranked)**.

Two things worth being precise about:

- **Most of the win was deletion, not addition.** Of the +17 points over the old
  hybrid, **+8.8 came from removing BM25** and +8.2 from adding the LLM.
- **Reranking is near its ceiling.** It selects from 20 candidates where recall is
  ~91%, so 92.6% extracts nearly everything available. More gains need a larger
  candidate pool, not a better reranker. Rewriting *and* reranking together is
  untested; recall@50 of 97% says there is headroom left.

Both LLM outputs are cached in `data/eval-query-rewrites.json` and
`data/eval-rerank-results.json` and committed, so the notebook re-runs to
identical numbers with no API key.

## Generation: citation accuracy, measured

`03`'s structured `{answer, recipe_ids, found}` envelope gives two
deterministic metrics for free, no LLM judge needed: does the model say
`found` at all, and does `recipe_ids` contain the expected recipe. Reused
the same 135-question answer key, wired to hybrid unfiltered search (the
retrieval eval's winner) instead of `rag.ipynb`'s older pt-only `search()`
— scored in `eval-generation.ipynb`, saved to
`data/eval-generation-results.json`.

| Metric | Value |
|---|---|
| Retrieval hit rate | 75.6% |
| Found rate (didn't refuse) | 94.1% |
| Citation hit rate (overall) | 74.1% |
| **Citation hit rate, given retrieval surfaced the doc** | **98.0%** (n=102) |

**Generation isn't the bottleneck — retrieval is.** Conditioned on the
expected recipe actually being in context, the LLM cites it correctly 98%
of the time. The unconditional 74.1% is explained almost entirely by the
75.6% retrieval ceiling, which lines up with the retrieval eval's own 76%
hybrid-unfiltered hit rate — the two eval harnesses agree with each other.
Per-language breakdown confirms the same cross-lingual weak spot as the
retrieval eval: en/es queries against pt recipes are worst (40% / 46.7%
hit rate), since pt is the dominant corpus language.

Two issues found, tracked below rather than fixed yet: weak refusal
calibration on retrieval misses, and a citation bug on child recipes.

### Re-measured on the shipped retrieval

Re-run against dense + reranking (`data/eval-generation-rerank-results.json`),
same 135 questions:

| Metric | hybrid (before) | dense+rerank (now) |
|---|---|---|
| Retrieval hit rate | 75.6% | **92.6%** |
| Found rate (didn't refuse) | 94.1% | 99.3% |
| Citation hit rate (overall) | 74.1% | **91.9%** |
| Citation hit rate, given retrieval | 98.0% | 99.2% |

The retrieval gain converts almost exactly 1:1 into citation accuracy, which is
what the 98%-conditional figure predicted. The two harnesses agree again.

The child-recipe citation bug is gone: of 18 questions expecting a `{parent}#{n}`
recipe, 14 are cited correctly, and the single citation miss among all retrieval
hits cites a *different* child (`#3` instead of `#1`) rather than dropping the
suffix — a relevance disagreement, not a format error.

**Refusal calibration got worse, though.** On the 10 remaining retrieval misses,
only 1 was correctly refused (10%, vs 24% before). Reranking hands the answering
model a set already filtered by another LLM pass, which appears to raise its
confidence that something in there must be right. Small n, but the direction is
wrong and `found: false` is now even less trustworthy as a "we have nothing"
signal.

> Addressed below — see "Generation, part 2". Three sentences of prompt took
> correct refusals from 10% to 60% at identical citation accuracy.

## Generation, part 2: which prompt? (a clean A/B)

The two runs above are not a prompt comparison. Citation accuracy went
74.1% → 91.9%, but *retrieval and the prompt both changed* between them, so the
gain can't be attributed to either. `notebooks/eval-generation-prompts.ipynb`
fixes that: **retrieval is held constant** at the shipped dense+rerank top-5,
replayed from `data/eval-rerank-results.json`, and only the instructions vary
across the same 135 questions.

- **A — original**, the `eval-generation.ipynb` wording. No language rule at all.
- **B — shipped**, what `app/rag.py` ran: bare shortcode, keep the `#n` suffix,
  and *"answer in the language of the question, even when the recipes are in
  another language."*
- **C — refusal-calibrated**, B plus three sentences telling the model the context
  is search output, that a same-genre recipe is not a match, and that having
  nothing is a correct answer.
- **D — explicit language rule**, C with the language rule naming the three
  languages concretely and **no longer mentioning the recipes' language**.
- **E — language rule last**, C with that same sentence moved to the end,
  unchanged. D and E are one change each: wording versus placement.

Three metrics, because the first run of this eval only had two — see below. Gate
fixed before running: promote over B only if citation hit rate drops ≤1.5 points,
correct refusals improve ≥20 points, **and** the answer is in the question's
language ≥95% overall / ≥90% on English questions.

| variant | citation hit | cite ∣ retrieval | correct refusal | false refusal | answer language | on **en** |
|---|---|---|---|---|---|---|
| A original | 91.9% | 99.2% | 0% | 0% | 93.3% | 82.2% |
| B shipped | 91.1% | 98.4% | 10% | 0% | 76.3% | 31.1% |
| C refusal-calibrated | 91.1% | 98.4% | 60% | 0% | 74.8% | 26.7% |
| **D explicit language rule** | **91.1%** | **98.4%** | **70%** | **0%** | **98.5%** | **97.8%** |
| E language rule last | 89.6% | 96.8% | 60% | 0% | 73.3% | 22.2% |

**Shipped: D**, the only variant that passes. Correct refusals go 1/10 → 7/10,
answers land in the question's language 98.5% of the time, citation accuracy is
unchanged, and no question where retrieval succeeded was refused.

### The language instruction was causing the bug it was written to prevent

B introduced *"even when the recipes are in another language"* — and English-question
accuracy fell from **82.2% (A, which has no language rule at all) to 31.1%**. The
rule was worse than saying nothing, and it had been in production the entire time.

E isolates the cause. It is C with that exact sentence moved to the end of the list
and not one word changed: **22.2%** — no better. It was never placement. Naming the
recipes' language is what does the damage: the clause meant to exclude Portuguese
makes Portuguese salient, and the pull is strongest precisely where the context is
most Portuguese, which for a 78%-pt corpus is every English query. D names the
language to write in and never mentions the one to avoid: 97.8%.

**Name the thing you want, never the thing you are steering away from.**

### And the eval that missed it

The first version of this notebook scored citation accuracy and refusal
calibration, promoted C, and shipped it. A user then asked in English and got
Portuguese back. **A dimension nobody measures is free to go to zero** — the bug
entered with B, survived every eval run in this repo, and was caught by a person
using the app, not by a metric.

That is the same failure the `hallucinated_ids` column exists to prevent, one level
up: A leads on citation accuracy while refusing *nothing* and is the only variant
to emit an id absent from its own context. Scored on citation accuracy alone, this
eval would have promoted the worst prompt in the set.

### Retrieval, not the prompt

With retrieval held fixed, A and B differ by 0.7 points — one question. The entire
74.1% → 91.9% jump was retrieval, exactly as the 98%-conditional figure predicted;
the confounded before/after had been quietly crediting the prompt.

Every reply is cached in `data/eval-generation-prompts-cache.json` and committed,
so the notebook re-runs to identical numbers with no API key.

## The app: search-first, not a chat

`app/main.py` is a Streamlit app, and deliberately **not** a chat interface.
The evals say retrieval is the bottleneck (92.6% hit rate, and every remaining
miss is cross-lingual) while generation is fine (98.4% citation accuracy given
the doc was retrieved) — and that the model still answers confidently on 3 of
every 10 retrieval misses, even after the refusal-calibrated prompt. A chat UI is
the worst possible wrapper for that failure mode: it hides a miss inside one
fluent, confident paragraph.

Showing a **grid of 9 results** turns the same miss into something the user can
see and recover from — they scan and pick, instead of depending on the model to
correctly refuse. It's also simply the right shape for steps 2 and 3, which are
multi-select and accumulation, not conversation.

The LLM stays, subordinate: it writes the framing line above the grid and stars
the recipes it recommends, from the same `{answer, recipe_ids, found}` envelope
as `03`. Every ingredient and step below it is rendered from the trusted JSON,
so a wrong `#n` suffix mis-stars a card instead of rendering the wrong recipe.

| Module | What it does |
|---|---|
| `app/search.py` | promoted from `notebooks/recipe_search.py` (now a shim, so the notebooks still run) — `bge-m3` dense search plus the LLM `rewrite_query` / `rerank` helpers. BM25 lives on for the eval notebooks but the app no longer builds it |
| `app/vectorstore.py` | the persisted Qdrant index — connect, upsert, search |
| `app/rag.py` | the `RecipeReply` envelope and context builder, lifted from `eval-generation.ipynb` |
| `app/recipes.py` | ingredient formatting, section grouping, photo path resolution |
| `app/cart.py` | aggregates the picked recipes into one shopping list |
| `app/monitoring.py` | writes searches, thumbs and picks to Postgres |
| `app/main.py` | the Streamlit UI |

## Ingestion: the index is built ahead of time, not at startup

The app used to embed all 287 documents on every cold start, behind a Streamlit
cache — 2 GB of model download and a full re-embed before the first search. That
is fine for a notebook and wrong for an application, and it also meant the index
existed only inside one process's memory.

Embeddings now live in **Qdrant**, and the only thing that writes them is a
**Prefect** flow (`flows/ingest_flow.py`):

```
corpus JSON ──▶ read_corpus ──▶ corpus_fingerprint ──▶ embed ──▶ load ──▶ verify
                                       │                                    │
                                       └── unchanged? skip ────────────────▶ done
```

- **Retries** on the two tasks that touch the network, so a Qdrant restart mid-run
  doesn't lose the run.
- **A fingerprint** (sha256 over every shortcode + indexed text) short-circuits the
  expensive step, so the daily schedule costs nothing on the days nothing changed.
- **Idempotent loads:** point ids are a uuid5 of the shortcode, so a re-run upserts
  over the previous vectors instead of duplicating them.
- **`verify` fails the run** if the collection ends up empty or the wrong vector
  size, rather than leaving a half-built index for the app to serve.

Three entry points, one code path: `docker compose up` runs it at boot and then
serves the `0 4 * * *` schedule; `uv run python flows/ingest_flow.py --once` runs
it locally; `scripts/ingest.py` is the same steps without Prefect, for debugging.

**Prefect rather than Kestra** for one reason: the flow is ordinary Python that
imports the same `app/` modules the application does, so the code that writes the
index and the code that reads it cannot drift, and the whole thing runs
identically inside compose and on a laptop with no orchestrator server at all.

Swapping the store was held to the same standard as the retrieval changes: Qdrant
returns **byte-identical top-5 lists on all 135 eval questions** — 84.4% hit rate,
0.735 MRR, the same numbers as the in-process index. The migration is a
performance change, not a retrieval change, and it is measured as one.

One design rule carried over: **the store holds vectors and identity only** —
shortcode, language, type, title. Search returns *ids*, and every ingredient and
step still comes from the committed JSON. The index gets to say which recipe, never
what is in it.

## Monitoring: what users actually did

Three tables (`db/init.sql`), one per thing a user does — search, rate, pick — and
a Grafana dashboard provisioned from source, so it exists on a fresh
`docker compose up` with nothing to click.

Every search writes its question, detected language, rerank on/off, the shortcodes
returned, the `found` flag, what the model cited, and both latencies. On top of
that: 👍/👎 on the answer and on each card, and every add/remove to the shopping
list along with the rank the recipe was shown at.

The panels are chosen to watch the two things the evals say are actually weak:

| Panel | Why it's there |
|---|---|
| Thumbs-up rate + feedback over time | the ground truth the offline evals can't see |
| Searches that led to a pick | relevance signal that costs the user nothing — most people never click a thumb |
| Refusal calibration: claimed vs. rated | the known weak spot, watched directly: thumbs-down inside the "claimed a match" row is a miss the model presented as a hit |
| Cross-lingual reach by query language | the project's core difficulty in production: the corpus is 78% pt, so es/en queries must reach across |
| Retrieval latency, rerank on vs off | the cost side of the +8.2 points reranking buys |
| Most-picked recipes, with average rank shown | a picked recipe sitting at rank 7 is a ranking miss the user recovered from |

Plus a recent-searches log, for the thing no aggregate shows: the questions people
actually type.

Monitoring is best-effort by construction — every write is wrapped, and if
Postgres is gone the app keeps serving searches and the thumbs stop rendering.
A gap in a chart beats a broken search.

## The cart: a shopping list, not a list of ingredients

The first version merged on `ingredients[].name` and was almost useless. Two
breakfast recipes produced 16 lines including *aveia em flocos* and *rolled oats*
as separate items, and *leite desnatado* next to *milk*.

The root cause isn't only that the corpus is multilingual. **A recipe and a
shopping list need different granularity.** A recipe legitimately says "iogurte
grego zero"; a shopping list says "Greek yogurt", because you buy one tub. The
corpus has **1,139 distinct ingredient names, 826 of them appearing exactly
once** — `ovo`, `ovos`, `ovo médio`, `ovo grande ou extra` are four keys for eggs,
and 51 distinct names contain "leite".

Two fixes, deliberately different in kind:

**Names merge through an LLM-built vocabulary.** `scripts/build_ingredient_vocabulary.py`
maps all 1,139 names to a shopping item plus a store category, in pt/es/en, and
commits the result to `data/ingredient-vocabulary.json`. It is an **offline build
step, not a runtime call** — the cart stays instant, deterministic, and works with
no API key. **1,139 names → 568 shopping items.**

The failure that matters here is a *wrong* merge, not a missed one: collapsing
`leite` into `leite de coco` makes someone buy the wrong thing, while leaving two
lines is merely untidy. So the prompt is biased toward splitting, and the script
validates against explicit pairs before writing:

```
must merge:      aveia em flocos / rolled oats     -> rolled oats     OK
                 ovo médio / large egg             -> eggs            OK
must NOT merge:  leite desnatado / leite de coco   -> milk / coconut milk    OK
                 aveia em flocos / farinha de aveia -> rolled oats / oat flour OK
                 pasta de amendoim / peanut butter powder -> kept apart      OK
```

Run `--check` to re-validate without spending a call. An early version quietly
dropped ~30% of names from each batch and fell back to the raw name, which looked
identical to "no mapping needed" — the script now keys on an index and retries at
shrinking batch sizes rather than trusting the model to echo 40 strings back.

**Quantities convert deterministically, and only within a family.** Volume merges
with volume, weight with weight, never across: `400 ml` + `0.75 cup` of milk
becomes **580 ml**, but `200 g` + `0.5 cup` of oats stays as two parts, because
combining those needs a density this data does not have. `to_taste` is never
summed, and a stated quantity of `0` is reported as "amount not stated" rather
than silently dropped. Merging happens in ml/g but display scales back to a
natural unit — `5 ml` of baking powder reads as `1 tsp`.

The list groups by store category in walk-the-aisles order, and renders in en, pt
or es from a selector in the sidebar. The same two recipes now give **14 lines
instead of 16**, with milk and oats correctly combined.

## Known issues

Found while building the RAG notebook — tracked here until addressed.

- **Recipe cards render untranslated, in the source post's language.** By
  design — the card is rendered verbatim from trusted JSON so the LLM
  never retypes ingredients/quantities (see step `03` above). But it means
  a Spanish-speaking user can get a Portuguese-language ingredient card
  under a Spanish reply. No fix yet; needs a product decision (translate
  at render time? restrict retrieval to the query's language? show both?).

- ~~**Weak refusal calibration when retrieval misses — and reranking made it
  worse.**~~ **Mostly fixed** by prompt variant D above: correct refusals on the
  10 remaining misses went 1/10 → 7/10, with zero false refusals and no loss of
  citation accuracy, so `found: false` is now trustworthy *when it fires*. What
  remains is recall: **3 of 10 misses still get a confident answer**, and n=10 is
  small enough that 70% should be read as a direction, not a number. The in-app
  thumbs exist to grow that n with production data.

- ~~**Answers came back in the recipes' language, not the question's.**~~ **Fixed**
  by variant D. The instruction meant to prevent this was causing it: *"even when
  the recipes are in another language"* made English questions come back in the
  wrong language 69% of the time — Portuguese in half of those — which is worse
  than having no language rule at all. Now 97.8% correct
  on English. Two things this leaves behind — it was found by a user, not by an
  eval, and it was in production for the whole project because **answer language
  was never a scored metric**. It is one now, and it is in the gate.

- ~~**Shopping list doesn't merge singular/plural ingredient names.**~~ **Fixed**
  by the ingredient vocabulary above — `ovo`/`ovos`/`ovo médio` now collapse to
  one item. What remains is that **the vocabulary is unverified at scale**: 10
  pairs are asserted, and the largest merge groups were eyeballed, but the other
  ~560 items are the model's judgement taken on trust. A wrong merge is silent.

- ~~**Child recipes get cited by their parent's shortcode.**~~ **Fixed.** The
  prompt now asks explicitly for the full id including any `#n` suffix. Of 18
  questions expecting a child recipe, 14 are cited correctly, and no citation
  drops the suffix.

  Fixing it exposed a sharper lesson, worth recording. The first wording —
  *"copy each shortcode exactly as it appears"*, next to an example shown as
  `[DLQKkt_u6_R#2]` — made the model return `[DUatO3aDv61]` **with the brackets**,
  and citation accuracy collapsed to 0.7%. A one-line prompt edit silently broke
  an id used as a dictionary key. The prompt now asks for the bare shortcode, and
  `clean_shortcode()` in `app/rag.py` strips brackets defensively: **model output
  used as a lookup key gets normalized, never trusted as-is.**

## Setup

### Everything, in Docker

Requires Docker. Nothing else — no Python, no uv, no model download of your own.

```bash
cp .env.example .env      # optional: add OPENAI_API_KEY
docker compose up
```

| Service | URL | What it is |
|---|---|---|
| app | http://localhost:8501 | the Streamlit UI |
| grafana | http://localhost:3000 | the dashboard (`admin` / `admin`) |
| prefect | http://localhost:4200 | ingestion run history and schedule |
| qdrant | http://localhost:6333/dashboard | the vector index |
| postgres | localhost:5433 | feedback and search log |

The **first** `up` takes a while and is supposed to: `ingest` downloads
`BAAI/bge-m3` (~2 GB) and embeds the 287 documents into Qdrant before the app is
allowed to start. That ordering is enforced by a health check that passes only
once the collection actually has points in it, so the app never comes up pointing
at an empty index. Both the model and the index live in named volumes — every
later `up` starts in seconds.

Ports are overridable if they collide with something you already run:

```bash
APP_PORT=8502 GRAFANA_PORT=3001 docker compose up
```

### Without Docker

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12.

```bash
uv sync
uv run streamlit run app/main.py
```

With no Qdrant reachable the app builds the index in-process at startup instead —
same results (verified identical top-5 on all 135 eval questions), just slower to
boot. With no Postgres reachable the thumbs simply don't render, rather than
collecting feedback into a void. The footer says which mode you're in.

### The API key is optional

`OPENAI_API_KEY` in `.env` enables LLM reranking and the summary line. **Without
it the app still runs** on plain dense search — 84.4% vs 92.6% hit rate — and the
shopping list is unaffected either way, since the ingredient vocabulary is
prebuilt and committed. There is no local-LLM path: reranking and generation are
`gpt-5.4-mini` or nothing.

Every dependency version is pinned in `uv.lock`, and the image installs with
`uv sync --frozen`, so a build either resolves exactly what the evals ran against
or fails.

Rebuilding that vocabulary is only needed if the corpus gains new ingredient
names:

```bash
uv run python scripts/build_ingredient_vocabulary.py          # build (needs a key)
uv run python scripts/build_ingredient_vocabulary.py --check  # validate, no calls
```

### Photos (optional)

Recipe photos are Instagram posts whose copyright belongs to the people who
posted them, so they are **not committed to this repository**. Cards fall back
to a text-only layout when they're absent. To get them:

```bash
uv run python scripts/fetch_photos.py                 # from the GitHub Release
uv run python scripts/fetch_photos.py --source ~/pics # from a local directory
```

They land in `data/photos/` (gitignored), named by `shortcode`; child recipes
resolve to their `parent_shortcode`.
