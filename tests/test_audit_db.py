"""Tests for audit_db.py - Day 5 Lab 4 (the workflow_events table design).

The property under test: `initialize()` creates one well-formed,
append-only table whose `id` column preserves insertion order. Writes
(`record_event`) are Lab 5; ordered reads (`list_events`) are Lab 6.
"""

import json
import sqlite3
from datetime import datetime

import pytest

from audit_db import SCHEMA, initialize, list_events, record_event
from workflow import ALLOWED_TRANSITIONS, WorkflowState, transition

# name -> declared type, from PRAGMA table_info
EXPECTED_COLUMNS = {
    "id": "INTEGER",
    "workflow_id": "TEXT",
    "event_type": "TEXT",
    "state": "TEXT",
    "created_at": "TEXT",
    "payload_json": "TEXT",
}

RECORDING_COLUMNS = ["workflow_id", "event_type", "state", "created_at", "payload_json"]


def _table_info(db):
    """Rows of (cid, name, type, notnull, dflt_value, pk) for workflow_events."""
    with sqlite3.connect(db) as connection:
        return connection.execute("PRAGMA table_info(workflow_events)").fetchall()


# --- initialize() ----------------------------------------------------------

def test_initialize_creates_the_database_file(tmp_path):
    db = tmp_path / "audit.db"
    assert not db.exists()
    initialize(db)
    assert db.exists()


def test_initialize_creates_missing_parent_directories(tmp_path):
    db = tmp_path / "nested" / "dir" / "audit.db"
    initialize(db)
    assert db.exists()


def test_initialize_accepts_a_string_path(tmp_path):
    db = tmp_path / "audit.db"
    initialize(str(db))
    assert db.exists()


def test_initialize_is_idempotent(tmp_path):
    db = tmp_path / "audit.db"
    initialize(db)
    initialize(db)  # must not raise
    with sqlite3.connect(db) as connection:
        # exclude SQLite's own internal tables (e.g. sqlite_sequence,
        # which AUTOINCREMENT creates to remember the last id)
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    assert [t[0] for t in tables] == ["workflow_events"]


# --- the table design ----------------------------------------------------------

def test_the_table_has_exactly_the_expected_columns_and_types(tmp_path):
    db = tmp_path / "audit.db"
    initialize(db)
    columns = {row[1]: row[2] for row in _table_info(db)}
    assert columns == EXPECTED_COLUMNS


def test_id_is_the_integer_primary_key(tmp_path):
    db = tmp_path / "audit.db"
    initialize(db)
    id_row = next(row for row in _table_info(db) if row[1] == "id")
    assert id_row[2] == "INTEGER"
    assert id_row[5] == 1  # pk flag


def test_every_recording_column_is_not_null(tmp_path):
    db = tmp_path / "audit.db"
    initialize(db)
    notnull = {row[1]: row[3] for row in _table_info(db)}
    for column in RECORDING_COLUMNS:
        assert notnull[column] == 1, f"{column} should be NOT NULL"


def test_schema_uses_create_if_not_exists(tmp_path):
    assert "CREATE TABLE IF NOT EXISTS workflow_events" in SCHEMA


# --- the point of the lab: id preserves insertion order ----------------------

def test_order_by_id_is_insertion_order_even_with_a_shared_timestamp(tmp_path):
    db = tmp_path / "audit.db"
    initialize(db)
    same_time = "2026-08-29T00:00:00+00:00"
    with sqlite3.connect(db) as connection:
        for event_type in ["one", "two", "three"]:
            connection.execute(
                "INSERT INTO workflow_events"
                "(workflow_id, event_type, state, created_at, payload_json) "
                "VALUES (?, ?, ?, ?, ?)",
                ("wf-1", event_type, "DISCOVERED", same_time, "{}"),
            )
        rows = connection.execute(
            "SELECT id, event_type FROM workflow_events ORDER BY id"
        ).fetchall()
    assert [r[1] for r in rows] == ["one", "two", "three"]
    assert [r[0] for r in rows] == sorted(r[0] for r in rows)  # ids strictly ascending


# --- Day 5 Lab 5: event writes ----------------------------------------------
#
# record_event() appends one row. Reads here use raw SELECT (list_events
# is Lab 6). The point of the lab: after a workflow runs, every step it
# took is a permanent, ordered row.

HAPPY_PATH = [
    "SCANNED", "PROPOSED", "APPROVED", "VERIFIED", "DRAFT_PR_CREATED", "ROLLED_BACK",
]


def _rows(db, workflow_id=None):
    sql = "SELECT workflow_id, event_type, state, created_at, payload_json FROM workflow_events"
    params = ()
    if workflow_id is not None:
        sql += " WHERE workflow_id = ?"
        params = (workflow_id,)
    sql += " ORDER BY id"
    with sqlite3.connect(db) as connection:
        return connection.execute(sql, params).fetchall()


def test_record_event_creates_the_database_on_a_fresh_path(tmp_path):
    db = tmp_path / "audit.db"
    assert not db.exists()
    record_event(db, "wf-1", "environment_discovered", "DISCOVERED", {"source_sha256": "abc"})
    assert db.exists()
    assert len(_rows(db)) == 1


def test_the_stored_row_has_the_exact_values_passed(tmp_path):
    db = tmp_path / "audit.db"
    record_event(db, "wf-7", "proposal_approved", "APPROVED", {"reviewer": "Dana"})
    (row,) = _rows(db)
    assert row[0] == "wf-7"
    assert row[1] == "proposal_approved"
    assert row[2] == "APPROVED"


def test_created_at_is_a_utc_iso_timestamp(tmp_path):
    db = tmp_path / "audit.db"
    record_event(db, "wf-1", "scanned", "SCANNED", {})
    (row,) = _rows(db)
    when = datetime.fromisoformat(row[3])
    assert when.tzinfo is not None
    assert when.utcoffset().total_seconds() == 0


def test_payload_round_trips_including_nested_structures(tmp_path):
    db = tmp_path / "audit.db"
    payload = {"proposal": {"tools": ["a", "b"], "human_approval_required": True}, "n": 3}
    record_event(db, "wf-1", "proposal_created", "PROPOSED", payload)
    (row,) = _rows(db)
    assert json.loads(row[4]) == payload


def test_the_same_payload_stores_as_the_same_text_regardless_of_key_order(tmp_path):
    db = tmp_path / "audit.db"
    record_event(db, "wf-1", "e", "SCANNED", {"b": 2, "a": 1})
    record_event(db, "wf-2", "e", "SCANNED", {"a": 1, "b": 2})
    stored = {r[0]: r[4] for r in _rows(db)}
    assert stored["wf-1"] == stored["wf-2"]


def test_events_are_append_only_in_practice(tmp_path):
    db = tmp_path / "audit.db"
    for i in range(5):
        record_event(db, "wf-1", f"step-{i}", "SCANNED", {"i": i})
    rows = _rows(db)
    assert [r[1] for r in rows] == [f"step-{i}" for i in range(5)]  # nothing overwritten
    with sqlite3.connect(db) as connection:
        ids = [r[0] for r in connection.execute("SELECT id FROM workflow_events ORDER BY id")]
    assert ids == sorted(set(ids)) and len(ids) == 5


def test_two_workflows_coexist_and_filter_cleanly(tmp_path):
    db = tmp_path / "audit.db"
    record_event(db, "wf-a", "one", "SCANNED", {})
    record_event(db, "wf-b", "one", "SCANNED", {})
    record_event(db, "wf-a", "two", "PROPOSED", {})
    assert [r[1] for r in _rows(db, "wf-a")] == ["one", "two"]
    assert [r[1] for r in _rows(db, "wf-b")] == ["one"]


def test_every_transition_becomes_a_recorded_event(tmp_path):
    db = tmp_path / "audit.db"
    state = WorkflowState("wf-1", "DISCOVERED")
    record_event(db, state.workflow_id, "environment_discovered", state.state, {})
    for nxt in HAPPY_PATH:
        state = transition(state, nxt)
        record_event(db, state.workflow_id, f"moved_to_{nxt.lower()}", state.state, {})

    recorded_states = [r[2] for r in _rows(db, "wf-1")]
    assert recorded_states == ["DISCOVERED"] + HAPPY_PATH


# --- Day 5 Lab 6: ordered event retrieval -----------------------------------
#
# list_events(path, workflow_id) is the read path: one workflow's whole
# history, in order, with each payload deserialised. This is how a
# reviewer reconstructs what happened without touching SQL.

FOUR_KEYS = {"event_type", "state", "created_at", "payload"}


def test_list_events_on_a_missing_database_returns_empty(tmp_path):
    assert list_events(tmp_path / "nope.db", "wf-1") == []


def test_list_events_for_an_unknown_workflow_returns_empty(tmp_path):
    db = tmp_path / "audit.db"
    record_event(db, "wf-1", "one", "SCANNED", {})
    assert list_events(db, "wf-other") == []


def test_list_events_returns_events_in_insertion_order(tmp_path):
    db = tmp_path / "audit.db"
    for event_type in ["first", "second", "third"]:
        record_event(db, "wf-1", event_type, "SCANNED", {})
    assert [e["event_type"] for e in list_events(db, "wf-1")] == ["first", "second", "third"]


def test_each_event_has_the_four_keys_and_a_deserialised_payload(tmp_path):
    db = tmp_path / "audit.db"
    payload = {"proposal": {"tools": ["a", "b"]}, "reviewer": "Dana"}
    record_event(db, "wf-1", "proposal_approved", "APPROVED", payload)
    (event,) = list_events(db, "wf-1")
    assert set(event) == FOUR_KEYS
    assert isinstance(event["payload"], dict)
    assert event["payload"] == payload


def test_list_events_filters_to_the_requested_workflow(tmp_path):
    db = tmp_path / "audit.db"
    record_event(db, "wf-a", "a1", "SCANNED", {})
    record_event(db, "wf-b", "b1", "SCANNED", {})
    record_event(db, "wf-a", "a2", "PROPOSED", {})
    assert [e["event_type"] for e in list_events(db, "wf-a")] == ["a1", "a2"]
    assert [e["event_type"] for e in list_events(db, "wf-b")] == ["b1"]


def test_a_reviewer_can_reconstruct_the_whole_workflow(tmp_path):
    db = tmp_path / "audit.db"
    state = WorkflowState("wf-1", "DISCOVERED")
    record_event(db, state.workflow_id, "environment_discovered", state.state, {})
    for nxt in HAPPY_PATH:
        state = transition(state, nxt)
        record_event(db, state.workflow_id, f"moved_to_{nxt.lower()}", state.state, {})

    events = list_events(db, "wf-1")
    assert [e["state"] for e in events] == ["DISCOVERED"] + HAPPY_PATH
    assert [e["event_type"] for e in events] == (
        ["environment_discovered"] + [f"moved_to_{s.lower()}" for s in HAPPY_PATH]
    )


def test_order_is_stable_across_a_fresh_call(tmp_path):
    db = tmp_path / "audit.db"
    for i in range(4):
        record_event(db, "wf-1", f"step-{i}", "SCANNED", {"i": i})
    first = [e["event_type"] for e in list_events(db, "wf-1")]
    second = [e["event_type"] for e in list_events(db, "wf-1")]
    assert first == second == [f"step-{i}" for i in range(4)]


# --- Day 5 Lab 7: the audit log is a legal, ordered walk --------------------
#
# Two guarantees, together: the recorded state sequence for any workflow
# is a legal walk of the state machine, and list_events returns it in the
# true order it happened.


def _record_run(db, workflow_id, path):
    """Drive `path` (a list of states after DISCOVERED) through transition()
    and record each step. Returns the recorded state list."""
    state = WorkflowState(workflow_id, "DISCOVERED")
    record_event(db, workflow_id, "discovered", state.state, {})
    for nxt in path:
        state = transition(state, nxt)
        record_event(db, workflow_id, f"to_{nxt.lower()}", state.state, {})
    return [e["state"] for e in list_events(db, workflow_id)]


@pytest.mark.parametrize(
    "path",
    [
        ["SCANNED", "PROPOSED", "APPROVED", "VERIFIED", "DRAFT_PR_CREATED", "ROLLED_BACK"],
        ["SCANNED", "PROPOSED", "REJECTED"],
        ["SCANNED", "PROPOSED", "APPROVED", "FAILED"],
        ["SCANNED", "FAILED"],
    ],
)
def test_the_recorded_state_sequence_is_always_a_legal_walk(tmp_path, path):
    states = _record_run(tmp_path / "audit.db", "wf-1", path)
    assert states == ["DISCOVERED"] + path
    for here, nxt in zip(states, states[1:]):
        assert nxt in ALLOWED_TRANSITIONS[here], f"{here} -> {nxt} is not a legal arrow"


def test_the_log_can_be_re_validated_against_the_state_machine(tmp_path):
    happy = ["SCANNED", "PROPOSED", "APPROVED", "VERIFIED", "DRAFT_PR_CREATED", "ROLLED_BACK"]
    states = _record_run(tmp_path / "audit.db", "wf-1", happy)
    # Feed the recorded pairs back through the guard - each must be accepted.
    for here, nxt in zip(states, states[1:]):
        result = transition(WorkflowState("wf-1", here), nxt)
        assert result.state == nxt


def test_event_order_survives_interleaved_writes_from_two_workflows(tmp_path):
    db = tmp_path / "audit.db"
    record_event(db, "wf-a", "a1", "SCANNED", {})
    record_event(db, "wf-b", "b1", "SCANNED", {})
    record_event(db, "wf-a", "a2", "PROPOSED", {})
    record_event(db, "wf-b", "b2", "PROPOSED", {})
    record_event(db, "wf-a", "a3", "APPROVED", {})
    assert [e["event_type"] for e in list_events(db, "wf-a")] == ["a1", "a2", "a3"]
    assert [e["event_type"] for e in list_events(db, "wf-b")] == ["b1", "b2"]


def test_a_ten_event_run_keeps_call_order(tmp_path):
    db = tmp_path / "audit.db"
    expected = [f"event-{i:02d}" for i in range(10)]
    for name in expected:
        record_event(db, "wf-1", name, "SCANNED", {})
    assert [e["event_type"] for e in list_events(db, "wf-1")] == expected


# --- Day 5 Lab 8: inspecting the log with plain Python ----------------------
#
# The audit database is one SQLite file. Everything needed to read it
# ships with Python: `audit_db.list_events()` for one workflow's history,
# and the stdlib `sqlite3` module for any other question. No SQLite CLI,
# no database GUI, no third-party package.


def _sample_log(tmp_path):
    """A small synthetic multi-workflow log to inspect."""
    db = tmp_path / "audit.db"
    record_event(db, "wf-a", "discovered", "DISCOVERED", {"source_sha256": "aaa"})
    record_event(db, "wf-a", "scanned", "SCANNED", {"high_risk": 2})
    record_event(db, "wf-a", "proposed", "PROPOSED", {"template": "REQUIRE_HUMAN_APPROVAL"})
    record_event(db, "wf-a", "approved", "APPROVED", {"reviewer": "Dana"})
    record_event(db, "wf-b", "discovered", "DISCOVERED", {"source_sha256": "bbb"})
    record_event(db, "wf-b", "scanned", "SCANNED", {"high_risk": 0})
    record_event(db, "wf-b", "rejected", "REJECTED", {"reviewer": "Lee"})
    return db


def test_list_events_reads_one_workflow_without_any_sql(tmp_path):
    db = _sample_log(tmp_path)
    history = list_events(db, "wf-a")
    assert [e["state"] for e in history] == ["DISCOVERED", "SCANNED", "PROPOSED", "APPROVED"]


def test_you_can_list_every_workflow_id_with_stdlib_sqlite3(tmp_path):
    db = _sample_log(tmp_path)
    with sqlite3.connect(db) as connection:
        ids = [
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT workflow_id FROM workflow_events ORDER BY workflow_id"
            )
        ]
    assert ids == ["wf-a", "wf-b"]


def test_you_can_count_events_per_workflow(tmp_path):
    db = _sample_log(tmp_path)
    with sqlite3.connect(db) as connection:
        counts = dict(
            connection.execute(
                "SELECT workflow_id, COUNT(*) FROM workflow_events GROUP BY workflow_id"
            )
        )
    assert counts == {"wf-a": 4, "wf-b": 3}


def test_you_can_filter_events_by_state(tmp_path):
    db = _sample_log(tmp_path)
    with sqlite3.connect(db) as connection:
        discovered = [
            row[0]
            for row in connection.execute(
                "SELECT workflow_id FROM workflow_events WHERE state = ? ORDER BY id",
                ("DISCOVERED",),
            )
        ]
    assert discovered == ["wf-a", "wf-b"]


def test_the_raw_payload_column_is_plain_json_text(tmp_path):
    db = _sample_log(tmp_path)
    with sqlite3.connect(db) as connection:
        (raw,) = connection.execute(
            "SELECT payload_json FROM workflow_events "
            "WHERE workflow_id = 'wf-a' AND event_type = 'approved'"
        ).fetchone()
    assert isinstance(raw, str)
    assert json.loads(raw) == {"reviewer": "Dana"}


def test_row_factory_gives_named_column_access(tmp_path):
    db = _sample_log(tmp_path)
    with sqlite3.connect(db) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM workflow_events WHERE workflow_id = 'wf-b' ORDER BY id LIMIT 1"
        ).fetchone()
    assert row["state"] == "DISCOVERED"
    assert row["event_type"] == "discovered"


def test_a_workflow_history_renders_as_readable_lines(tmp_path):
    db = _sample_log(tmp_path)
    lines = [f"{e['state']:16} {e['event_type']}" for e in list_events(db, "wf-a")]
    text = "\n".join(lines)

    assert lines[0].split() == ["DISCOVERED", "discovered"]
    assert lines[-1].split() == ["APPROVED", "approved"]
    # states appear top-to-bottom in workflow order
    assert text.index("DISCOVERED") < text.index("SCANNED") < text.index("APPROVED")
