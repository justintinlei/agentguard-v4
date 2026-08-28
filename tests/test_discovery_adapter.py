"""Tests for discovery_adapter.py's MCP-to-Agent contract.

Labs 1-6 built this file up test by test alongside each new function.
Lab 7 (the tests below the analyze_mcp_inventory reuse test) audited
the whole suite instead of adding more of the same: found empty-input
handling was never tested, "missing key" and "wrong-typed key" were
conflated, nothing proved an unexpected extra field gets dropped
rather than smuggled into an Agent, and one real bug (a non-dict
mcp_output crashed with AttributeError instead of a clean ValueError,
now fixed in discovery_adapter.py).
"""

import dataclasses

import pytest

import discovery_adapter
from analysis_schema import GroundedAnalysis
from claude_analyst import UsageRecord
from discovery_adapter import (
    analyze_mcp_inventory,
    extract_provenance,
    mcp_agent_to_agent,
    mcp_inventory_to_agents,
    scan_mcp_inventory,
)
from discovery_core import list_agents
from scanner import Agent, ScanResult


def _valid_mcp_agent() -> dict:
    """A well-formed MCP-shaped agent dict, for tests to mutate one
    field at a time rather than repeating all six every time."""
    return {
        "agent_name": "Test Agent",
        "owner": "Test Team",
        "identity": "test-agent-001",
        "tools": ["read_ticket"],
        "sensitive_data_access": False,
        "human_approval_required": True,
    }


def test_mcp_agent_to_agent_converts_a_real_discovered_agent():
    mcp_agent = list_agents()["agents"][0]

    agent = mcp_agent_to_agent(mcp_agent)

    assert isinstance(agent, Agent)
    assert agent.agent_name == mcp_agent["agent_name"]
    assert agent.owner == mcp_agent["owner"]
    assert agent.identity == mcp_agent["identity"]
    assert agent.tools == mcp_agent["tools"]
    assert agent.sensitive_data_access == mcp_agent["sensitive_data_access"]
    assert agent.human_approval_required == mcp_agent["human_approval_required"]


def test_mcp_agent_to_agent_rejects_a_missing_field():
    mcp_agent = {"agent_name": "Test Agent"}

    with pytest.raises(ValueError, match="missing required field"):
        mcp_agent_to_agent(mcp_agent)


def test_mcp_agent_to_agent_accepts_an_empty_owner():
    """An empty owner is a valid string - v1's own AG-005 rule treats a
    missing owner as a finding to report, not something to reject."""
    mcp_agent = _valid_mcp_agent()
    mcp_agent["owner"] = ""

    agent = mcp_agent_to_agent(mcp_agent)

    assert agent.owner == ""


def test_mcp_agent_to_agent_rejects_a_non_string_agent_name():
    mcp_agent = _valid_mcp_agent()
    mcp_agent["agent_name"] = 12345

    with pytest.raises(ValueError, match="agent_name must be a string"):
        mcp_agent_to_agent(mcp_agent)


def test_mcp_agent_to_agent_rejects_a_non_string_owner():
    mcp_agent = _valid_mcp_agent()
    mcp_agent["owner"] = ["Test Team"]

    with pytest.raises(ValueError, match="owner must be a string"):
        mcp_agent_to_agent(mcp_agent)


def test_mcp_agent_to_agent_rejects_a_non_string_identity():
    mcp_agent = _valid_mcp_agent()
    mcp_agent["identity"] = None

    with pytest.raises(ValueError, match="identity must be a string"):
        mcp_agent_to_agent(mcp_agent)


def test_mcp_agent_to_agent_rejects_non_list_tools():
    mcp_agent = _valid_mcp_agent()
    mcp_agent["tools"] = "read_ticket"

    with pytest.raises(ValueError, match="tools must be a list of strings"):
        mcp_agent_to_agent(mcp_agent)


def test_mcp_agent_to_agent_rejects_a_tools_list_with_a_non_string_entry():
    """The exact scenario that would otherwise crash scanner.py's own
    rules deep inside a tool.startswith(...) call."""
    mcp_agent = _valid_mcp_agent()
    mcp_agent["tools"] = ["read_ticket", 42]

    with pytest.raises(ValueError, match="tools must be a list of strings"):
        mcp_agent_to_agent(mcp_agent)


def test_mcp_agent_to_agent_rejects_a_non_boolean_sensitive_data_access():
    """The exact type-confusion scenario that would otherwise silently
    misclassify an agent's real risk: a truthy string standing in for
    the boolean False."""
    mcp_agent = _valid_mcp_agent()
    mcp_agent["sensitive_data_access"] = "false"

    with pytest.raises(ValueError, match="sensitive_data_access must be true or false"):
        mcp_agent_to_agent(mcp_agent)


def test_mcp_agent_to_agent_rejects_a_non_boolean_human_approval_required():
    mcp_agent = _valid_mcp_agent()
    mcp_agent["human_approval_required"] = "true"

    with pytest.raises(ValueError, match="human_approval_required must be true or false"):
        mcp_agent_to_agent(mcp_agent)


def test_mcp_inventory_to_agents_converts_the_real_discovered_environment():
    mcp_output = list_agents()

    agents = mcp_inventory_to_agents(mcp_output)

    assert len(agents) == 3
    assert all(isinstance(agent, Agent) for agent in agents)
    assert [agent.agent_name for agent in agents] == [
        raw["agent_name"] for raw in mcp_output["agents"]
    ]


def test_mcp_inventory_to_agents_rejects_a_non_list_agents_value():
    with pytest.raises(ValueError, match="must contain an 'agents' list"):
        mcp_inventory_to_agents({"agents": "not-a-list"})


def test_mcp_inventory_to_agents_rejects_a_non_dict_agent_entry():
    with pytest.raises(ValueError, match="index 0 is not an object"):
        mcp_inventory_to_agents({"agents": [42]})


def test_mcp_inventory_to_agents_reports_which_agent_index_is_invalid():
    mcp_output = {"agents": [_valid_mcp_agent(), {"agent_name": "Bad Agent"}]}

    with pytest.raises(ValueError, match="index 1 is invalid"):
        mcp_inventory_to_agents(mcp_output)


def test_extract_provenance_returns_real_values_from_a_discovered_inventory():
    mcp_output = list_agents()

    provenance = extract_provenance(mcp_output)

    assert provenance["source_name"] == "agents.json"
    assert len(provenance["source_sha256"]) == 64
    assert provenance["correlation_id"]


def test_extract_provenance_rejects_a_missing_field():
    mcp_output = {"source_name": "agents.json", "correlation_id": "abc"}

    with pytest.raises(ValueError, match="missing required provenance field 'source_sha256'"):
        extract_provenance(mcp_output)


def test_extract_provenance_rejects_a_non_string_field():
    mcp_output = {"source_name": "agents.json", "source_sha256": "a" * 64, "correlation_id": 12345}

    with pytest.raises(ValueError, match="correlation_id must be a string"):
        extract_provenance(mcp_output)


def test_provenance_and_agents_both_derive_from_the_same_mcp_response():
    """The 'stays attached' property this lab is about: one shared MCP
    response can produce both halves of a future risk report - the
    agent list and its provenance - without either function
    interfering with the other."""
    mcp_output = list_agents()

    agents = mcp_inventory_to_agents(mcp_output)
    provenance = extract_provenance(mcp_output)

    assert len(agents) == 3
    assert set(provenance) == {"source_name", "source_sha256", "correlation_id"}


def test_scan_mcp_inventory_runs_evaluate_agent_on_every_discovered_agent():
    report = scan_mcp_inventory(list_agents())

    assert len(report["results"]) == 3
    assert all(isinstance(result, ScanResult) for result in report["results"])


def test_scan_mcp_inventory_reproduces_the_known_before_state():
    """Ties back to CLAUDE.md's core v1 evidence requirement: the
    BEFORE environment must show exactly two HIGH-risk agents. Verified
    by hand against connected_environment/agents.json: Customer
    Support Agent (delete_customer_record + no approval, sensitive
    access + no approval, empty owner) and Deployment Agent
    (deploy_production + no approval, sensitive access + no approval)
    both score HIGH; Research Agent scores NO RISK FOUND. Same numbers,
    now reproduced through the MCP-discovery path instead of the
    original file-based one."""
    report = scan_mcp_inventory(list_agents())

    risk_levels = [result.risk_level for result in report["results"]]
    assert risk_levels.count("HIGH") == 2
    assert risk_levels.count("NO RISK FOUND") == 1


def test_scan_mcp_inventory_preserves_provenance_alongside_results():
    report = scan_mcp_inventory(list_agents())

    assert report["provenance"]["source_name"] == "agents.json"
    assert len(report["provenance"]["source_sha256"]) == 64


def test_scan_mcp_inventory_reuses_v1s_real_evaluate_agent(monkeypatch):
    """Proves the actual v1 evaluate_agent is invoked - not a
    reimplementation - by wrapping it with a call-counting spy that
    still delegates to the real function."""
    from scanner import evaluate_agent as real_evaluate_agent

    calls = []

    def spy(agent):
        calls.append(agent)
        return real_evaluate_agent(agent)

    monkeypatch.setattr(discovery_adapter, "evaluate_agent", spy)

    report = scan_mcp_inventory(list_agents())

    assert len(calls) == 3
    assert len(report["results"]) == 3


def test_analyze_mcp_inventory_runs_the_v2_pipeline_for_every_discovered_agent():
    """mode="mock" is explicit here and in every test below - never
    relying on an environment default, never "live" - so this test can
    never trigger a real, billed API call."""
    analyses = analyze_mcp_inventory(list_agents(), mode="mock")

    assert len(analyses) == 3
    for analysis, usage in analyses:
        assert isinstance(analysis, GroundedAnalysis)
        assert isinstance(usage, UsageRecord)
        assert usage.mode == "mock"


def test_analyze_mcp_inventory_reuses_v2_services_real_analyze_agent(monkeypatch):
    """Proves the actual v2_service.analyze_agent is invoked - not a
    reimplementation - by wrapping it with a call-counting spy that
    still delegates to the real function, always in mock mode."""
    from v2_service import analyze_agent as real_analyze_agent

    calls = []

    def spy(agent, mode=None):
        calls.append((agent, mode))
        return real_analyze_agent(agent, mode=mode)

    monkeypatch.setattr(discovery_adapter, "analyze_agent", spy)

    analyses = analyze_mcp_inventory(list_agents(), mode="mock")

    assert len(calls) == 3
    assert all(mode == "mock" for _, mode in calls)
    assert len(analyses) == 3


# --- Day 7, Lab 7: audit-found gaps and the one real bug fixed alongside them ---


def test_mcp_inventory_to_agents_accepts_an_empty_agents_list():
    """Zero discovered agents is a legitimate state (a fresh
    environment with nothing registered yet), not an error."""
    assert mcp_inventory_to_agents({"agents": []}) == []


def test_scan_mcp_inventory_handles_an_empty_discovered_environment():
    mcp_output = {
        "agents": [],
        "source_name": "agents.json",
        "source_sha256": "a" * 64,
        "correlation_id": "test-correlation-id",
    }

    report = scan_mcp_inventory(mcp_output)

    assert report["results"] == []
    assert report["provenance"]["source_name"] == "agents.json"


def test_mcp_inventory_to_agents_rejects_a_missing_agents_key():
    """Distinct from a wrong-typed 'agents' value: the key isn't
    there at all."""
    with pytest.raises(ValueError, match="must contain an 'agents' list"):
        mcp_inventory_to_agents({"environment_name": "Test Environment"})


def test_mcp_agent_to_agent_ignores_unexpected_extra_fields():
    """The direct proof of this lab's learning goal: an unexpected
    field in a malformed or malicious agent record is silently
    dropped, never smuggled into the resulting Agent."""
    mcp_agent = _valid_mcp_agent()
    mcp_agent["internal_debug_token"] = "should-never-appear"

    agent = mcp_agent_to_agent(mcp_agent)

    assert "internal_debug_token" not in dataclasses.asdict(agent)
    assert not hasattr(agent, "internal_debug_token")


def test_mcp_inventory_to_agents_rejects_a_non_dict_mcp_output():
    """The bug-fix test: a non-dict mcp_output used to crash with a
    raw AttributeError; it now raises the same clean ValueError every
    other malformed input produces."""
    with pytest.raises(ValueError, match="MCP inventory must be an object"):
        mcp_inventory_to_agents("this is not a dict")


def test_extract_provenance_rejects_a_non_dict_mcp_output():
    with pytest.raises(ValueError, match="MCP inventory must be an object"):
        extract_provenance(["also", "not", "a", "dict"])


def test_complete_discovery_to_analysis_flow_through_the_real_mcp_client():
    """Day 7, Lab 8: the first end-to-end connected scenario. Every
    test above used discovery_core.list_agents() directly - an
    in-process shortcut, not the real MCP protocol. This test spans
    the real transport instead: a genuine MCP client starts
    mcp_server.py as a separate subprocess, discovers the live
    connected-environment inventory over STDIO, and that output flows
    through the adapter into v1's unchanged scanner and v2's unchanged
    analyst - proving the seams from Day 6 and Day 7 actually fit
    together, not just that each side is individually correct."""
    from mcp_client import call_tool_sync

    mcp_output = call_tool_sync("list_agent_inventory")

    report = scan_mcp_inventory(mcp_output)
    assert len(report["results"]) == 3
    risk_levels = [result.risk_level for result in report["results"]]
    assert risk_levels.count("HIGH") == 2
    assert risk_levels.count("NO RISK FOUND") == 1
    assert report["provenance"]["source_name"] == "agents.json"

    analyses = analyze_mcp_inventory(mcp_output, mode="mock")
    assert len(analyses) == 3
    assert all(usage.mode == "mock" for _, usage in analyses)


# --- Day 9, Lab 7 security review: size / count limits are now enforced ---
#
# docs/v3_data_contract.md wrote these limits down; the adapter never
# checked them until this review. Numbers here mirror the constants in
# discovery_adapter.py, which mirror the data contract.


def _inventory_of(n_agents: int) -> dict:
    return {
        "agents": [dict(_valid_mcp_agent(), agent_name=f"Agent {i}") for i in range(n_agents)],
        "source_name": "agents.json",
        "source_sha256": "a" * 64,
        "correlation_id": "test-correlation-id",
    }


def test_mcp_agent_to_agent_rejects_an_oversized_name_field():
    mcp_agent = _valid_mcp_agent()
    mcp_agent["agent_name"] = "x" * 201

    with pytest.raises(ValueError, match="agent_name is 201 characters, over the 200 limit"):
        mcp_agent_to_agent(mcp_agent)


def test_mcp_agent_to_agent_accepts_a_name_field_at_the_limit():
    mcp_agent = _valid_mcp_agent()
    mcp_agent["identity"] = "y" * 200

    assert mcp_agent_to_agent(mcp_agent).identity == "y" * 200


def test_mcp_agent_to_agent_rejects_too_many_tools():
    mcp_agent = _valid_mcp_agent()
    mcp_agent["tools"] = [f"tool_{i}" for i in range(21)]

    with pytest.raises(ValueError, match="tools has 21 entries, over the 20 limit"):
        mcp_agent_to_agent(mcp_agent)


def test_mcp_agent_to_agent_rejects_an_oversized_tool_name():
    mcp_agent = _valid_mcp_agent()
    mcp_agent["tools"] = ["read_ticket", "z" * 101]

    with pytest.raises(ValueError, match="a tool name is 101 characters, over the 100 limit"):
        mcp_agent_to_agent(mcp_agent)


def test_mcp_inventory_to_agents_rejects_more_than_fifty_agents():
    with pytest.raises(ValueError, match="has 51 agents, over the 50 limit"):
        mcp_inventory_to_agents(_inventory_of(51))


def test_mcp_inventory_to_agents_accepts_exactly_fifty_agents():
    assert len(mcp_inventory_to_agents(_inventory_of(50))) == 50


def test_extract_provenance_rejects_an_oversized_correlation_id():
    mcp_output = _inventory_of(0)
    mcp_output["correlation_id"] = "c" * 201

    with pytest.raises(ValueError, match="correlation_id is 201 characters, over the 200 limit"):
        extract_provenance(mcp_output)


def test_real_discovered_inventory_is_within_every_limit():
    # Regression: the synthetic BEFORE inventory must still pass unchanged.
    agents = mcp_inventory_to_agents(list_agents())
    assert len(agents) == 3
