# AgentGuard v2 — Evaluation Report

## Summary

v1's deterministic scanner is unchanged and still fully covered by
regression tests. The v2 AI explanation layer sits on top of it, and every
claim it makes is independently checked before anything is shown: its
reported risk score must match the scanner exactly, and every citation
must point at real, retrieved policy text. All checks below pass as of
this report.

## Release Gate Output

One command proves both proofs together (Day 7 · Lab 7):

```
$ python evals/run_v2_evals.py
>>> python -m pytest -q
...............................................                          [100%]
52 passed in 0.38s
V2-001: PASS level=HIGH citations=True
V2-002: PASS level=NO RISK FOUND citations=True
V2-003: PASS level=HIGH citations=True
V2 EVALUATION PASS: 3 of 3 cases passed
FULL REGRESSION AND EVALUATION MATRIX PASS
```

## Case-by-Case Results

Golden cases from `evals/v2_cases.json`, run against
`sample_environment_before.json` in mock mode:

| Case | Agent | Expected level | Actual level | Citations | Result |
|---|---|---|---|---|---|
| V2-001 | Customer Support Agent | HIGH | HIGH | Yes | PASS |
| V2-002 | Research Agent | NO RISK FOUND | NO RISK FOUND | Yes | PASS |
| V2-003 | Deployment Agent | HIGH | HIGH | Yes | PASS |

Two HIGH-risk agents and one NO RISK FOUND agent — matching `CLAUDE.md`'s
required v1 evidence for the BEFORE environment exactly.

## Citation Validation

Every citation is checked two ways before it can reach a user:

1. `grounding.validate_grounding()` (Day 5 · Lab 6/7) rejects any citation
   whose `chunk_id` isn't real retrieved evidence, or whose quote doesn't
   genuinely appear in that chunk's text.
2. `tests/test_v2_service.py::test_every_citation_is_valid_for_every_agent`
   (Day 7 · Lab 3) independently re-runs this check for all 3 real
   synthetic agents, not just one hand-built example — proving the
   guardrail engages on the real pipeline entry point (`analyze_agent()`),
   not only in isolation.

## Mock vs. Live Comparison

One real, billed live call was made during Day 6 · Lab 6 (with explicit
approval given at the time) and reused for this comparison — no new live
spend was needed to produce this report:

| | Mock (free) | Live (real, Day 6 · Lab 6/7) |
|---|---|---|
| Risk level | HIGH | HIGH |
| Risk score | 60 | 60 |
| Model | `mock` | `claude-sonnet-5` |
| Input / output tokens | 0 / 0 | 2,225 / 419 |
| Latency | ~0ms | ~10s |
| Estimated cost | $0.00 | $0.013 |
| Citations | Real, grounded | Real, grounded (`AGP-003-S01`, `AGP-003-S02`) |

Risk level and score match exactly; only the explanatory prose differs —
proof that adding the AI layer never changed what v1's scanner decides.

## Latency, Tokens, And Estimated Cost

Mock mode is free and near-instant by construction — every mock
`UsageRecord` reports `input_tokens=0`, `output_tokens=0`,
`estimated_cost_usd=0.0` (`v2_service.py`). Every evaluation run now
writes this data to a local, gitignored audit trail
(`audit_events.jsonl`, Day 7 · Lab 5/6) instead of only printing it once
to a terminal that scrolls away. The one live sample on record (above)
cost $0.013 against a $5 monthly spend limit set in Day 2.

## Failures

None currently open. Two real bugs were found and fixed during Day 6 ·
Lab 6's first live call — missing `.env` loading in the pipeline's real
entry point, and unsupported JSON Schema keywords rejected by the live
API — both fixed the same lab and covered by tests since.

## Follow-Up Actions

- Complete the human relevance/completeness review for all 3 golden cases
  (Day 7 · Lab 4 added the scaffold; `relevance_reviewed` /
  `completeness_reviewed` are still `null` in `evals/v2_cases.json`,
  waiting on an actual reviewer's judgment call — not something the AI can
  fill in for itself).
- Wire `v2_service.py` and this evaluation/audit infrastructure into the
  live Streamlit app (`app_v2.py`) — Day 8's explicit scope, not a gap in
  Day 7.
- Consider expanding the golden case set beyond the current 3 agents as
  new scanner rules or policy documents are added.

## Evidence Sources

Every figure above is traceable to a specific, real command run recorded
in `notes/learning_log.md`:

- Release gate output, case results: Day 7 · Lab 7
- Citation validation: Day 5 · Lab 6/7, Day 7 · Lab 3
- Mock vs. live comparison, tokens/latency/cost: Day 6 · Lab 6/7
- Audit trail mechanism: Day 7 · Lab 5/6
- Review-field scaffold: Day 7 · Lab 4
- v1 regression baseline: Day 1 · Lab 5
