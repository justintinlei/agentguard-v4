"""Tests for retrieval.py: relevant findings should retrieve relevant
policy evidence (positive cases), and irrelevant or absent evidence
should fail safely - a clean empty result, never a crash or a guess
(negative/empty-evidence cases).
"""

from pathlib import Path

from policy_library import load_policy_chunks
from retrieval import build_retrieval_query, format_hits, retrieve
from scanner import Agent, evaluate_agent

POLICIES_DIR = Path(__file__).resolve().parent.parent / "policies"


def _retrieve_for_agent(agent: Agent):
    chunks = load_policy_chunks(POLICIES_DIR)
    scan_result = evaluate_agent(agent)
    query = build_retrieval_query(scan_result)
    return retrieve(query, chunks, top_k=3)


def test_destructive_action_finding_retrieves_human_approval_policy():
    agent = Agent(
        agent_name="Test Deletion Agent",
        owner="Some Team",
        identity="test-deletion-agent",
        tools=["delete_customer_record"],
        sensitive_data_access=False,
        human_approval_required=False,
    )
    hits = _retrieve_for_agent(agent)
    policy_ids = {hit.policy_id for hit in hits}
    assert "AGP-003" in policy_ids


def test_sensitive_data_finding_retrieves_sensitive_data_policy():
    agent = Agent(
        agent_name="Test Data Access Agent",
        owner="Some Team",
        identity="test-data-access-agent",
        tools=["read_customer_profile"],
        sensitive_data_access=True,
        human_approval_required=False,
    )
    hits = _retrieve_for_agent(agent)
    policy_ids = {hit.policy_id for hit in hits}
    assert "AGP-004" in policy_ids


def test_no_owner_finding_retrieves_agent_ownership_policy():
    agent = Agent(
        agent_name="Test Unowned Agent",
        owner="",
        identity="test-unowned-agent",
        tools=["read_public_document"],
        sensitive_data_access=False,
        human_approval_required=False,
    )
    hits = _retrieve_for_agent(agent)
    policy_ids = {hit.policy_id for hit in hits}
    assert "AGP-001" in policy_ids


def test_relevant_query_returns_a_positive_top_score():
    chunks = load_policy_chunks(POLICIES_DIR)
    hits = retrieve("destructive tool needs human approval", chunks, top_k=3)
    assert len(hits) > 0
    assert hits[0].score > 0


def test_query_with_no_matching_vocabulary_returns_no_hits():
    chunks = load_policy_chunks(POLICIES_DIR)
    hits = retrieve("xyzzy quux wobblefrobnicate", chunks, top_k=3)
    assert hits == []


def test_empty_query_string_returns_no_hits():
    chunks = load_policy_chunks(POLICIES_DIR)
    hits = retrieve("", chunks, top_k=3)
    assert hits == []


def test_empty_chunk_list_returns_no_hits():
    hits = retrieve("destructive tool needs human approval", [], top_k=3)
    assert hits == []


def test_clean_agent_with_no_findings_does_not_raise():
    agent = Agent(
        agent_name="Test Clean Agent",
        owner="Some Team",
        identity="test-clean-agent",
        tools=["read_public_document"],
        sensitive_data_access=False,
        human_approval_required=False,
    )
    hits = _retrieve_for_agent(agent)
    assert isinstance(hits, list)


def test_format_hits_shows_score_and_matched_terms():
    chunks = load_policy_chunks(POLICIES_DIR)
    hits = retrieve("destructive tool needs human approval", chunks, top_k=3)
    output = format_hits(hits)
    assert hits[0].chunk_id in output
    assert hits[0].matched_terms[0] in output


def test_format_hits_handles_empty_list():
    output = format_hits([])
    assert output == "No relevant policy evidence found."
