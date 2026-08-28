"""Integration tests for v2_service.analyze_agent(): prove the full mock
pipeline - not just the grounding validator in isolation - preserves v1's
deterministic score and produces valid citations, for every real synthetic
agent in the before-environment.
"""

import json
from pathlib import Path

import pytest

from audit_log import append_event, log_analysis_event
from grounding import validate_grounding
from policy_library import load_policy_chunks
from retrieval import build_retrieval_query, retrieve
from scanner import Agent, evaluate_agent
from v2_service import analyze_agent

BASE = Path(__file__).resolve().parent.parent
POLICIES_DIR = BASE / "policies"


def _load_agents() -> list[Agent]:
    data = json.loads((BASE / "sample_environment_before.json").read_text())
    return [Agent(**item) for item in data]


def test_deterministic_score_is_preserved_for_every_agent():
    for agent in _load_agents():
        scan_result = evaluate_agent(agent)
        analysis, _usage = analyze_agent(agent, mode="mock")
        assert analysis.deterministic_risk_level == scan_result.risk_level
        assert analysis.deterministic_risk_score == scan_result.score


def test_every_citation_is_valid_for_every_agent():
    for agent in _load_agents():
        scan_result = evaluate_agent(agent)
        chunks = load_policy_chunks(POLICIES_DIR)
        query = build_retrieval_query(scan_result)
        evidence = retrieve(query, chunks)

        analysis, _usage = analyze_agent(agent, mode="mock")

        assert analysis.citations
        validate_grounding(analysis, scan_result, evidence)


def test_v2_cases_have_relevance_and_completeness_review_fields():
    """Every golden case must have a place for a human reviewer's
    relevance/completeness judgment - grounding.py can prove a citation is
    real text, but not that it was the right citation to pick, or that the
    explanation covered every finding. These fields start unreviewed
    (None) since only a human, not the AI, can fill in the verdict.
    """
    cases = json.loads((BASE / "evals" / "v2_cases.json").read_text())
    for case in cases:
        assert "relevance_reviewed" in case
        assert "completeness_reviewed" in case
        assert "reviewer_notes" in case
        assert case["relevance_reviewed"] is None or isinstance(case["relevance_reviewed"], bool)
        assert case["completeness_reviewed"] is None or isinstance(case["completeness_reviewed"], bool)
        assert isinstance(case["reviewer_notes"], str)


def test_append_event_appends_one_line_per_call(tmp_path):
    log_path = tmp_path / "audit_events.jsonl"

    append_event(log_path, "first", {"n": 1})
    append_event(log_path, "second", {"n": 2})

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2

    first_record = json.loads(lines[0])
    second_record = json.loads(lines[1])
    assert first_record["event_type"] == "first"
    assert second_record["event_type"] == "second"
    assert "timestamp" in first_record
    assert "timestamp" in second_record


def test_append_event_payload_round_trips_exactly(tmp_path):
    log_path = tmp_path / "audit_events.jsonl"
    payload = {"agent_name": "Customer Support Agent", "risk_level": "HIGH", "risk_score": 100, "mode": "mock"}

    append_event(log_path, "analysis_complete", payload)

    record = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
    assert record["payload"] == payload


def test_append_event_refuses_a_payload_containing_a_secret_pattern(tmp_path):
    log_path = tmp_path / "audit_events.jsonl"
    # Built at runtime, not written as one literal - this source file must
    # never contain a contiguous string matching the real secret pattern.
    fake_key = "sk-ant-" + "x" * 20

    with pytest.raises(ValueError):
        append_event(log_path, "leak", {"key": fake_key})

    assert not log_path.exists()


def test_log_analysis_event_records_latency_tokens_model_mode_and_cost(tmp_path):
    log_path = tmp_path / "audit_events.jsonl"
    agent = _load_agents()[0]

    analysis, usage = analyze_agent(agent, mode="mock")
    log_analysis_event(log_path, analysis, usage)

    record = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
    payload = record["payload"]

    assert payload["agent_name"] == analysis.agent_name
    assert payload["risk_level"] == analysis.deterministic_risk_level
    assert payload["risk_score"] == analysis.deterministic_risk_score
    assert payload["mode"] == usage.mode
    assert payload["model"] == usage.model
    assert payload["input_tokens"] == usage.input_tokens
    assert payload["output_tokens"] == usage.output_tokens
    assert payload["latency_ms"] == usage.latency_ms
    assert payload["estimated_cost_usd"] == usage.estimated_cost_usd
