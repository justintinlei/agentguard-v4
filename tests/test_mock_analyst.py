"""Tests for mock_analyst.py: deterministic, evidence-grounded output."""

import pytest

from mock_analyst import analyze_with_mock
from retrieval import RetrievalHit
from scanner import Agent, evaluate_agent


def _sample_hit(chunk_id: str = "AGP-001-S01") -> RetrievalHit:
    return RetrievalHit(
        chunk_id=chunk_id,
        policy_id="AGP-001",
        title="Agent Ownership",
        text="Every AI agent must have a named human owner responsible for it.",
        source_path="policies/AGP-001-agent-ownership.md",
        sha256="test-hash-not-real",
        score=1.0,
        matched_terms=("agent", "owner"),
    )


def test_mock_preserves_deterministic_decision_and_cites():
    agent = Agent(
        agent_name="Test Deletion Agent",
        owner="Some Team",
        identity="test-deletion-agent",
        tools=["delete_customer_record"],
        sensitive_data_access=False,
        human_approval_required=False,
    )
    scan_result = evaluate_agent(agent)
    analysis = analyze_with_mock(scan_result, [_sample_hit()])

    assert analysis.deterministic_risk_level == scan_result.risk_level
    assert analysis.deterministic_risk_score == scan_result.score
    assert analysis.citations[0].chunk_id == "AGP-001-S01"


def test_mock_raises_without_evidence():
    agent = Agent(
        agent_name="Test Clean Agent",
        owner="Some Team",
        identity="test-clean-agent",
        tools=["read_public_document"],
        sensitive_data_access=False,
        human_approval_required=False,
    )
    scan_result = evaluate_agent(agent)
    with pytest.raises(ValueError):
        analyze_with_mock(scan_result, [])


def test_mock_is_deterministic_across_calls():
    agent = Agent(
        agent_name="Test Deletion Agent",
        owner="Some Team",
        identity="test-deletion-agent",
        tools=["delete_customer_record"],
        sensitive_data_access=False,
        human_approval_required=False,
    )
    scan_result = evaluate_agent(agent)
    hit = _sample_hit()

    first = analyze_with_mock(scan_result, [hit])
    second = analyze_with_mock(scan_result, [hit])
    assert first == second


def test_mock_summary_mentions_no_risk_for_clean_agent():
    agent = Agent(
        agent_name="Test Clean Agent",
        owner="Some Team",
        identity="test-clean-agent",
        tools=["read_public_document"],
        sensitive_data_access=False,
        human_approval_required=False,
    )
    scan_result = evaluate_agent(agent)
    analysis = analyze_with_mock(scan_result, [_sample_hit()])
    assert "no risk found" in analysis.summary.lower()
