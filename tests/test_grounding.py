"""Tests for grounding.py: valid grounded output passes validation, and
each specific way a model could misbehave (score change, fake citation,
invented quote) is caught and rejected.
"""

from pathlib import Path

import pytest

from analysis_schema import Citation
from grounding import GroundingError, validate_grounding
from mock_analyst import analyze_with_mock
from policy_library import load_policy_chunks
from retrieval import build_retrieval_query, retrieve
from scanner import Agent, evaluate_agent

POLICIES_DIR = Path(__file__).resolve().parent.parent / "policies"


def _build_valid_analysis():
    """Run the real pipeline once and return (analysis, scan_result, evidence)."""
    agent = Agent(
        agent_name="Test Deletion Agent",
        owner="Some Team",
        identity="test-deletion-agent",
        tools=["delete_customer_record"],
        sensitive_data_access=False,
        human_approval_required=False,
    )
    scan_result = evaluate_agent(agent)
    chunks = load_policy_chunks(POLICIES_DIR)
    evidence = retrieve(build_retrieval_query(scan_result), chunks, top_k=3)
    analysis = analyze_with_mock(scan_result, evidence)
    return analysis, scan_result, evidence


def test_valid_grounded_output_passes():
    analysis, scan_result, evidence = _build_valid_analysis()
    validated = validate_grounding(analysis, scan_result, evidence)
    assert validated is analysis


def test_changed_score_is_rejected():
    analysis, scan_result, evidence = _build_valid_analysis()
    tampered = analysis.model_copy(
        update={"deterministic_risk_score": analysis.deterministic_risk_score + 1}
    )
    with pytest.raises(GroundingError):
        validate_grounding(tampered, scan_result, evidence)


def test_unknown_citation_is_rejected():
    analysis, scan_result, evidence = _build_valid_analysis()
    fake_citation = Citation(
        chunk_id="AGP-999-S99",
        quote="This citation references a chunk that was never retrieved.",
    )
    tampered = analysis.model_copy(update={"citations": [fake_citation]})
    with pytest.raises(GroundingError):
        validate_grounding(tampered, scan_result, evidence)


def test_invented_quote_is_rejected():
    analysis, scan_result, evidence = _build_valid_analysis()
    real_chunk_id = evidence[0].chunk_id
    invented_citation = Citation(
        chunk_id=real_chunk_id,
        quote="This exact sentence does not appear anywhere in the policy text.",
    )
    tampered = analysis.model_copy(update={"citations": [invented_citation]})
    with pytest.raises(GroundingError):
        validate_grounding(tampered, scan_result, evidence)


def test_whitespace_only_quote_is_rejected():
    """A quote that's only whitespace normalizes to "", and "" is a
    substring of everything - without an explicit empty-quote check, a
    real chunk_id paired with a blank quote would pass unconditionally.
    """
    analysis, scan_result, evidence = _build_valid_analysis()
    real_chunk_id = evidence[0].chunk_id
    blank_citation = Citation(chunk_id=real_chunk_id, quote=" ")
    tampered = analysis.model_copy(update={"citations": [blank_citation]})
    with pytest.raises(GroundingError):
        validate_grounding(tampered, scan_result, evidence)
