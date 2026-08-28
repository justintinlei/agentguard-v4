"""Tests for mcp_client.py's tool allowlist check and error handling.

_verify_tool_allowlist() and _structured() are pure logic (no async, no
subprocess, no server) precisely so their refusal/rejection behavior
can be tested directly, without spinning up a real or fake MCP server.
The two call_tool() tests below do spin up a real subprocess (a
missing script, then a genuinely hung one) because that's the only way
to prove the actual connection-failure path - the one behavior this
file can't reduce to pure logic - really produces a clean
MCPUnavailableError instead of a raw ExceptionGroup.
"""

import pytest

import mcp_client
from mcp_client import (
    EXPECTED_TOOLS,
    MCPMalformedResponseError,
    MCPUnavailableError,
    _structured,
    _verify_tool_allowlist,
)


def test_verify_tool_allowlist_accepts_the_real_five_tools():
    _verify_tool_allowlist(set(EXPECTED_TOOLS))


def test_verify_tool_allowlist_rejects_a_missing_tool():
    with pytest.raises(RuntimeError):
        _verify_tool_allowlist(EXPECTED_TOOLS - {"health_check"})


def test_verify_tool_allowlist_rejects_an_unexpected_extra_tool():
    with pytest.raises(RuntimeError):
        _verify_tool_allowlist(EXPECTED_TOOLS | {"delete_everything"})


class _FakeBlock:
    def __init__(self, text):
        self.text = text


class _FakeResult:
    def __init__(self, content):
        self.content = content


def test_structured_rejects_malformed_json_as_a_clear_error():
    with pytest.raises(MCPMalformedResponseError):
        _structured(_FakeResult([_FakeBlock("this is not json {")]))


def test_structured_rejects_empty_content_as_a_clear_error():
    with pytest.raises(MCPMalformedResponseError):
        _structured(_FakeResult([]))


def test_call_tool_raises_a_controlled_error_when_the_server_is_unavailable(tmp_path, monkeypatch):
    """No mcp_server.py exists at BASE_DIR, so the launched process exits
    immediately - the exact "wrong script path" scenario verified by
    hand while planning this lab, which otherwise surfaces as a nested
    ExceptionGroup instead of a clear, catchable error."""
    monkeypatch.setattr(mcp_client, "BASE_DIR", tmp_path)
    with pytest.raises(MCPUnavailableError):
        mcp_client.call_tool_sync("health_check")


def test_call_tool_raises_a_controlled_error_when_the_server_hangs(tmp_path, monkeypatch):
    """A server that starts but never speaks MCP is just as unavailable
    as one that never starts. Verified by hand while planning this lab
    that this resolves in a few seconds under a short timeout, not a
    real 60-second wait."""
    slow_script = tmp_path / "mcp_server.py"
    slow_script.write_text("import time\ntime.sleep(60)\n")
    monkeypatch.setattr(mcp_client, "BASE_DIR", tmp_path)
    monkeypatch.setattr(mcp_client, "CONNECT_TIMEOUT_SECONDS", 1.0)
    with pytest.raises(MCPUnavailableError):
        mcp_client.call_tool_sync("health_check")


def test_call_tool_sync_succeeds_against_the_real_server():
    """Day 6, Lab 8 gap: every prior test proves a failure path through
    the real call_tool() machinery, or a success path through
    scripts/run_mcp_live_smoke.py - which pytest -q never runs. This is
    the one test proving the plain happy path (real, unmodified
    mcp_server.py, real subprocess, no monkeypatching) inside the
    enforced pytest gate."""
    health = mcp_client.call_tool_sync("health_check")
    assert health["status"] == "ok"
    assert health["mode"] == "read-only"
    assert health["tool_count"] == 5
