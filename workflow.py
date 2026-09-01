"""The v4 workflow state machine - an allowlist for process movement.

v4 already allowlists tools (the MCP server is exactly five read-only
tools) and remediations (exactly three templates). This file applies the
same principle to the *process*: a remediation may only be in one of the
states in `STATES`, and may only move along an arrow listed in
`ALLOWED_TRANSITIONS`. Any state or step not written here is refused.

`transition()` is the single guard every state change goes through: it
returns a new `WorkflowState` for a legal step and raises a clear
`ValueError` for anything else. It is pure - it writes nothing.

`record_terminal_state()` (Day 8 Lab 4) is the one helper that takes a
terminal step (REJECTED / FAILED / ROLLED_BACK) *and* appends the matching
row to the SQLite audit log (`audit_db.py`), so a workflow that ends
without succeeding is recorded, not silently dropped.
"""

from __future__ import annotations

from dataclasses import dataclass

from audit_db import record_event

# Every state a remediation workflow can be in, in workflow order.
STATES = (
    "DISCOVERED",        # agent inventory read in (read-only) + provenance hash
    "SCANNED",           # v1 deterministic findings + risk score attached
    "PROPOSED",          # one allowlisted RemediationProposal exists
    "APPROVED",          # a human ApprovalRecord exists, bound to the hashes
    "VERIFIED",          # approved change applied to an isolated copy, checks pass
    "DRAFT_PR_CREATED",  # draft PR open on the private synthetic demo repo
    "ROLLED_BACK",       # that draft PR closed and its branch deleted
    "REJECTED",          # a human rejected the proposal / withheld approval
    "FAILED",            # a required check failed - fail closed
)

# For each state, the complete set of states it may move to next.
# A state mapped to an empty set is terminal: the workflow stops there.
ALLOWED_TRANSITIONS = {
    "DISCOVERED": {"SCANNED", "FAILED"},
    "SCANNED": {"PROPOSED", "FAILED"},
    "PROPOSED": {"APPROVED", "REJECTED", "FAILED"},
    "APPROVED": {"VERIFIED", "FAILED"},
    "VERIFIED": {"DRAFT_PR_CREATED", "FAILED"},
    "DRAFT_PR_CREATED": {"ROLLED_BACK"},
    "ROLLED_BACK": set(),
    "REJECTED": set(),
    "FAILED": set(),
}

# Derived from the map so it can never drift: the states with no way out.
TERMINAL_STATES = frozenset(
    state for state, nexts in ALLOWED_TRANSITIONS.items() if not nexts
)

# The one state a workflow starts in. Nothing transitions into it.
START_STATE = "DISCOVERED"


@dataclass(frozen=True)
class WorkflowState:
    """Where one workflow currently is.

    Frozen: to move the workflow you build a *new* `WorkflowState`
    (via `transition()`, Day 5 Lab 3) - you never edit this one, so the
    history is a chain of distinct records rather than one mutated value.
    """

    workflow_id: str
    state: str


def is_terminal(state: str) -> bool:
    """True if `state` has no outgoing transition (the workflow ends here)."""
    return state in TERMINAL_STATES


def transition(current: WorkflowState, next_state: str) -> WorkflowState:
    """Move a workflow from `current` to `next_state`, or raise.

    The only way to change a workflow's state. A legal step returns a new
    frozen `WorkflowState` with the same `workflow_id`. Anything else -
    an unknown state, or a step not on the map (state-skipping, or moving
    out of a terminal state) - raises `ValueError` with a message that
    names the states and lists what was allowed.
    """
    if current.state not in ALLOWED_TRANSITIONS:
        raise ValueError(f"Unknown current state: {current.state!r}")
    if next_state not in STATES:
        raise ValueError(f"Unknown target state: {next_state!r}")

    allowed = ALLOWED_TRANSITIONS[current.state]
    if next_state not in allowed:
        options = ", ".join(sorted(allowed)) if allowed else "none - terminal state"
        raise ValueError(
            f"Invalid transition: {current.state} -> {next_state}. "
            f"Allowed from {current.state}: {options}"
        )

    return WorkflowState(current.workflow_id, next_state)


# --- Day 8 Lab 4: record a workflow that ends without succeeding ------------
#
# A remediation can end three ways that are not success: REJECTED (a human
# declined), FAILED (a required check failed - fail closed), ROLLED_BACK (a
# draft PR was closed and its branch deleted). The audit trail must record
# those endings as deliberately as it records a successful step, so the log
# never just goes quiet. `record_terminal_state()` is the one place that
# does "take the terminal step, then record it".
#
# `transition()` above stays a pure guard - it writes nothing. This helper
# is a separate function that calls the guard and then `audit_db.record_event`.

# The fixed audit `event_type` written for each terminal state.
TERMINAL_EVENT_TYPES = {
    "REJECTED": "workflow_rejected",
    "FAILED": "workflow_failed",
    "ROLLED_BACK": "workflow_rolled_back",
}


def record_terminal_state(
    db_path,
    current: WorkflowState,
    terminal_state: str,
    *,
    reason: str,
    details: dict | None = None,
) -> WorkflowState:
    """Move `current` to a terminal state and append one audit event for it.

    `terminal_state` must be one of REJECTED / FAILED / ROLLED_BACK - this
    helper only records an *ending*. The move goes through `transition()`,
    so an illegal arrow (`SCANNED -> ROLLED_BACK`, a second terminal step
    out of an already-terminal state, ...) raises *before* anything is
    written - the log can never show a terminal state the state machine
    would have rejected.

    `reason` is required, keyword-only, and non-empty: an unsuccessful
    ending with no recorded "why" is not a useful audit record. `details`
    is optional structured extra data. The stored payload is
    `{**details, "reason": reason}` - the explicit `reason` always wins.

    Returns the new frozen `WorkflowState`.
    """
    if terminal_state not in TERMINAL_STATES:
        raise ValueError(
            f"record_terminal_state is only for terminal states "
            f"{sorted(TERMINAL_STATES)}, not {terminal_state!r}"
        )
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("reason must be a non-empty string")

    new_state = transition(current, terminal_state)

    payload = dict(details or {})
    payload["reason"] = reason.strip()
    record_event(
        db_path,
        new_state.workflow_id,
        TERMINAL_EVENT_TYPES[terminal_state],
        new_state.state,
        payload,
    )
    return new_state
