"""Four automated tests for AgentGuard v1's scanner."""

from pathlib import Path

from scanner import Agent, evaluate_agent, scan_environment

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BEFORE_PATH = PROJECT_ROOT / "sample_environment_before.json"
AFTER_PATH = PROJECT_ROOT / "sample_environment_after.json"


def test_dangerous_agent_is_high_risk_with_four_findings():
    agent = Agent(
        agent_name="Test Dangerous Agent",
        owner="",
        identity="test-dangerous-agent",
        tools=["read_ticket", "send_email", "delete_customer_record"],
        sensitive_data_access=True,
        human_approval_required=False,
    )
    result = evaluate_agent(agent)
    assert result.risk_level == "HIGH"
    assert result.score == 100
    assert len(result.findings) == 4


def test_read_only_agent_has_no_risk():
    agent = Agent(
        agent_name="Test Read-Only Agent",
        owner="Some Team",
        identity="test-readonly-agent",
        tools=["web_search", "read_public_document"],
        sensitive_data_access=False,
        human_approval_required=False,
    )
    result = evaluate_agent(agent)
    assert result.risk_level == "NO RISK FOUND"
    assert result.score == 0
    assert result.findings == []


def test_unapproved_newsletter_send_is_medium_risk():
    agent = Agent(
        agent_name="Test Newsletter Agent",
        owner="Marketing",
        identity="test-newsletter-agent",
        tools=["send_newsletter"],
        sensitive_data_access=False,
        human_approval_required=False,
    )
    result = evaluate_agent(agent)
    assert result.risk_level == "MEDIUM"
    assert result.score == 30


def test_before_environment_has_two_high_and_after_has_zero_high_three_clear():
    before_results = scan_environment(BEFORE_PATH)
    after_results = scan_environment(AFTER_PATH)

    before_high = [r for r in before_results if r.risk_level == "HIGH"]
    after_high = [r for r in after_results if r.risk_level == "HIGH"]
    after_clear = [r for r in after_results if r.risk_level == "NO RISK FOUND"]

    assert len(before_high) == 2
    assert len(after_high) == 0
    assert len(after_clear) == 3
