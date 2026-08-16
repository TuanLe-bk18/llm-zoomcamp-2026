# Agent handoff — MCP Advisor independent validation

## Goal

Finish the independent retrieval validation for `mcp-advisor` using the frozen 60-query bank in this package.

The objective is **evaluation only**. Do not change the production retrieval default, do not remove CrossEncoder, and do not change the Gemini Judge model.

## Repository

Target repository:

`TuanLe-bk18/llm-zoomcamp-2026`

Target project:

`mcp-advisor`

Relevant current files include:

- `data/servers.json`
- `data/documents.json`
- `data/eval/ground_truth.json`
- `src/evaluation/benchmark.py`
- `src/evaluation/llm_eval.py`

## Phase 1 — Import without contaminating the existing benchmark

Copy:

`validation_intents_v1.json`

to an appropriate new path such as:

`mcp-advisor/data/eval/validation_intents_v1.json`

Do **not** overwrite the existing `ground_truth.json`.

The 60 query strings are frozen. Do not rewrite, regenerate, or “improve” them.

## Phase 2 — Label ground truth against the current corpus

For every query:

1. Inspect `servers.json` / `documents.json`.
2. Identify every server that clearly satisfies the requested capability.
3. Check every explicit `hard_constraint`.
4. Add one or more exact corpus `server_id` values to `relevant_server_ids`.
5. If no server clearly satisfies the request, set `no_relevant_server=true` instead of forcing a match.
6. Fill `rationale`.
7. Add `label_evidence` entries containing at least:
   - `server_id`
   - evidence source/field or document reference
   - concise reason it satisfies the intent
   - concise constraint assessment
8. Set `label_status="labeled_pending_human_signoff"`.

Important: do not define ground truth merely by taking the Top-K output from Vector/Hybrid/CE. Candidate discovery may use corpus search/indexing, but final labels must be justified from the underlying server/document content.

Write the result to a new file, preferably:

`mcp-advisor/data/eval/validation_realistic_v1.json`

Keep metadata needed for auditability.

## Phase 3 — Prepare a concise human-review artifact

Create:

`mcp-advisor/data/eval/validation_realistic_v1_review.md`

For all 60 queries, show compactly:

- query ID and query
- assigned relevant server IDs, or `NO MATCH`
- one-sentence evidence/rationale
- hard-constraint pass/fail/unknown

Flag for special review:

- every `NO MATCH`
- every query with only a weak/uncertain candidate
- every constraint-heavy query where a required property is undocumented
- any query where more than 5 servers are marked relevant

Do not call the dataset “human-reviewed” until the human approves it.

## Phase 4 — Run independent retrieval benchmark

Use `validation_realistic_v1.json`, not the old synthetic file.

If necessary, make a minimal evaluation-only patch so `benchmark.py` accepts an eval-file argument instead of hard-coding `ground_truth.json`. Preserve the current search implementations and retrieval settings.

Compare:

- Keyword / BM25
- Vector
- Hybrid
- Hybrid + CrossEncoder

At minimum calculate:

- Hit@1
- Hit@5
- MRR
- N

Also add if straightforward:

- Recall@5 for multi-relevant labels
- p50/p95 latency
- metrics by query type:
  - simple_intent
  - constraint_heavy
  - ambiguous_realistic

Handle `no_relevant_server=true` separately; do not silently count those as ordinary retrieval misses.

Save machine-readable and human-readable results, e.g.:

- `data/eval/results/validation_v1_metrics.json`
- `docs/evaluation/validation_v1_report.md`

## Phase 5 — Compare with synthetic benchmark

Clearly distinguish:

- repaired synthetic benchmark: README-derived queries
- independent realistic validation: frozen intent-first queries

Explain any material change in ranking or metrics.

Specifically inspect:

- cases Vector misses but Hybrid+CE gets
- cases all retrieval methods miss
- constraint-heavy failures
- ambiguous-query failures

## Gemini / LLM Judge rule

Do **not** use Gemini to generate or rewrite this validation set.

Keep Judge model exactly:

`gemini-3.5-flash`

If API quota returns 429, stop Judge work and record it as `pending_due_to_quota`. Do not silently substitute `gemini-3.1-flash-lite` or any other model.

Retrieval benchmarking itself should not require Gemini.

## Final decision rule for this task

Do **not** make a production architecture change automatically.

Return:

1. labeled dataset
2. human-review artifact
3. benchmark metrics
4. latency comparison if available
5. key failure cases
6. recommendation: Vector default / Hybrid+CE default / conditional fallback architecture
7. exact reasoning

But leave any production-default promotion and dependency cleanup for a separate explicit decision.

## Acceptance checks

Before finishing, verify:

- [ ] exactly 60 frozen queries are preserved
- [ ] zero query text was generated from a ground-truth README
- [ ] every non-empty `relevant_server_ids` value exists in the current corpus
- [ ] every label has evidence
- [ ] multi-relevant labels are allowed
- [ ] no-match cases are explicit
- [ ] old `ground_truth.json` remains intact
- [ ] Gemini Judge model remains `gemini-3.5-flash`
- [ ] CrossEncoder code/dependencies remain intact
- [ ] no production default was changed
