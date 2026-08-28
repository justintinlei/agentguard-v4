"""Tests for claude_analyst.py: text extraction, the missing-key failure
path, request-level controls, structured-output parsing, and cost
estimation. No test here makes a real network call or needs a real key.
"""

import json
from pathlib import Path
from types import SimpleNamespace

import anthropic
import httpx
import pytest

import claude_analyst
from analysis_schema import GroundedAnalysis
from claude_analyst import _api_compatible_schema, _extract_text, analyze_with_claude
from grounding import validate_grounding
from mock_analyst import analyze_with_mock
from policy_library import load_policy_chunks
from retrieval import build_retrieval_query, retrieve
from scanner import Agent, evaluate_agent

POLICIES_DIR = Path(__file__).resolve().parent.parent / "policies"


def test_api_compatible_schema_strips_unsupported_keywords_recursively():
    schema = _api_compatible_schema(GroundedAnalysis.model_json_schema())

    score_property = schema["properties"]["deterministic_risk_score"]
    assert "minimum" not in score_property
    assert "maximum" not in score_property

    citations_property = schema["properties"]["citations"]
    assert "minItems" not in citations_property
    assert "maxItems" not in citations_property

    # Citation is a nested model, defined under $defs - confirm the
    # stripping reached that far, not just the top-level properties.
    citation_def = schema["$defs"]["Citation"]["properties"]
    assert "minLength" not in citation_def["quote"]
    assert "maxLength" not in citation_def["quote"]


def test_extract_text_joins_only_text_blocks():
    message = SimpleNamespace(
        content=[
            SimpleNamespace(type="text", text="first"),
            SimpleNamespace(type="other", text="ignored"),
            SimpleNamespace(type="text", text="second"),
        ]
    )
    assert _extract_text(message) == "first\nsecond"


def test_extract_text_rejects_empty_text_response():
    message = SimpleNamespace(content=[SimpleNamespace(type="other", text="ignored")])
    with pytest.raises(ValueError, match="no text block"):
        _extract_text(message)


def test_analyze_with_claude_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        analyze_with_claude(scan_result=None, evidence=[])


def test_analyze_with_claude_raises_on_timeout(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-placeholder")

    class FakeMessages:
        def create(self, **kwargs):
            request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
            raise anthropic.APITimeoutError(request)

    class FakeAnthropic:
        def __init__(self, **kwargs):
            self.messages = FakeMessages()

    monkeypatch.setattr("anthropic.Anthropic", FakeAnthropic)

    scan_result = evaluate_agent(
        Agent(
            agent_name="Test Deletion Agent",
            owner="Some Team",
            identity="test-deletion-agent",
            tools=["delete_customer_record"],
            sensitive_data_access=False,
            human_approval_required=False,
        )
    )

    with pytest.raises(RuntimeError, match="timed out"):
        analyze_with_claude(scan_result, evidence=[])


def test_analyze_with_claude_raises_on_malformed_json(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-placeholder")

    class FakeMessages:
        def create(self, **kwargs):
            return SimpleNamespace(
                stop_reason="end_turn",
                content=[SimpleNamespace(type="text", text="not valid json {")],
                usage=SimpleNamespace(input_tokens=10, output_tokens=5),
            )

    class FakeAnthropic:
        def __init__(self, **kwargs):
            self.messages = FakeMessages()

    monkeypatch.setattr("anthropic.Anthropic", FakeAnthropic)

    scan_result = evaluate_agent(
        Agent(
            agent_name="Test Deletion Agent",
            owner="Some Team",
            identity="test-deletion-agent",
            tools=["delete_customer_record"],
            sensitive_data_access=False,
            human_approval_required=False,
        )
    )

    with pytest.raises(RuntimeError, match="not valid JSON"):
        analyze_with_claude(scan_result, evidence=[])


def test_analyze_with_claude_raises_on_refusal(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-placeholder")

    class FakeMessages:
        def create(self, **kwargs):
            return SimpleNamespace(
                stop_reason="refusal",
                content=[],
                usage=SimpleNamespace(input_tokens=10, output_tokens=0),
            )

    class FakeAnthropic:
        def __init__(self, **kwargs):
            self.messages = FakeMessages()

    monkeypatch.setattr("anthropic.Anthropic", FakeAnthropic)

    scan_result = evaluate_agent(
        Agent(
            agent_name="Test Deletion Agent",
            owner="Some Team",
            identity="test-deletion-agent",
            tools=["delete_customer_record"],
            sensitive_data_access=False,
            human_approval_required=False,
        )
    )

    with pytest.raises(RuntimeError, match="declined"):
        analyze_with_claude(scan_result, evidence=[])


def test_analyze_with_claude_applies_controls_and_parses_response(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-placeholder")
    monkeypatch.setenv("AGENTGUARD_MAX_OUTPUT_TOKENS", "500")

    captured = {}

    agent = Agent(
        agent_name="Test Deletion Agent",
        owner="Some Team",
        identity="test-deletion-agent",
        tools=["delete_customer_record"],
        sensitive_data_access=False,
        human_approval_required=False,
    )
    scan_result = evaluate_agent(agent)

    fake_response_json = json.dumps(
        {
            "agent_name": scan_result.agent.agent_name,
            "deterministic_risk_level": scan_result.risk_level,
            "deterministic_risk_score": scan_result.score,
            "summary": "Test summary.",
            "why_it_matters": "Test why it matters.",
            "recommended_next_step": "Test next step.",
            "citations": [{"chunk_id": "AGP-003-S01", "quote": "Test quote."}],
        }
    )

    class FakeMessages:
        def create(self, **kwargs):
            captured["create_kwargs"] = kwargs
            return SimpleNamespace(
                content=[SimpleNamespace(type="text", text=fake_response_json)],
                usage=SimpleNamespace(input_tokens=120, output_tokens=80),
            )

    class FakeAnthropic:
        def __init__(self, **kwargs):
            captured["client_kwargs"] = kwargs
            self.messages = FakeMessages()

    monkeypatch.setattr("anthropic.Anthropic", FakeAnthropic)

    analysis, usage = analyze_with_claude(scan_result, evidence=[])

    # Product data: a real, validated GroundedAnalysis.
    assert isinstance(analysis, GroundedAnalysis)
    assert analysis.deterministic_risk_level == scan_result.risk_level
    assert analysis.deterministic_risk_score == scan_result.score
    assert analysis.citations[0].chunk_id == "AGP-003-S01"

    # Observability data: what the call actually cost/took.
    assert usage.mode == "live"
    assert usage.input_tokens == 120
    assert usage.output_tokens == 80
    assert usage.estimated_cost_usd > 0

    # Request-level controls actually reached the request.
    assert captured["client_kwargs"]["timeout"] == claude_analyst.REQUEST_TIMEOUT_SECONDS
    assert captured["client_kwargs"]["max_retries"] == claude_analyst.MAX_RETRIES
    assert captured["create_kwargs"]["max_tokens"] == 500
    assert captured["create_kwargs"]["output_config"]["effort"] == "low"
    assert captured["create_kwargs"]["output_config"]["format"]["type"] == "json_schema"


def test_estimate_cost_uses_per_million_token_rates(monkeypatch):
    monkeypatch.setenv("AGENTGUARD_ESTIMATED_INPUT_COST_PER_MTOK", "3.00")
    monkeypatch.setenv("AGENTGUARD_ESTIMATED_OUTPUT_COST_PER_MTOK", "15.00")
    assert claude_analyst.estimate_cost(1_000_000, 1_000_000) == 18.0


def test_mock_and_live_preserve_identical_risk_despite_different_prose(monkeypatch):
    """Mock and live are two different explainers for the same
    deterministic decision - their prose can differ, but the risk level
    and score they report must not, and both must independently ground.
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-placeholder")

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

    mock_analysis = analyze_with_mock(scan_result, evidence)

    # A fake "live" response with deliberately different wording, but the
    # same required risk fields - a different explainer, same source of truth.
    fake_live_json = json.dumps(
        {
            "agent_name": scan_result.agent.agent_name,
            "deterministic_risk_level": scan_result.risk_level,
            "deterministic_risk_score": scan_result.score,
            "summary": "A completely different summary, worded nothing like the mock template.",
            "why_it_matters": "A differently-phrased explanation of why this matters.",
            "recommended_next_step": "A differently-worded recommended next step.",
            "citations": [
                {"chunk_id": evidence[0].chunk_id, "quote": evidence[0].text[:80]}
            ],
        }
    )

    class FakeMessages:
        def create(self, **kwargs):
            return SimpleNamespace(
                content=[SimpleNamespace(type="text", text=fake_live_json)],
                usage=SimpleNamespace(input_tokens=100, output_tokens=50),
            )

    class FakeAnthropic:
        def __init__(self, **kwargs):
            self.messages = FakeMessages()

    monkeypatch.setattr("anthropic.Anthropic", FakeAnthropic)

    live_analysis, _usage = analyze_with_claude(scan_result, evidence)

    # Same deterministic risk, regardless of which explainer produced it.
    assert mock_analysis.deterministic_risk_level == live_analysis.deterministic_risk_level
    assert mock_analysis.deterministic_risk_score == live_analysis.deterministic_risk_score
    assert mock_analysis.deterministic_risk_level == scan_result.risk_level
    assert mock_analysis.deterministic_risk_score == scan_result.score

    # But the explanations are genuinely different texts.
    assert mock_analysis.summary != live_analysis.summary

    # Both are independently grounded - identical risk isn't enough on
    # its own, each analysis's own citations must hold up too.
    validate_grounding(mock_analysis, scan_result, evidence)
    validate_grounding(live_analysis, scan_result, evidence)
