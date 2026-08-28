"""Tests for app_v3.py - the v3 discovery page (Day 9, Labs 1-8).

Covers, per lab: the boundary text and discovery-journey map (1); the two
discovery paths (2); provenance + risk display (3); safe error messages
(4); the discovery audit event (5); and an end-to-end page-flow check
that all of it stays internally consistent on one report (8).

The direct (in-process) path is exercised end to end - no server, no
STDIO; the MCP path is monkeypatched so pytest never spawns a real
server. Importing app_v3 is side-effect free: render() only runs under
the `__main__` guard (i.e. under `streamlit run`), never on import.
"""

import json
from pathlib import Path

import pytest

import app_v3
from discovery_core import ALLOWED_FILES
from mcp_client import (
    EXPECTED_TOOLS,
    MCPMalformedResponseError,
    MCPUnavailableError,
)
from mcp_security import MCPAccessError

APP_SOURCE = (Path(__file__).resolve().parent.parent / "app_v3.py").read_text()

# Built at runtime so this source file never contains a contiguous string
# matching scripts/check_no_secrets.py's pattern (the same rule
# tests/test_v2_service.py follows). It is a fake, key-shaped token used
# only to prove it never appears in a user-facing message.
FAKE_API_TOKEN = "sk-ant-" + "A" * 24


def test_app_v3_compiles():
    compile(APP_SOURCE, "app_v3.py", "exec")


def test_boundary_is_stated_on_the_page():
    joined = " ".join(app_v3.BOUNDARY_NOTES).lower()
    assert "synthetic" in joined
    assert "read-only" in joined
    assert "allowlist" in joined
    # v1's scanner is named as the single risk authority.
    assert "sole authority" in joined
    assert "never" in joined  # AI can never change a score


def test_journey_has_ordered_numbered_steps():
    steps = app_v3.DISCOVERY_JOURNEY
    assert len(steps) >= 5
    assert [item["step"] for item in steps] == list(range(1, len(steps) + 1))
    for item in steps:
        assert item["actor"] and item["action"] and item["trust"]


def test_journey_marks_the_untrusted_entry_and_the_authority():
    trust_markers = [item["trust"].lower() for item in app_v3.DISCOVERY_JOURNEY]
    assert any("untrusted" in marker for marker in trust_markers)
    assert any("validation boundary" in marker for marker in trust_markers)
    assert any("authority" in marker for marker in trust_markers)


def test_map_uses_the_real_allowlists():
    # The page imports the live constants, so it can never describe a
    # different file set or tool set than the system actually enforces.
    assert app_v3.ALLOWED_FILES is ALLOWED_FILES
    assert app_v3.EXPECTED_TOOLS is EXPECTED_TOOLS


def test_discover_button_is_enabled_now():
    # Lab 1 shipped this button disabled; Lab 2 wires it.
    assert 'st.button("Discover and scan"' in APP_SOURCE
    assert "disabled=True" not in APP_SOURCE


def test_two_discovery_paths_are_offered():
    assert app_v3.DISCOVERY_PATHS == ("Direct core (debug)", "MCP client/server")


def test_direct_path_returns_the_inventory_shape():
    # In-process: no server, no STDIO, no subprocess.
    inventory = app_v3.discover_inventory("Direct core (debug)")
    assert isinstance(inventory["agents"], list) and inventory["agents"]
    assert inventory["source_name"] == "agents.json"
    assert len(inventory["source_sha256"]) == 64
    assert inventory["correlation_id"]


def test_direct_path_scan_reproduces_the_known_before_state():
    # CLAUDE.md's required v1 evidence: the BEFORE inventory has exactly
    # two HIGH-risk agents. Here it is proved through the UI's own helpers.
    inventory = app_v3.discover_inventory("Direct core (debug)")
    report = app_v3.scan_mcp_inventory(inventory)
    rows = app_v3.scan_rows(report)

    levels = [row["Risk level"] for row in rows]
    assert levels.count("HIGH") == 2
    assert levels.count("NO RISK FOUND") == 1
    assert {"Agent", "Risk level", "Score", "Findings"} == set(rows[0])


def test_mcp_path_calls_only_the_inventory_tool(monkeypatch):
    calls = []

    def fake_call_tool_sync(tool_name, arguments=None):
        calls.append((tool_name, arguments))
        return {"agents": [], "source_name": "agents.json",
                "source_sha256": "0" * 64, "correlation_id": "test"}

    monkeypatch.setattr(app_v3, "call_tool_sync", fake_call_tool_sync)
    app_v3.discover_inventory("MCP client/server")

    assert calls == [("list_agent_inventory", None)]
    assert "list_agent_inventory" in EXPECTED_TOOLS


def test_unknown_path_is_rejected():
    with pytest.raises(ValueError, match="Unknown discovery path"):
        app_v3.discover_inventory("bogus")


# --- Lab 3: provenance and risk-result display -------------------------------

def _direct_report():
    inventory = app_v3.discover_inventory("Direct core (debug)")
    return inventory, app_v3.scan_mcp_inventory(inventory)


def test_provenance_rows_expose_hash_and_correlation_id():
    _inventory, report = _direct_report()
    rows = app_v3.provenance_rows(report)
    by_field = {row["Field"]: row["Value"] for row in rows}

    assert by_field["Source file"] == "agents.json"
    sha = by_field["SHA-256 of source bytes"]
    assert len(sha) == 64 and all(c in "0123456789abcdef" for c in sha)
    assert by_field["Correlation ID"]  # non-empty


def test_report_provenance_matches_the_raw_inventory():
    inventory, report = _direct_report()
    assert app_v3.provenance_matches_inventory(report, inventory) is True

    tampered = dict(inventory)
    tampered["source_sha256"] = "0" * 64
    assert app_v3.provenance_matches_inventory(report, tampered) is False


def test_finding_rows_list_every_finding_with_its_agent():
    _inventory, report = _direct_report()
    rows = app_v3.finding_rows(report)

    expected_count = sum(len(result.findings) for result in report["results"])
    assert len(rows) == expected_count > 0
    for row in rows:
        assert row["Agent"] and row["Rule"] and row["Severity"]
    assert any(row["Agent"] == "Customer Support Agent" for row in rows)


def test_page_carries_the_not_fully_secure_note():
    assert "NO RISK FOUND" in app_v3.NOT_FULLY_SECURE_NOTE


# --- Lab 4: safe error handling --------------------------------------------

def test_safe_error_message_per_category():
    messages = {
        "unavailable": app_v3.safe_error_message(MCPUnavailableError("x")),
        "malformed": app_v3.safe_error_message(MCPMalformedResponseError("x")),
        "value": app_v3.safe_error_message(ValueError("x")),
        "runtime": app_v3.safe_error_message(RuntimeError("x")),
        "unknown": app_v3.safe_error_message(KeyError("x")),
    }
    for text in messages.values():
        assert isinstance(text, str) and text.strip()
    # The four categorised messages are all different from each other.
    assert len(set(messages.values())) == 5


def test_safe_error_message_never_leaks_the_raw_exception_text():
    secrets = [
        FAKE_API_TOKEN,
        "/Users/alice/.ssh/id_rsa",
        "Authorization: Bearer xyz",
    ]
    planted = " ".join(secrets)
    for exc in (
        MCPUnavailableError(planted),
        MCPMalformedResponseError(planted),
        ValueError(planted),
        RuntimeError(planted),
        OSError(planted),
    ):
        message = app_v3.safe_error_message(exc)
        for secret in secrets:
            assert secret not in message


def test_named_mcp_errors_beat_the_generic_runtime_branch():
    # Both named errors subclass RuntimeError - order in the ladder matters.
    assert app_v3.safe_error_message(MCPUnavailableError("x")) != \
        app_v3.safe_error_message(RuntimeError("x"))
    assert "could not reach" in \
        app_v3.safe_error_message(MCPUnavailableError("x")).lower()


def test_render_uses_the_safe_message_not_the_raw_exception():
    assert "safe_error_message(" in APP_SOURCE
    assert "st.exception(" not in APP_SOURCE
    assert 'f"Discovery failed: {exc}"' not in APP_SOURCE


# --- Lab 5: read-only discovery audit events -------------------------------

def _one_audit_line(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    return json.loads(lines[0])


def test_record_discovery_event_writes_a_success_line(tmp_path, monkeypatch):
    monkeypatch.setattr(app_v3, "AUDIT_LOG_PATH", tmp_path / "audit_events.jsonl")
    inventory = app_v3.discover_inventory("Direct core (debug)")
    report = app_v3.scan_mcp_inventory(inventory)

    app_v3.record_discovery_event(
        "Direct core (debug)", "(direct core - no tool call)", inventory, report=report
    )

    payload = _one_audit_line(tmp_path / "audit_events.jsonl")["payload"]
    assert payload["outcome"] == "success"
    assert payload["route"] == "Direct core (debug)"
    assert payload["tool_name"] == "(direct core - no tool call)"
    assert len(payload["source_sha256"]) == 64
    assert payload["correlation_id"]
    assert payload["agent_count"] == 3
    assert payload["high_risk_count"] == 2


def test_record_discovery_event_error_line_has_category_not_message(tmp_path, monkeypatch):
    monkeypatch.setattr(app_v3, "AUDIT_LOG_PATH", tmp_path / "audit_events.jsonl")
    exc = ValueError(f"boom /Users/alice/.ssh/id_rsa {FAKE_API_TOKEN}")

    app_v3.record_discovery_event(
        "MCP client/server", "list_agent_inventory", None, exc=exc
    )

    record = _one_audit_line(tmp_path / "audit_events.jsonl")
    assert record["payload"]["outcome"] == "error"
    assert record["payload"]["error_category"] == "ValueError"
    dumped = json.dumps(record)
    assert "id_rsa" not in dumped
    assert FAKE_API_TOKEN not in dumped


def test_record_discovery_event_is_best_effort(tmp_path, monkeypatch):
    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(app_v3, "log_discovery_event", boom)
    # A broken audit log must not raise out of the discovery handler.
    app_v3.record_discovery_event(
        "Direct core (debug)",
        "(direct core - no tool call)",
        {"source_name": "agents.json", "source_sha256": "x", "correlation_id": "c"},
        report=None,
    )


def test_handler_audits_both_success_and_failure_paths():
    # Both call sites are present in the button handler.
    assert APP_SOURCE.count("record_discovery_event(") >= 3  # 1 def + 2 calls
    assert "record_discovery_event(path_label, tool_name, inventory, report=report)" in APP_SOURCE
    assert "record_discovery_event(path_label, tool_name, inventory, exc=exc)" in APP_SOURCE


# --- Lab 8 release candidate: the whole page flow holds together ----------

def test_page_flow_is_internally_consistent(tmp_path, monkeypatch):
    """The RC smoke test: run exactly what the 'Discover and scan' handler
    does on its success path and prove every piece agrees with every
    other - one discovery, one correlation id, one set of counts."""
    monkeypatch.setattr(app_v3, "AUDIT_LOG_PATH", tmp_path / "audit_events.jsonl")

    inventory = app_v3.discover_inventory("Direct core (debug)")
    report = app_v3.scan_mcp_inventory(inventory)
    app_v3.record_discovery_event(
        "Direct core (debug)", "(direct core - no tool call)", inventory, report=report
    )

    # Provenance ties the raw inventory and the risk report together.
    assert app_v3.provenance_matches_inventory(report, inventory)

    audit_line = json.loads((tmp_path / "audit_events.jsonl").read_text().splitlines()[0])
    correlation_ids = {
        inventory["correlation_id"],
        report["provenance"]["correlation_id"],
        audit_line["payload"]["correlation_id"],
    }
    assert len(correlation_ids) == 1  # the same id everywhere

    rows = app_v3.scan_rows(report)
    assert len(rows) == 3
    assert [r["Risk level"] for r in rows].count("HIGH") == 2
    assert len(app_v3.finding_rows(report)) == 6

    assert audit_line["payload"]["outcome"] == "success"
    assert audit_line["payload"]["agent_count"] == 3
    assert audit_line["payload"]["high_risk_count"] == 2


def test_safe_error_message_categorises_mcp_access_error():
    # MCPAccessError subclasses ValueError, so it lands in the value-error
    # branch - the right category for a path-safety rejection ("could not
    # be read"). str(exc) never appears in the message.
    message = app_v3.safe_error_message(MCPAccessError("File is not allowlisted: 'x'"))
    assert message == app_v3.safe_error_message(ValueError("x"))
    assert "allowlisted" not in message
    assert "'x'" not in message
