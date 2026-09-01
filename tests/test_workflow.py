"""Tests for workflow.py - Day 5 Lab 2 (the state list and transition map).

The property under test: the map is a well-formed allowlist for process
movement. Every state is known, every arrow points somewhere real, the
three terminal states have no way out, the happy path is fully connected,
and known state-skips are absent. Enforcement (transition()) is Lab 3.
"""

from dataclasses import FrozenInstanceError

import pytest

from audit_db import list_events
from workflow import (
    ALLOWED_TRANSITIONS,
    START_STATE,
    STATES,
    TERMINAL_EVENT_TYPES,
    TERMINAL_STATES,
    WorkflowState,
    is_terminal,
    record_terminal_state,
    transition,
)

HAPPY_PATH = [
    "DISCOVERED", "SCANNED", "PROPOSED", "APPROVED",
    "VERIFIED", "DRAFT_PR_CREATED", "ROLLED_BACK",
]


# --- the map is complete and internally consistent --------------------------

def test_every_state_has_exactly_one_transition_entry():
    assert set(ALLOWED_TRANSITIONS) == set(STATES)


def test_states_has_no_duplicates():
    assert len(STATES) == len(set(STATES))


def test_every_transition_target_is_a_known_state():
    for state, nexts in ALLOWED_TRANSITIONS.items():
        for target in nexts:
            assert target in STATES, f"{state} -> {target} is not a known state"


def test_every_transition_value_is_a_set():
    for nexts in ALLOWED_TRANSITIONS.values():
        assert isinstance(nexts, (set, frozenset))


# --- terminal states -------------------------------------------------------

def test_terminal_states_are_exactly_the_three_endings():
    assert TERMINAL_STATES == frozenset({"ROLLED_BACK", "REJECTED", "FAILED"})


def test_terminal_states_have_no_outgoing_transitions():
    for state in TERMINAL_STATES:
        assert ALLOWED_TRANSITIONS[state] == set()
        assert is_terminal(state)


def test_non_terminal_states_are_not_terminal():
    for state in STATES:
        if state not in TERMINAL_STATES:
            assert not is_terminal(state)
            assert ALLOWED_TRANSITIONS[state], f"{state} has no way forward"


# --- shape of the map ----------------------------------------------------------

def test_the_pre_github_active_states_can_all_fail_closed():
    for state in ["DISCOVERED", "SCANNED", "PROPOSED", "APPROVED", "VERIFIED"]:
        assert "FAILED" in ALLOWED_TRANSITIONS[state]


def test_draft_pr_created_only_leads_to_rolled_back():
    assert ALLOWED_TRANSITIONS["DRAFT_PR_CREATED"] == {"ROLLED_BACK"}


def test_a_proposal_can_be_rejected_only_from_proposed():
    rejecters = {s for s, nexts in ALLOWED_TRANSITIONS.items() if "REJECTED" in nexts}
    assert rejecters == {"PROPOSED"}


# --- start, happy path, and skips --------------------------------------------

def test_start_state_has_no_inbound_transitions():
    assert START_STATE == "DISCOVERED"
    for state, nexts in ALLOWED_TRANSITIONS.items():
        assert START_STATE not in nexts, f"{state} -> {START_STATE} should not exist"


def test_the_happy_path_is_fully_connected():
    for current, nxt in zip(HAPPY_PATH, HAPPY_PATH[1:]):
        assert nxt in ALLOWED_TRANSITIONS[current], f"{current} -> {nxt} missing"


@pytest.mark.parametrize(
    "current, skipped",
    [
        ("DISCOVERED", "APPROVED"),
        ("DISCOVERED", "PROPOSED"),
        ("SCANNED", "APPROVED"),
        ("PROPOSED", "VERIFIED"),
        ("PROPOSED", "DRAFT_PR_CREATED"),
        ("APPROVED", "DRAFT_PR_CREATED"),
        ("VERIFIED", "ROLLED_BACK"),
    ],
)
def test_known_state_skips_are_absent_from_the_map(current, skipped):
    assert skipped not in ALLOWED_TRANSITIONS[current]


# --- WorkflowState -----------------------------------------------------------

def test_workflowstate_holds_an_id_and_a_state():
    ws = WorkflowState("wf-1", "DISCOVERED")
    assert ws.workflow_id == "wf-1"
    assert ws.state == "DISCOVERED"


def test_workflowstate_is_frozen():
    ws = WorkflowState("wf-1", "DISCOVERED")
    with pytest.raises(FrozenInstanceError):
        ws.state = "APPROVED"


# --- Day 5 Lab 3: transition validation -------------------------------------
#
# transition() is the only way to change state. A legal step returns a new
# WorkflowState; anything else raises a clear ValueError.

ALL_ALLOWED_ARROWS = [
    (current, nxt)
    for current, nexts in ALLOWED_TRANSITIONS.items()
    for nxt in nexts
]


def test_the_happy_path_runs_through_transition():
    state = WorkflowState("wf-1", "DISCOVERED")
    for nxt in HAPPY_PATH[1:]:
        state = transition(state, nxt)
    assert state.state == "ROLLED_BACK"
    assert state.workflow_id == "wf-1"


@pytest.mark.parametrize("current, nxt", ALL_ALLOWED_ARROWS)
def test_every_allowed_arrow_is_accepted(current, nxt):
    result = transition(WorkflowState("wf-1", current), nxt)
    assert isinstance(result, WorkflowState)
    assert result.state == nxt
    assert result.workflow_id == "wf-1"


def test_transition_returns_a_new_object_and_leaves_the_input_alone():
    before = WorkflowState("wf-1", "DISCOVERED")
    after = transition(before, "SCANNED")
    assert after is not before
    assert before.state == "DISCOVERED"   # unchanged


@pytest.mark.parametrize(
    "current, skipped",
    [
        ("DISCOVERED", "APPROVED"),
        ("DISCOVERED", "PROPOSED"),
        ("SCANNED", "APPROVED"),
        ("PROPOSED", "VERIFIED"),
        ("PROPOSED", "DRAFT_PR_CREATED"),
        ("APPROVED", "DRAFT_PR_CREATED"),
    ],
)
def test_state_skipping_raises_a_clear_error(current, skipped):
    with pytest.raises(ValueError, match="Invalid transition"):
        transition(WorkflowState("wf-1", current), skipped)


def test_a_self_loop_is_rejected():
    with pytest.raises(ValueError, match="Invalid transition"):
        transition(WorkflowState("wf-1", "DISCOVERED"), "DISCOVERED")


def test_an_unknown_target_state_is_rejected():
    with pytest.raises(ValueError, match="Unknown target state"):
        transition(WorkflowState("wf-1", "DISCOVERED"), "PUBLISHED")


def test_an_unknown_current_state_is_rejected():
    with pytest.raises(ValueError, match="Unknown current state"):
        transition(WorkflowState("wf-1", "PUBLISHED"), "SCANNED")


@pytest.mark.parametrize("terminal", ["ROLLED_BACK", "REJECTED", "FAILED"])
def test_you_cannot_move_out_of_a_terminal_state(terminal):
    with pytest.raises(ValueError, match="terminal"):
        transition(WorkflowState("wf-1", terminal), "SCANNED")


def test_the_error_message_names_the_attempt_and_an_allowed_step():
    with pytest.raises(ValueError) as exc:
        transition(WorkflowState("wf-1", "PROPOSED"), "VERIFIED")
    message = str(exc.value)
    assert "PROPOSED -> VERIFIED" in message
    assert "APPROVED" in message   # one of the genuinely-allowed next states


# --- Day 5 Lab 7: control flow cannot jump ahead ----------------------------
#
# Lab 3 spot-checked a handful of skips. These tests state the whole
# guarantee: only the arrows on the map are ever accepted, the only route
# to VERIFIED is the full path, and a terminal state is a dead end.

FULL_PATH = ["DISCOVERED", "SCANNED", "PROPOSED", "APPROVED", "VERIFIED"]


def test_no_illegal_transition_is_ever_accepted():
    # Every from->to pair that is not on the map must raise. ~70 pairs.
    for from_state in STATES:
        for to_state in STATES:
            if to_state in ALLOWED_TRANSITIONS[from_state]:
                continue
            with pytest.raises(ValueError):
                transition(WorkflowState("wf-1", from_state), to_state)


def test_the_only_route_from_discovered_to_verified_is_the_full_path():
    # Walking the exact prefix works...
    state = WorkflowState("wf-1", "DISCOVERED")
    for nxt in FULL_PATH[1:]:
        state = transition(state, nxt)
    assert state.state == "VERIFIED"

    # ...and at each point on that path, the ONLY way to keep going is the
    # next path step. Every other allowed target is a drop to a terminal
    # (FAILED / REJECTED); there is no forward shortcut.
    for here, forward in zip(FULL_PATH, FULL_PATH[1:]):
        allowed = ALLOWED_TRANSITIONS[here]
        assert forward in allowed
        non_terminal_targets = {s for s in allowed if s not in TERMINAL_STATES}
        assert non_terminal_targets == {forward}


@pytest.mark.parametrize(
    "current, skipped, gate_bypassed",
    [
        ("SCANNED", "APPROVED", "the proposal step"),
        ("PROPOSED", "VERIFIED", "the human approval"),
        ("APPROVED", "DRAFT_PR_CREATED", "the verifier"),
        ("SCANNED", "VERIFIED", "proposal + approval"),
        ("DISCOVERED", "PROPOSED", "the scan"),
    ],
)
def test_a_security_critical_gate_cannot_be_skipped(current, skipped, gate_bypassed):
    with pytest.raises(ValueError, match="Invalid transition"):
        transition(WorkflowState("wf-1", current), skipped)


@pytest.mark.parametrize("terminal", sorted(TERMINAL_STATES))
def test_a_terminal_state_is_a_dead_end_to_every_other_state(terminal):
    for other in STATES:
        with pytest.raises(ValueError):
            transition(WorkflowState("wf-1", terminal), other)


# --- Day 8 Lab 4: record_terminal_state ------------------------------------
#
# One helper that takes a terminal step (REJECTED / FAILED / ROLLED_BACK)
# AND writes the matching audit row, so a workflow that ends without
# succeeding is recorded, not silently dropped. It reuses transition() for
# the guard and audit_db.record_event() for the write.

# (from_state, terminal_state) pairs that ARE legal terminal endings.
LEGAL_TERMINAL_ENDINGS = [
    ("DISCOVERED", "FAILED"),
    ("SCANNED", "FAILED"),
    ("PROPOSED", "FAILED"),
    ("APPROVED", "FAILED"),
    ("VERIFIED", "FAILED"),
    ("PROPOSED", "REJECTED"),
    ("DRAFT_PR_CREATED", "ROLLED_BACK"),
]


@pytest.mark.parametrize("from_state, terminal_state", LEGAL_TERMINAL_ENDINGS)
def test_record_terminal_state_moves_and_records_the_ending(tmp_path, from_state, terminal_state):
    db = tmp_path / "audit.db"
    start = WorkflowState("wf-1", from_state)

    result = record_terminal_state(db, start, terminal_state, reason="a plain reason")

    assert result == WorkflowState("wf-1", terminal_state)
    events = list_events(db, "wf-1")
    assert len(events) == 1
    assert events[0]["state"] == terminal_state
    assert events[0]["event_type"] == TERMINAL_EVENT_TYPES[terminal_state]
    assert events[0]["payload"] == {"reason": "a plain reason"}


def test_the_three_terminal_event_types_are_distinct_and_named():
    assert TERMINAL_EVENT_TYPES == {
        "REJECTED": "workflow_rejected",
        "FAILED": "workflow_failed",
        "ROLLED_BACK": "workflow_rolled_back",
    }
    assert set(TERMINAL_EVENT_TYPES) == TERMINAL_STATES


def test_details_are_merged_into_the_payload(tmp_path):
    db = tmp_path / "audit.db"
    result = record_terminal_state(
        db,
        WorkflowState("wf-1", "APPROVED"),
        "FAILED",
        reason="stale approval",
        details={"proposal_sha256": "abc123", "check": "hash_match"},
    )
    assert result.state == "FAILED"
    (event,) = list_events(db, "wf-1")
    assert event["payload"] == {
        "proposal_sha256": "abc123",
        "check": "hash_match",
        "reason": "stale approval",
    }


def test_explicit_reason_wins_over_a_reason_key_in_details(tmp_path):
    db = tmp_path / "audit.db"
    record_terminal_state(
        db,
        WorkflowState("wf-1", "PROPOSED"),
        "REJECTED",
        reason="the real reason",
        details={"reason": "a decoy"},
    )
    (event,) = list_events(db, "wf-1")
    assert event["payload"]["reason"] == "the real reason"


def test_reason_is_stripped(tmp_path):
    db = tmp_path / "audit.db"
    record_terminal_state(db, WorkflowState("wf-1", "PROPOSED"), "REJECTED", reason="  spaced  ")
    (event,) = list_events(db, "wf-1")
    assert event["payload"]["reason"] == "spaced"


@pytest.mark.parametrize("non_terminal", ["DISCOVERED", "SCANNED", "PROPOSED", "APPROVED", "VERIFIED", "DRAFT_PR_CREATED"])
def test_a_non_terminal_target_is_refused_and_writes_nothing(tmp_path, non_terminal):
    db = tmp_path / "audit.db"
    with pytest.raises(ValueError, match="only for terminal states"):
        record_terminal_state(db, WorkflowState("wf-1", "APPROVED"), non_terminal, reason="x")
    assert list_events(db, "wf-1") == []


@pytest.mark.parametrize(
    "from_state, terminal_state",
    [
        ("SCANNED", "ROLLED_BACK"),
        ("VERIFIED", "ROLLED_BACK"),
        ("PROPOSED", "ROLLED_BACK"),
        ("APPROVED", "REJECTED"),
        ("DISCOVERED", "REJECTED"),
    ],
)
def test_an_illegal_arrow_to_a_terminal_is_refused_and_writes_nothing(tmp_path, from_state, terminal_state):
    db = tmp_path / "audit.db"
    with pytest.raises(ValueError, match="Invalid transition"):
        record_terminal_state(db, WorkflowState("wf-1", from_state), terminal_state, reason="x")
    assert list_events(db, "wf-1") == []


@pytest.mark.parametrize("already_terminal", sorted(TERMINAL_STATES))
def test_you_cannot_record_a_second_terminal_state(tmp_path, already_terminal):
    db = tmp_path / "audit.db"
    with pytest.raises(ValueError):
        record_terminal_state(db, WorkflowState("wf-1", already_terminal), "FAILED", reason="x")
    assert list_events(db, "wf-1") == []


@pytest.mark.parametrize("bad_reason", ["", "   ", None, 5, ["why"]])
def test_a_missing_or_blank_reason_is_refused_and_writes_nothing(tmp_path, bad_reason):
    db = tmp_path / "audit.db"
    with pytest.raises(ValueError, match="reason must be a non-empty string"):
        record_terminal_state(db, WorkflowState("wf-1", "PROPOSED"), "REJECTED", reason=bad_reason)
    assert list_events(db, "wf-1") == []


def test_reason_is_keyword_only(tmp_path):
    db = tmp_path / "audit.db"
    with pytest.raises(TypeError):
        record_terminal_state(db, WorkflowState("wf-1", "PROPOSED"), "REJECTED", "positional reason")


def test_record_terminal_state_returns_a_new_object_and_leaves_the_input_alone(tmp_path):
    db = tmp_path / "audit.db"
    before = WorkflowState("wf-1", "PROPOSED")
    after = record_terminal_state(db, before, "REJECTED", reason="x")
    assert after is not before
    assert before.state == "PROPOSED"


def test_the_ending_completes_a_legal_ordered_audit_walk(tmp_path):
    # A run that is discovered, scanned, proposed - then rejected. The
    # rejection must be the last recorded row, and every step a legal arrow.
    from audit_db import record_event

    db = tmp_path / "audit.db"
    state = WorkflowState("wf-1", "DISCOVERED")
    record_event(db, "wf-1", "environment_discovered", state.state, {})
    for nxt in ["SCANNED", "PROPOSED"]:
        state = transition(state, nxt)
        record_event(db, "wf-1", f"moved_to_{nxt.lower()}", state.state, {})

    state = record_terminal_state(db, state, "REJECTED", reason="reviewer withheld sign-off")

    recorded = [e["state"] for e in list_events(db, "wf-1")]
    assert recorded == ["DISCOVERED", "SCANNED", "PROPOSED", "REJECTED"]
    for here, nxt in zip(recorded, recorded[1:]):
        assert nxt in ALLOWED_TRANSITIONS[here], f"{here} -> {nxt} is not a legal arrow"
    assert list_events(db, "wf-1")[-1]["event_type"] == "workflow_rejected"
