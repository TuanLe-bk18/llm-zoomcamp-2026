# MCP Advisor — Independent Realistic Validation v1

## What this package is

This package provides a **frozen, independent 60-query intent bank** for validating MCP Advisor retrieval.

It exists to fix the evaluation-design problem in the current synthetic benchmark:

`server README -> LLM generates a query -> same server is declared ground truth`

That design is useful for a synthetic semantic-retrieval smoke test, but it can overestimate performance on real user requests because the query is derived from the answer source.

This v1 set instead follows:

`realistic user need -> freeze query -> inspect corpus -> assign all acceptable server IDs -> benchmark`

## Important status

- Query text: **frozen**
- Ground-truth server IDs: **not assigned yet**
- Query review: **assistant-curated**
- Human sign-off: **pending**
- Safe to run retrieval benchmark now: **NO**

Do not describe this dataset as “human-reviewed” in the capstone until a human has reviewed and signed off on the final labels.

## Composition

- 20 simple-intent queries
- 20 constraint-heavy queries
- 20 ambiguous/realistic queries
- Core language: English, to keep this validation focused on retrieval quality rather than multilingual behavior

The set intentionally includes realistic ambiguity and constraints such as read-only access, scoped permissions, local-only storage, sandboxing, and least-privilege access.

## Files

- `validation_intents_v1.json`: source of truth. Frozen query bank plus labeling metadata.
- `ground_truth_template_v1.json`: benchmark-compatible labeling template. **Do not benchmark while labels are empty.**
- `AGENT_HANDOFF.md`: exact procedure for the implementation/evaluation agent.
- `AGENT_PROMPT.txt`: short prompt to give the agent together with this package.
- `HUMAN_SIGNOFF.md`: final human review checklist.
- `MANIFEST.json`: file hashes.

## Methodology rules

1. **Never regenerate or paraphrase the 60 query texts while labeling.**
2. Do not use Gemini or any other LLM to create replacement queries from server READMEs.
3. Inspect the current `servers.json` / `documents.json` corpus and assign **all clearly acceptable servers**, not just one.
4. A query may legitimately have multiple `relevant_server_ids`.
5. A query may legitimately have no suitable server. Mark `no_relevant_server=true`; do not force a weak match.
6. Every assigned server ID must have evidence from the corpus explaining why it satisfies the intent and explicit hard constraints.
7. Do not use the output of the retrieval method being benchmarked as the sole authority for ground truth.
8. Keep the current synthetic benchmark for historical comparison, but label it clearly as synthetic.
9. Do not change the Gemini Judge model. If `gemini-3.5-flash` is quota-blocked, report Judge as pending.
10. Do not promote Vector to production default and do not delete CrossEncoder as part of this validation task.

## Retrieval evaluation

After labeling, run the same four methods under the same retrieval settings:

- Keyword / BM25
- Vector
- Hybrid
- Hybrid + CrossEncoder rerank

At minimum report:

- Hit@1
- Hit@5
- MRR
- number of evaluated queries
- result broken down by `simple_intent`, `constraint_heavy`, and `ambiguous_realistic`

Strongly recommended additions:

- Recall@5 for multi-relevant ground truth
- p50/p95 latency per method
- per-query failures, especially cases where Vector misses but CrossEncoder succeeds

Do not auto-promote a method based solely on the previous synthetic benchmark. Present both absolute and relative gaps and let the final architecture decision use the independent set.

## Current synthetic benchmark context

The previously repaired synthetic set produced approximately:

- Vector: Hit@1 49.0%, Hit@5 71.4%, MRR 0.566
- Hybrid + CrossEncoder: Hit@1 49.0%, Hit@5 81.6%, MRR 0.610

Those numbers remain useful as a synthetic baseline, but this independent set is the test that should carry more weight for production-default selection.
