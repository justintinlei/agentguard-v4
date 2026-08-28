"""Append privacy-safe audit events to a local JSON Lines (.jsonl) file.

Each event is one JSON object per line - appendable without reading or
rewriting the rest of the file, easy to grep, easy to replay line by line.
Nothing already written is ever edited or overwritten (append-only), so
the file is a durable record even if a later run crashes mid-write.
As of v3 this file also serves discovery: log_discovery_event() records
one line per "Discover and scan" click (route, tool, source hash,
correlation id, outcome) alongside v2's analysis_complete events.

The payload passed in must only ever be structured, non-sensitive metadata
(e.g. agent name, risk level, mode, token counts) - never an API key,
token, or password. This module has no way to read `.env` or fetch a
secret itself, so the only way one could ever reach the log is a caller
passing one directly - which append_event actively refuses to do, using
the same two secret patterns scripts/check_no_secrets.py already scans
for elsewhere in this project (that scanner's own extension allowlist
does not include .jsonl files, so this check is this file's only line of
defense against that specific gap).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from analysis_schema import GroundedAnalysis
from claude_analyst import UsageRecord

_SECRET_PATTERN = re.compile(r"sk-ant-[A-Za-z0-9_-]{16,}|github_pat_[A-Za-z0-9_]{16,}")


def append_event(path: Path, event_type: str, payload: dict) -> None:
    """Append one event as a single JSON line: timestamp, event_type, payload.

    Raises ValueError, and writes nothing, if the payload's values match a
    known secret pattern - a caller mistake should fail loudly, not get
    logged.
    """
    serialized_payload = json.dumps(payload, sort_keys=True)
    if _SECRET_PATTERN.search(serialized_payload):
        raise ValueError("Refusing to log an event whose payload looks like it contains a secret.")

    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "payload": payload,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def log_analysis_event(path: Path, analysis: GroundedAnalysis, usage: UsageRecord) -> None:
    """Record one analyze_agent() run as an audit event: which agent, its
    deterministic risk (already grounding-validated to match the real
    scan), and observability metrics - mode, model, token counts, latency,
    estimated cost - via usage.to_dict(). Makes a run measurable after the
    fact instead of only visible in the moment it happened.
    """
    payload = {
        "agent_name": analysis.agent_name,
        "risk_level": analysis.deterministic_risk_level,
        "risk_score": analysis.deterministic_risk_score,
        **usage.to_dict(),
    }
    append_event(path, "analysis_complete", payload)


def log_discovery_event(
    path: Path,
    *,
    route: str,
    tool_name: str,
    source_name: str,
    source_sha256: str,
    correlation_id: str,
    outcome: str,
    agent_count: int | None = None,
    high_risk_count: int | None = None,
    error_category: str | None = None,
) -> None:
    """Record one v3 discovery attempt as an audit event.

    This is a trail that a read *happened* - which route (direct core or
    the MCP client/server), which MCP tool was called, which source file
    and its SHA-256 hash, the correlation id that ties the request
    together, and how it ended. It is deliberately NOT a copy of what was
    discovered: no agent names, no findings text, and on failure only the
    exception's class name (error_category), never its message - the same
    rule app_v3's on-screen error handler follows.

    outcome must be "success" or "error". On success, agent_count and
    high_risk_count summarise the deterministic scan. append_event() adds
    the timestamp, keeps the file append-only, and still refuses any
    payload that looks like it contains a secret.
    """
    if outcome not in ("success", "error"):
        raise ValueError("outcome must be 'success' or 'error'")

    payload = {
        "route": route,
        "tool_name": tool_name,
        "source_name": source_name,
        "source_sha256": source_sha256,
        "correlation_id": correlation_id,
        "outcome": outcome,
    }
    if agent_count is not None:
        payload["agent_count"] = agent_count
    if high_risk_count is not None:
        payload["high_risk_count"] = high_risk_count
    if error_category is not None:
        payload["error_category"] = error_category

    append_event(path, "discovery_complete", payload)
