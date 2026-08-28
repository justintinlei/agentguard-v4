"""Tests for audit_log.log_discovery_event() (Day 9, Lab 5).

append_event() and log_analysis_event() are already covered in
tests/test_v2_service.py. This file covers the new v3 discovery event:
the schema it writes, and what it deliberately leaves out.
"""

import json

import pytest

from audit_log import log_discovery_event


def _read_one(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    return json.loads(lines[0])


def test_success_event_has_the_core_fields_and_counts(tmp_path):
    log_path = tmp_path / "audit_events.jsonl"
    log_discovery_event(
        log_path,
        route="MCP client/server",
        tool_name="list_agent_inventory",
        source_name="agents.json",
        source_sha256="c" * 64,
        correlation_id="corr-1",
        outcome="success",
        agent_count=3,
        high_risk_count=2,
    )

    record = _read_one(log_path)
    assert record["event_type"] == "discovery_complete"
    assert "timestamp" in record
    payload = record["payload"]
    assert payload["route"] == "MCP client/server"
    assert payload["tool_name"] == "list_agent_inventory"
    assert payload["source_name"] == "agents.json"
    assert payload["source_sha256"] == "c" * 64
    assert payload["correlation_id"] == "corr-1"
    assert payload["outcome"] == "success"
    assert payload["agent_count"] == 3
    assert payload["high_risk_count"] == 2
    assert "error_category" not in payload


def test_error_event_has_a_category_and_no_counts(tmp_path):
    log_path = tmp_path / "audit_events.jsonl"
    log_discovery_event(
        log_path,
        route="Direct core (debug)",
        tool_name="(direct core - no tool call)",
        source_name="",
        source_sha256="",
        correlation_id="",
        outcome="error",
        error_category="MCPUnavailableError",
    )

    payload = _read_one(log_path)["payload"]
    assert payload["outcome"] == "error"
    assert payload["error_category"] == "MCPUnavailableError"
    assert "agent_count" not in payload
    assert "high_risk_count" not in payload


def test_outcome_must_be_success_or_error(tmp_path):
    with pytest.raises(ValueError, match="outcome"):
        log_discovery_event(
            tmp_path / "audit_events.jsonl",
            route="x",
            tool_name="x",
            source_name="x",
            source_sha256="x",
            correlation_id="x",
            outcome="weird",
        )


def test_append_only_two_calls_two_lines(tmp_path):
    log_path = tmp_path / "audit_events.jsonl"
    common = dict(
        route="Direct core (debug)",
        tool_name="(direct core - no tool call)",
        source_name="agents.json",
        source_sha256="a" * 64,
        correlation_id="c",
        outcome="success",
        agent_count=3,
        high_risk_count=2,
    )
    log_discovery_event(log_path, **common)
    log_discovery_event(log_path, **common)

    assert len(log_path.read_text(encoding="utf-8").splitlines()) == 2
