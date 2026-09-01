# AgentGuard v4 Architecture — State Machine and Trust Boundaries

**Status: as built.** This document began as a design sketch and has been
reconciled against the implemented code (`workflow.py`, `audit_db.py`,
`proposal_hash.py`, `approval.py`, `verifier.py`, `remediation_templates.py`,
`github_plan.py`, `rollback.py`) and its tests. Where the original design and
the code disagreed, the code won — see **How this is verified** at the end. The
canonical transition map and its enforcement live in
[`docs/v4_state_machine.md`](v4_state_machine.md); this document adds the
per-state *data / authority / gate* view and the trust boundaries.

## The core question this design answers

v1, v2, and v3 only ever **read and score** — v3's whole architecture is about
where untrusted inventory data becomes safe to treat like a local file
(`docs/v3_architecture.md`). v4 is different: it can **change** an agent's
configuration (on synthetic data, via a draft pull request). So the question is
no longer just "where does data become trusted" but:

> **At each state of the remediation workflow, what data does the system hold,
> what is it allowed to *do* with that data, and which specific check must pass
> before it is allowed to do more?**

Every point where the system's *authority to act* increases is a trust boundary,
and every trust boundary is gated by one named, deterministic check.

## New terms

`docs/v4_state_machine.md` and `docs/v4_threat_model.md` define proposal, hash,
approval, verification, draft PR, rollback, and audit event in context. The
terms specific to this document:

- **State** — one named stage of the workflow (`PROPOSED`, `APPROVED`, …). The
  system is in exactly one state at a time for a given remediation.
- **Transition** — one allowed step from one state to another. Only the arrows
  drawn below are permitted.
- **Terminal state** — a state with no outgoing transition: `REJECTED`,
  `FAILED`, and `ROLLED_BACK`. The workflow stops there.
- **State-skipping** — attempting a transition that isn't drawn (e.g. `PROPOSED`
  straight to `VERIFIED`). Rejected outright.
- **Authority** — what the system is permitted to *do* in a given state, as
  opposed to what data it *holds*. Authority only increases when a check allows
  it.
- **Trust boundary** — a point between two states where authority increases, so
  a specific check must gate the transition. Everything before the boundary is
  "cannot do this yet" regardless of intent; everything after is allowed only
  because the check passed.
- **Isolated verification** — applying a proposed change to a throwaway copy of
  the environment and re-scanning it, so the real source is never touched during
  checking.
- **Dry-run** — emitting the exact commands that *would* run while changing
  nothing. The default for the GitHub step.
- **Draft PR** — a pull request marked not-ready; it cannot merge automatically.
- **Repo / branch / path allowlist** — the fixed set of one repository, one
  branch prefix, and one target file path that the GitHub step is permitted to
  touch. Anything else is refused.
- **Fail closed** — on any failed check, the workflow moves to a terminal state
  rather than continuing with partial results.

## State machine

```
  DISCOVERED
      │  v1 scanner runs (deterministic)
      ▼  (or → FAILED on a failed check)
  SCANNED
      │  deterministic rules select an allowlisted template → build a proposal
      ▼  (or → FAILED)
  PROPOSED ───────────────► REJECTED   (human rejects the proposal — terminal)
      │  human approval, bound to proposal hash + source hash
      ▼  (or → FAILED)
  APPROVED
      │  isolated apply + re-scan: all verification checks pass
      ▼  (or → FAILED — includes a stale approval: proposal/source hash no longer matches)
  VERIFIED
      │  repo/branch/path allowlist ok; dry-run reviewed; live run opted in
      ▼  (or → FAILED — gh auth / command error / allowlist miss)
  DRAFT_PR_CREATED
      │  the draft PR is closed and its branch deleted, before any merge
      ▼
  ROLLED_BACK   (terminal)
```

Every non-terminal state except `DRAFT_PR_CREATED` can also drop to `FAILED` on a
failed check. `DRAFT_PR_CREATED` has exactly one exit — `ROLLED_BACK` — because
once a draft PR exists, undoing it is a reversal, not a failure.

Rules that hold across the whole machine (all enforced by
`workflow.transition()`; see [`docs/v4_state_machine.md`](v4_state_machine.md)):

- **Skipping a state is rejected.** Each transition checks that the current
  state is exactly the expected predecessor. Every one of the ~70 `(from, to)`
  pairs not on the map raises `ValueError`.
- **Only `PROPOSED` can be rejected.** `REJECTED` is reachable from `PROPOSED`
  alone. Withdrawing sign-off later, or a stale approval, moves the workflow to
  `FAILED`, not `REJECTED` — there is no backward edge.
- **An approval cannot be reused after the source or proposal changes.** The
  `APPROVED → VERIFIED` step re-checks that the proposal hash and source hash
  still match what the human approved (`approval.validate_approval`); if either
  changed, that check fails and the workflow goes to `FAILED`.
- **`transition()` is a pure guard — it writes nothing.** The orchestrator
  records each step separately: `state = transition(state, "SCANNED");
  record_event(db, wf, "environment_scanned", state.state, {...})`. Terminal
  endings go through `workflow.record_terminal_state()`, which takes the step
  *and* appends the matching audit row (`workflow_rejected` / `workflow_failed`
  / `workflow_rolled_back`). Every legal transition becomes one durable,
  append-only row in the SQLite `workflow_events` table.
- **Fail closed.** `REJECTED`, `FAILED`, and `ROLLED_BACK` are terminal; there
  is no "continue anyway".

## What the system holds and may do at each state

| State | Data the system now holds | Authority at this state | Check that gates entry into this state |
|---|---|---|---|
| `DISCOVERED` | Synthetic agent inventory from v3's read-only MCP boundary, plus its SHA-256 provenance hash | Read only | v3's validation adapter (`discovery_adapter.py`, unchanged) accepted the data |
| `SCANNED` | + v1 deterministic findings and risk score per agent | Read only; the score is authoritative and **fixed** | v1's `scanner.py` ran — deterministic, no model involved |
| `PROPOSED` | + one `RemediationProposal`: template id, target agent, exact field edits, the finding it addresses, the **predicted** post-change score, the source hash | May *describe* one bounded change; **cannot apply it**. The AI layer may *explain* the proposal, exactly as v2 explains a finding | The proposal was built from one of the three allowlisted templates; deterministic rules chose *what* to propose; the AI proposed/explained only |
| `APPROVED` | + an `ApprovalRecord`: reviewer, decision, reason, timestamp, bound to the proposal hash **and** the source hash | Human intent is on record; the system **still cannot touch any real configuration** | A person approved *this exact proposal* against *this exact source*. Approve/reject is an explicit human action |
| `VERIFIED` | + a `VerificationResult` from applying the approved proposal to an **isolated temp copy** and re-scanning it | Proven that the change produces the predicted state — in isolation, not in production | Every verification check passed: predicted score reached, exactly one target changed, only allowlisted keys changed, data still serialises, HIGH-risk count did not increase |
| `DRAFT_PR_CREATED` | + the `agentguard/<id>` branch name; a live run additionally surfaces the draft-PR URL that `gh` prints. All on the **separate, private, synthetic** demo repository | A *proposed* change now exists on GitHub, in review state, **un-mergeable automatically** | Target repo, branch prefix, and file path are all on the allowlist; the dry-run plan was produced and reviewed; live execution was explicitly opted into (dry-run is the default) |
| `ROLLED_BACK` *(terminal)* | + a record of the reversal | None — the draft PR is closed and its branch deleted | Rollback was requested **before merge** (the only exit from `DRAFT_PR_CREATED`). Automatic rollback *after* merge is refused by `rollback_plan(merged=True)` — that needs a deliberate, reviewed `git revert` |
| `REJECTED` *(terminal)* | Whatever was held when a human rejected the proposal | None | Reachable from `PROPOSED` only |
| `FAILED` *(terminal)* | Whatever was held when a required check failed (including a withdrawn or stale approval) | None — fail closed | Reachable from every non-terminal state except `DRAFT_PR_CREATED` |

## The trust boundaries

Reading the workflow top to bottom, authority increases at six points. Each is a
boundary gated by a deterministic check:

1. **Data boundary (inherited from v3, unchanged).** Connected inventory →
   validated data the scanner can read. Enforced by `discovery_adapter.py`.
2. **Score boundary.** Only v1's `scanner.py` ever sets a risk score. A proposal
   carries a *predicted* score; nothing in the action layer — and no AI output —
   may set or change the real one.
3. **Approval boundary (`PROPOSED → APPROVED`).** Nothing proceeds without an
   `ApprovalRecord` bound to the exact proposal hash and source hash. A human
   made this decision.
4. **Verification boundary (`APPROVED → VERIFIED`).** Nothing proceeds without an
   isolated apply + re-scan in which every check passes. Software, not the
   human, confirms correctness.
5. **GitHub boundary (`VERIFIED → DRAFT_PR_CREATED`).** Nothing reaches a real
   (synthetic) repository except an approved *and* verified proposal, only
   within the repo/branch/path allowlist, dry-run by default, draft-only. There
   is no merge command anywhere in the code.
6. **Rollback boundary.** Automatic reversal is allowed only *before* merge
   (close PR, delete branch). After merge, the system refuses and requires a
   reviewed revert.

## What is NOT in this state machine

The **MCP discovery server is not in this workflow at any step.** It stays
exactly what v3 shipped: five read-only tools (`health_check`,
`list_agent_inventory`, `get_agent_by_name`, `list_tool_catalog`,
`list_agent_ownership`), no create/update/delete tool. v4 does **not** add a
sixth, write-capable tool. The action layer is a separate governed workflow so
that v3's server stays provably read-only forever and v4's new risk is isolated
to the new component. The reasoning is recorded in
`docs/v3_to_v4_handoff.md`.

## The one invariant this design must never break

Deterministic rules decide *what* to propose. Software verifies whether an
applied change is correct. A human approves *intent*. The AI layer may explain a
finding and propose a remediation — it may never approve, apply, verify, or
score. **v1's `scanner.py` remains the sole authority for the risk number**, from
v1 through v4 unchanged: a proposal *predicts* a score, it never *sets* one.

## How this is verified

Nothing in this document is asserted on faith — each claim maps to a test:

- **The transition map** — `tests/test_workflow.py` checks that *every* one of
  the ~70 `(from, to)` pairs not in `ALLOWED_TRANSITIONS` raises, that the only
  forward route to `VERIFIED` is the full path, and that terminal states are
  dead ends. `tests/test_failure_paths.py` adds the cross-module skips
  (e.g. `PROPOSED → VERIFIED`).
- **Each trust boundary** — `tests/test_approval.py` (approval bound to both
  hashes; stale approval rejected), `tests/test_verifier.py` +
  `verifier.require_verified` (a failed check blocks GitHub planning),
  `tests/test_github_plan.py` (repo/branch/path allowlist; draft-only; no merge
  token in any plan), `tests/test_rollback.py` (`merged=True` refused).
- **The audit trail** — `tests/test_audit_db.py` (append-only, ordered by `id`);
  `tests/test_workflow.py` proves every recorded run is a legal, ordered walk.
- **End to end, failing closed** — `evals/run_v4_evals.py` injects 10 bad
  inputs (state-skip, post-merge rollback, unapproved repo, risk-raising
  remediation, drifted approval, broken `gh`, …) and passes only if v4 refuses
  each, plus 2 positive controls.
- **One command** — `python scripts/run_release_gate.py` runs all of the above
  and ends `RELEASE GATE PASS for AgentGuard v4`.
