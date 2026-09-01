# AgentGuard v4 State Machine

v4 applies the **allowlist** principle to process movement, not just to
tools. The MCP discovery server is exactly five read-only tools;
remediation is exactly three templates; and a remediation workflow may
only be in one of the states below and may only move along an arrow that
is explicitly listed. Any state or step not written here is refused.

This document is the map. `workflow.transition()` enforces it (see
**Enforcement** below); the durable audit log of every step
(`audit_db.py`) is Day 5 Labs 4–5.

## States

| State | Kind | What it means |
|---|---|---|
| `DISCOVERED` | active (start) | The agent inventory has been read in (read-only), with a SHA-256 provenance hash. |
| `SCANNED` | active | v1's deterministic findings and risk score are attached; the score is authoritative and fixed. |
| `PROPOSED` | active | One allowlisted `RemediationProposal` exists — it describes a bounded change and cannot apply it. |
| `APPROVED` | active | A human `ApprovalRecord` exists, bound to the proposal hash and the source hash. No real configuration is touched. |
| `VERIFIED` | active | The approved change was applied to an isolated throwaway copy and re-scanned; every verification check passed. |
| `DRAFT_PR_CREATED` | active | A draft pull request exists on the separate, private, synthetic demo repo. It cannot be merged automatically. |
| `ROLLED_BACK` | terminal | That draft PR was closed and its branch deleted. |
| `REJECTED` | terminal | A human rejected the proposal or withheld approval. |
| `FAILED` | terminal | A required check failed. The workflow stops — fail closed. |

`START_STATE` is `DISCOVERED`; nothing transitions into it.
`TERMINAL_STATES` is derived from the map as every state with no outgoing
arrow: `{ROLLED_BACK, REJECTED, FAILED}`.

## Transition map

| From | Allowed next states |
|---|---|
| `DISCOVERED` | `SCANNED`, `FAILED` |
| `SCANNED` | `PROPOSED`, `FAILED` |
| `PROPOSED` | `APPROVED`, `REJECTED`, `FAILED` |
| `APPROVED` | `VERIFIED`, `FAILED` |
| `VERIFIED` | `DRAFT_PR_CREATED`, `FAILED` |
| `DRAFT_PR_CREATED` | `ROLLED_BACK` |
| `ROLLED_BACK` | *(none — terminal)* |
| `REJECTED` | *(none — terminal)* |
| `FAILED` | *(none — terminal)* |

**Happy path:**
`DISCOVERED → SCANNED → PROPOSED → APPROVED → VERIFIED → DRAFT_PR_CREATED → ROLLED_BACK`

## Rules

- **State-skipping is rejected.** A step that is not on the map — for
  example `PROPOSED → VERIFIED`, or `DISCOVERED → APPROVED` — is refused.
  You cannot reach `VERIFIED` without passing through `APPROVED`, so you
  cannot verify a change no human approved.
- **Only `PROPOSED` can be rejected.** `REJECTED` is reachable from
  `PROPOSED` alone; withdrawing sign-off later moves the workflow to
  `FAILED`, not `REJECTED`.
- **The pre-GitHub states fail closed.** `DISCOVERED`, `SCANNED`,
  `PROPOSED`, `APPROVED`, and `VERIFIED` can each drop to `FAILED` on a
  failed check. `DRAFT_PR_CREATED` has one exit, `ROLLED_BACK`: once a
  draft PR exists, undoing it is a reversal, not a failure.
- **Every transition is a gated trust boundary.** Each arrow has its own
  check — an allowlisted template for `SCANNED → PROPOSED`, an explicit
  human decision for `PROPOSED → APPROVED`, a re-check of the proposal
  and source hashes for `APPROVED → VERIFIED`, an allowlisted
  repo/branch/path plus an opted-in live run for
  `VERIFIED → DRAFT_PR_CREATED`.

## Enforcement

`workflow.transition(current, next_state)` is the **only** way to change a
workflow's state. It is a pure guard:

- A legal step returns a **new** frozen `WorkflowState` with the same
  `workflow_id`. The input state object is never mutated, so the history
  is a chain of distinct records.
- An **unknown current state** raises
  `ValueError: Unknown current state: '<x>'`.
- An **unknown target state** raises
  `ValueError: Unknown target state: '<x>'`.
- A step **not on the map** — state-skipping, a self-loop, or moving out
  of a terminal state — raises
  `ValueError: Invalid transition: <from> -> <to>. Allowed from <from>: <list>`,
  where `<list>` is the sorted allowed next states or `none - terminal
  state`. The message names what *was* allowed, so the error teaches the
  map.

There is no "force" parameter and no silent fallback: an illegal move is
always an exception, never a no-op.

## Audit log

Every workflow event is appended as one row in the SQLite
`workflow_events` table (`audit_db.py`). The table is **append-only by
convention** — the module has no code that updates or deletes a row — so
the recorded history is immutable evidence.

| Column | Type | Meaning |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | insertion order — `ORDER BY id` is the true event sequence |
| `workflow_id` | `TEXT NOT NULL` | which remediation run |
| `event_type` | `TEXT NOT NULL` | what happened (`proposal_created`, `proposal_approved`, …) |
| `state` | `TEXT NOT NULL` | the workflow state at/after this event |
| `created_at` | `TEXT NOT NULL` | UTC ISO-8601 timestamp |
| `payload_json` | `TEXT NOT NULL` | the event's data as canonical (sorted-key) JSON |

`id`, not `created_at`, is the ordering key: two events can share a
timestamp (same millisecond, or a clock that did not advance) but never
an `id`.

`audit_db.initialize(path)` creates the table (idempotent).
`audit_db.record_event(path, workflow_id, event_type, state, payload)`
appends one row: it calls `initialize()` first, stamps `created_at` from
the machine's UTC clock, stores `payload` as sorted-key JSON, and uses
`?` placeholders so values are never parsed as SQL.

`audit_db.list_events(path, workflow_id) -> list[dict]` is the read path.
It returns every event for one workflow, in `ORDER BY id` order (so the
list order is the true sequence even when timestamps tie), each as a dict
with four keys — `event_type`, `state`, `created_at`, `payload` — with
`payload` deserialised back into a dict. A missing database or an unknown
`workflow_id` returns `[]`, not an error. Reading the list top to bottom
is how a reviewer reconstructs what a workflow did, without touching SQL.

`transition()` does not write anything - it stays a pure guard. The
convention the orchestrator follows is: take the step, then record it —
`state = transition(state, "SCANNED"); record_event(db, wf, "environment_scanned", state.state, {...})`.
So every legal transition becomes one durable row.

### Inspecting the log

The audit database is one plain SQLite file, and everything needed to
read it ships with Python — no SQLite CLI, no database GUI, no
third-party package.

- **One workflow's history:** `audit_db.list_events(path, workflow_id)`
  returns it as an ordered list of dicts. No SQL needed.
- **Anything else** (every workflow id, event counts, filtering by
  state, the raw stored JSON): open the file with the standard-library
  `sqlite3` module and run a `SELECT`.

```
python -c "import sqlite3; print(sqlite3.connect('data/audit.db').execute('SELECT id,workflow_id,state,event_type FROM workflow_events ORDER BY id').fetchall())"
```

Inspection is read-only: it only ever runs `SELECT`, so looking at the
log cannot change it.

## Guarantees under test

`tests/test_workflow.py` and `tests/test_audit_db.py` prove:

- **Only mapped arrows are accepted.** Every one of the ~70 `(from, to)`
  pairs not in `ALLOWED_TRANSITIONS` raises `ValueError` — not just a
  sampled few.
- **The only forward route to `VERIFIED` is the full path.** From each
  state on `DISCOVERED → SCANNED → PROPOSED → APPROVED → VERIFIED`, the
  single non-terminal next state is the next state on the path; every
  other allowed target is a drop to `FAILED` / `REJECTED`. No shortcut
  skips the scan, the proposal, the human, or the verifier.
- **Terminal states are dead ends.** From `REJECTED`, `FAILED`, or
  `ROLLED_BACK`, `transition()` to any state raises.
- **The audit log is a legal, ordered walk.** For any recorded run
  (happy, rejected, or failed), every consecutive pair of `state` values
  in `list_events()` is a legal arrow, and the list is in the true order
  the events happened — even across interleaved writes from other
  workflows.

## Reconciliation with `docs/v4_architecture.md`

`docs/v4_architecture.md` (Day 1 Lab 7) sketched the machine before the
code existed and shows two arrows this implemented map does **not**
include:

- `APPROVED → REJECTED` — the implemented map has `APPROVED → {VERIFIED,
  FAILED}`; withdrawing approval is a `FAILED`, not a `REJECTED`.
- `DRAFT_PR_CREATED → FAILED` — the implemented map has
  `DRAFT_PR_CREATED → {ROLLED_BACK}` only.

The Day-1 prose also mentions a stale approval sending the workflow
"back to `PROPOSED` / `REJECTED`"; there is no backward edge — a stale
approval fails the `APPROVED → VERIFIED` check and the workflow goes to
`FAILED`. `workflow.py` and this document are authoritative; the Day-1
narrative doc is scheduled for reconciliation in Day 10 Lab 5.
