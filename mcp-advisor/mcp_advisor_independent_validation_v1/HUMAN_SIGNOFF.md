# Human sign-off — MCP Advisor validation v1

This checklist is intentionally short. The implementation agent should first produce `validation_realistic_v1_review.md`, which contains the 60 labeled queries and evidence.

## Human review

Review the agent-produced label report and confirm:

- [ ] Query wording still looks like realistic user requests and none were rewritten to resemble a selected server README.
- [ ] Ground-truth servers are plausible answers to the user need.
- [ ] Explicit hard constraints are actually supported by evidence rather than inferred without documentation.
- [ ] Multiple valid servers are retained where appropriate instead of forcing a single “correct” repo.
- [ ] `NO MATCH` is used when the corpus does not contain a defensible answer.
- [ ] Uncertain/undocumented claims are marked as such.
- [ ] The old README-derived synthetic dataset is not presented as the independent validation set.

## Sign-off state

Until a human checks the items above, report the dataset as:

`assistant-curated / corpus-labeled / human-signoff-pending`

After approval, it may be reported as:

`human-reviewed independent validation set`
