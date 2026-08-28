"""Tests for discovery_core.py's pure discovery functions.

Only imports discovery_core itself - no MCP package, no server process,
no STDIO. That's the whole point of this lab: business logic testable
without a running protocol server.
"""

import json
from pathlib import Path
from uuid import UUID

import pytest

from discovery_core import (
    ALLOWED_FILES,
    BASE_DIR,
    get_agent,
    get_ownership,
    health,
    list_agents,
    list_tools,
    new_correlation_id,
)


def test_health_reports_ok_and_read_only():
    result = health()
    assert result["status"] == "ok"
    assert result["mode"] == "read-only"


def test_health_reports_five_tools():
    assert health()["tool_count"] == 5


def test_health_includes_a_correlation_id():
    UUID(health()["correlation_id"])


def test_allowed_files_is_exactly_the_three_registry_sources():
    assert ALLOWED_FILES == {"agents.json", "tool_catalog.json", "ownership.json"}


def test_base_dir_points_at_the_connected_environment_folder():
    assert BASE_DIR.name == "connected_environment"
    assert BASE_DIR.exists()


def test_new_correlation_id_returns_a_string():
    assert isinstance(new_correlation_id(), str)


def test_new_correlation_id_is_unique_each_call():
    assert new_correlation_id() != new_correlation_id()


def test_new_correlation_id_is_a_valid_uuid4():
    """Proves the actual property that makes this useful for tracing -
    not just 'it returns something', but a properly formatted,
    practically-guaranteed-unique identifier."""
    parsed = UUID(new_correlation_id())
    assert parsed.version == 4


def test_list_agents_returns_all_three_synthetic_agents():
    result = list_agents()
    assert result["count"] == 3
    assert result["environment_name"] == "AgentGuard Connected Demo Environment"
    assert {agent["agent_name"] for agent in result["agents"]} == {
        "Customer Support Agent",
        "Research Agent",
        "Deployment Agent",
    }
    assert result["source_name"] == "agents.json"
    assert len(result["source_sha256"]) == 64
    UUID(result["correlation_id"])


def test_get_agent_returns_the_matching_record():
    result = get_agent("Research Agent")
    assert result["agent"]["agent_name"] == "Research Agent"
    assert result["agent"]["owner"] == "Product Research"


def test_get_agent_reuses_list_agents_correlation_id(monkeypatch):
    """Proves reuse, not just a coincidentally-matching mock: each call
    to new_correlation_id() here returns a DIFFERENT value, so if
    get_agent minted its own ID instead of reusing list_agents()'s, this
    test would catch it."""
    ids = iter(["first-id", "second-id", "third-id"])
    monkeypatch.setattr("discovery_core.new_correlation_id", lambda: next(ids))
    result = get_agent("Research Agent")
    assert result["correlation_id"] == "first-id"


def test_get_agent_rejects_empty_name():
    with pytest.raises(ValueError):
        get_agent("")


def test_get_agent_rejects_overly_long_name():
    with pytest.raises(ValueError):
        get_agent("x" * 201)


def test_get_agent_raises_key_error_for_unknown_agent():
    with pytest.raises(KeyError):
        get_agent("Nonexistent Agent")


def test_list_tools_returns_all_eight_catalog_entries():
    result = list_tools()
    assert len(result["tools"]) == 8
    assert result["source_name"] == "tool_catalog.json"
    UUID(result["correlation_id"])


def test_get_ownership_returns_all_three_owner_records():
    result = get_ownership()
    assert len(result["owners"]) == 3
    assert result["source_name"] == "ownership.json"
    UUID(result["correlation_id"])


def test_list_agents_propagates_a_clear_error_for_malformed_registry_data(tmp_path, monkeypatch):
    """Confirms the malformed-content rejection is consistent all the
    way up through the composed discovery function, not just the
    low-level helper - using an isolated tmp_path copy, never the real
    connected_environment fixtures."""
    (tmp_path / "agents.json").write_text("{not valid json")
    monkeypatch.setattr("discovery_core.BASE_DIR", tmp_path)

    with pytest.raises(json.JSONDecodeError):
        list_agents()


def test_discovery_core_has_no_mcp_import():
    """The concrete proof of this lab's own claim: no line in
    discovery_core.py imports the mcp package, so this module never
    depends on a running protocol server."""
    lines = Path("discovery_core.py").read_text().splitlines()
    mcp_import_lines = [
        line for line in lines
        if line.startswith("import mcp") or line.startswith("from mcp ")
    ]
    assert mcp_import_lines == []
