"""Local SQLite audit log for the v4 remediation workflow.

Every workflow step is recorded as one row in the `workflow_events`
table. The table is **append-only by convention** - this module never
updates or deletes a row - so the recorded history is immutable evidence.

SQLite is a single local file: no server, no configuration, no network.
Rows carry an autoincrementing integer `id`, so `ORDER BY id` always
returns events in the exact order they were written, even when two
events share a `created_at` timestamp.

Day 5 Lab 4 designed the table and `initialize()`; Lab 5 added
`record_event()` (writes); Lab 6 added `list_events()` (ordered reads) -
how a reviewer replays one workflow's history.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# The one table. `id` is the ordering key - an ever-increasing integer
# the database assigns per row. The five recording columns are NOT NULL:
# an event with no workflow, type, state, time, or payload is not a
# usable audit record.
SCHEMA = """
CREATE TABLE IF NOT EXISTS workflow_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
"""


def initialize(path: str | Path) -> None:
    """Create the audit database and the `workflow_events` table if absent.

    Safe to call repeatedly - `CREATE TABLE IF NOT EXISTS` makes it a
    no-op once the table exists. Creates the parent directory if needed.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute(SCHEMA)


def record_event(
    path: str | Path,
    workflow_id: str,
    event_type: str,
    state: str,
    payload: dict,
) -> None:
    """Append one event row to the audit log.

    Calls `initialize()` first, so it works on a path with no database
    yet. The `INSERT` uses `?` placeholders - the values are passed to
    SQLite as data, never as SQL - and `created_at` is stamped here from
    the machine's UTC clock, so a caller cannot supply a fake time.
    `payload` is stored as sorted-key JSON so the same payload always
    stores as the same text.
    """
    initialize(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO workflow_events"
            "(workflow_id, event_type, state, created_at, payload_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                workflow_id,
                event_type,
                state,
                datetime.now(timezone.utc).isoformat(),
                json.dumps(payload, sort_keys=True),
            ),
        )


def list_events(path: str | Path, workflow_id: str) -> list[dict]:
    """Return every event recorded for `workflow_id`, in the order it happened.

    `ORDER BY id` uses the autoincrement key, so the list is in insertion
    order even if two events share a `created_at`. Each row's stored JSON
    is deserialised back into a dict under `"payload"`. A workflow with no
    events - or a database file that does not exist yet - returns `[]`,
    not an error.
    """
    initialize(path)
    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            "SELECT event_type, state, created_at, payload_json "
            "FROM workflow_events WHERE workflow_id = ? ORDER BY id",
            (workflow_id,),
        ).fetchall()
    return [
        {
            "event_type": row[0],
            "state": row[1],
            "created_at": row[2],
            "payload": json.loads(row[3]),
        }
        for row in rows
    ]
