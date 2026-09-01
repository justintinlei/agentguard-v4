"""Failure-path tests - the system fails closed.

Seeded in Day 8 Lab 2 with two general "no unsafe shortcut" guarantees.
Day 8 Lab 3 adds the rollback-after-merge refusal. Day 8 Lab 4 adds the
"the audit trail stays complete when work does not succeed" checks. Day 8
Lab 5 adds "a failed verification stops GitHub planning". Day 8 Lab 6 adds
"a stale approval forces a new human review". Day 8 Lab 7 adds "a GitHub
auth / command failure is surfaced without partial continuation".
"""

import subprocess

import pytest

from approval import approval_is_current, decide, validate_approval
from audit_db import list_events, record_event
from github_plan import GitHubPlan, create_plan, execute_plan
from proposal_hash import sha256_value
from remediation_templates import RemediationProposal, build_proposal
from rollback import rollback_plan
from verifier import require_verified, verify
from workflow import ALLOWED_TRANSITIONS, WorkflowState, record_terminal_state, transition


def test_unapproved_repository_format_is_blocked() -> None:
    with pytest.raises(ValueError, match="OWNER/REPO"):
        create_plan("not a safe repo value", "abc123")


def test_workflow_cannot_skip_from_proposed_to_verified() -> None:
    with pytest.raises(ValueError, match="Invalid transition"):
        transition(WorkflowState("w1", "PROPOSED"), "VERIFIED")


def test_rollback_after_merge_is_refused() -> None:
    # A merged change is shared history - the only safe undo is a reviewed
    # revert PR, so rollback_plan produces no command at all.
    with pytest.raises(ValueError, match="refused after merge"):
        rollback_plan(
            "justintinlei/agentguard-remediation-demo",
            17,
            "agentguard/workflow-17",
            merged=True,
        )


# --- Day 8 Lab 4: the audit trail stays complete when work does not succeed


def _record_prefix(db, workflow_id, states_after_discovered):
    """Record DISCOVERED then each further state through transition()."""
    state = WorkflowState(workflow_id, "DISCOVERED")
    record_event(db, workflow_id, "environment_discovered", state.state, {})
    for nxt in states_after_discovered:
        state = transition(state, nxt)
        record_event(db, workflow_id, f"moved_to_{nxt.lower()}", state.state, {})
    return state


def _assert_legal_walk(db, workflow_id):
    states = [e["state"] for e in list_events(db, workflow_id)]
    for here, nxt in zip(states, states[1:]):
        assert nxt in ALLOWED_TRANSITIONS[here], f"{here} -> {nxt} is not a legal arrow"
    return states


def test_failed_workflow_still_has_a_complete_audit_trail(tmp_path):
    db = tmp_path / "audit.db"
    state = _record_prefix(db, "wf-1", ["SCANNED", "PROPOSED", "APPROVED"])

    record_terminal_state(db, state, "FAILED", reason="verification check 'hash_match' failed")

    events = list_events(db, "wf-1")
    assert events[-1]["state"] == "FAILED"
    assert events[-1]["event_type"] == "workflow_failed"
    assert events[-1]["payload"]["reason"] == "verification check 'hash_match' failed"
    assert _assert_legal_walk(db, "wf-1") == ["DISCOVERED", "SCANNED", "PROPOSED", "APPROVED", "FAILED"]


def test_rejected_workflow_is_recorded_not_dropped(tmp_path):
    db = tmp_path / "audit.db"
    state = _record_prefix(db, "wf-2", ["SCANNED", "PROPOSED"])

    record_terminal_state(db, state, "REJECTED", reason="reviewer declined the proposal")

    events = list_events(db, "wf-2")
    assert events[-1]["state"] == "REJECTED"
    assert events[-1]["event_type"] == "workflow_rejected"
    assert _assert_legal_walk(db, "wf-2") == ["DISCOVERED", "SCANNED", "PROPOSED", "REJECTED"]


# --- Day 8 Lab 5: a failed verification stops GitHub planning --------------

VERIFY_ENV = {
    "environment_name": "Failure Path Demo",
    "source_system": "synthetic-agent-registry",
    "agents": [
        {
            "agent_name": "Billing Agent",
            "owner": "Finance Platform",
            "identity": "billing-agent-prod",
            "tools": ["read_invoice"],
            "sensitive_data_access": False,
            "human_approval_required": False,
        },
    ],
}

# A hand-built proposal that would make the agent HIGH risk (destructive
# tool + sensitive data, still no approval) - verify() must fail it on
# "high-risk count did not increase".
RISK_RAISING_PROPOSAL = RemediationProposal(
    template_id="REQUIRE_HUMAN_APPROVAL",
    agent_name="Billing Agent",
    field_changes={"tools": ["delete_invoice"], "sensitive_data_access": True},
    rationale="synthetic Lab 5 verification-failure scenario",
    source_sha256="0" * 64,
)


def test_a_failed_verification_stops_github_planning(tmp_path):
    db = tmp_path / "audit.db"
    state = _record_prefix(db, "wf-vf", ["SCANNED", "PROPOSED", "APPROVED"])

    result = verify(VERIFY_ENV, RISK_RAISING_PROPOSAL)
    assert result.passed is False

    # The gate stops the flow here - create_plan() is never reached.
    with pytest.raises(ValueError, match="GitHub planning is blocked"):
        require_verified(result)

    failed_checks = [c["name"] for c in result.checks if not c["passed"]]
    record_terminal_state(
        db, state, "FAILED",
        reason="verification failed",
        details={"failed_checks": failed_checks},
    )

    events = list_events(db, "wf-vf")
    assert events[-1]["state"] == "FAILED"
    assert events[-1]["event_type"] == "workflow_failed"
    assert "high-risk count did not increase" in events[-1]["payload"]["failed_checks"]
    assert _assert_legal_walk(db, "wf-vf")[-1] == "FAILED"


def test_a_passing_verification_allows_github_planning():
    # Positive control: the gate is not just rejecting everything.
    ok_proposal = RemediationProposal(
        template_id="REQUIRE_HUMAN_APPROVAL",
        agent_name="Billing Agent",
        field_changes={"human_approval_required": True},
        rationale="synthetic Lab 5 positive control",
        source_sha256="0" * 64,
    )
    result = require_verified(verify(VERIFY_ENV, ok_proposal))
    assert result.passed is True

    plan = create_plan("justintinlei/agentguard-remediation-demo", "wf-ok")
    assert isinstance(plan, GitHubPlan)
    assert len(plan.commands) == 5


# --- Day 8 Lab 6: a stale approval forces a new human review --------------

STALE_ENV = {
    "environment_name": "Stale Approval Demo",
    "source_system": "synthetic-agent-registry",
    "agents": [
        {
            "agent_name": "Support Agent",
            "owner": "Customer Ops",
            "identity": "support-agent-prod",
            "tools": ["read_ticket", "delete_customer_record"],
            "sensitive_data_access": True,
            "human_approval_required": False,
        },
        {
            "agent_name": "Deployment Agent",
            "owner": "Platform Engineering",
            "identity": "deploy-agent-prod",
            "tools": ["read_repository", "deploy_production"],
            "sensitive_data_access": True,
            "human_approval_required": False,
        },
    ],
}


def _approve_support_change():
    """Approve turning on human approval for the Support Agent.
    Returns (record, proposal_hash, source_hash, env-as-approved)."""
    env = {k: (v if k != "agents" else [dict(a) for a in v]) for k, v in STALE_ENV.items()}
    source_hash = sha256_value(env)
    proposal = build_proposal("REQUIRE_HUMAN_APPROVAL", env["agents"][0], source_hash)
    proposal_hash = sha256_value(proposal.to_dict())
    record = decide(
        "wf-stale", proposal_hash, source_hash, "Justin", "APPROVE",
        "reviewed the one-field change",
    )
    return record, proposal_hash, source_hash, env


def test_source_drift_after_approval_forces_a_new_review(tmp_path):
    db = tmp_path / "audit.db"
    record, proposal_hash, source_hash, _ = _approve_support_change()
    state = _record_prefix(db, "wf-stale", ["SCANNED", "PROPOSED", "APPROVED"])

    # After sign-off, someone widens a DIFFERENT agent's tools.
    drifted = {k: (v if k != "agents" else [dict(a) for a in v]) for k, v in STALE_ENV.items()}
    drifted["agents"][1]["tools"] = drifted["agents"][1]["tools"] + ["admin_override"]
    drifted_hash = sha256_value(drifted)

    # The approval no longer matches the world it was granted for.
    assert approval_is_current(record, proposal_hash, drifted_hash) is False
    with pytest.raises(ValueError, match="source changed"):
        validate_approval(record, proposal_hash, drifted_hash)

    # The workflow fails closed and the reason is recorded.
    record_terminal_state(
        db, state, "FAILED",
        reason="approval is stale: source changed",
        details={"approved_source_sha256": source_hash, "current_source_sha256": drifted_hash},
    )
    events = list_events(db, "wf-stale")
    assert events[-1]["event_type"] == "workflow_failed"
    assert _assert_legal_walk(db, "wf-stale")[-1] == "FAILED"

    # A NEW human review against the changed world is required - and enough.
    new_record = decide(
        "wf-stale-2", proposal_hash, drifted_hash, "Dana", "APPROVE",
        "re-reviewed after the environment changed",
    )
    assert approval_is_current(new_record, proposal_hash, drifted_hash) is True
    validate_approval(new_record, proposal_hash, drifted_hash)  # no exception

    # The original approval is still spent - it never becomes current again.
    assert approval_is_current(record, proposal_hash, drifted_hash) is False


def test_proposal_drift_after_approval_forces_a_new_review(tmp_path):
    db = tmp_path / "audit.db"
    record, _, source_hash, env = _approve_support_change()
    state = _record_prefix(db, "wf-pd", ["SCANNED", "PROPOSED", "APPROVED"])

    # The proposal is regenerated, this time targeting a different agent.
    other = build_proposal("REQUIRE_HUMAN_APPROVAL", env["agents"][1], source_hash)
    other_hash = sha256_value(other.to_dict())

    assert approval_is_current(record, other_hash, source_hash) is False
    with pytest.raises(ValueError, match="proposal changed"):
        validate_approval(record, other_hash, source_hash)

    record_terminal_state(
        db, state, "FAILED", reason="approval is stale: proposal changed",
    )
    assert _assert_legal_walk(db, "wf-pd")[-1] == "FAILED"

    new_record = decide(
        "wf-pd-2", other_hash, source_hash, "Dana", "APPROVE", "reviewed the new proposal",
    )
    assert approval_is_current(new_record, other_hash, source_hash) is True


# --- Day 8 Lab 7: a GitHub auth / command failure is surfaced, no partial run

DEMO_REPO = "justintinlei/agentguard-remediation-demo"

# A realistic "gh is not logged in" message. Synthetic - no real token.
GH_AUTH_STDERR = (
    "gh: To get started with GitHub CLI, please run: gh auth login\n"
    "HTTP 401: Bad credentials"
)


class _FakeRun:
    """Stand-in for subprocess.run.

    Records every call. Succeeds until a command whose token list contains
    `fail_on` is seen, then raises CalledProcessError exactly as `gh` /
    `git` would on a non-zero exit. `fail_on=""` never matches (a token is
    never the empty string); pass a sentinel to fail on everything.
    """

    def __init__(self, fail_on=None, stderr=""):
        self.fail_on = fail_on
        self.stderr = stderr
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append(list(args))
        if self.fail_on is not None and (self.fail_on == "*" or self.fail_on in args):
            raise subprocess.CalledProcessError(1, list(args), stderr=self.stderr)
        return subprocess.CompletedProcess(list(args), 0, stdout="ok\n", stderr="")


def test_a_github_auth_failure_is_surfaced(monkeypatch):
    fake = _FakeRun(fail_on="--draft", stderr=GH_AUTH_STDERR)
    monkeypatch.setattr(subprocess, "run", fake)

    plan = create_plan(DEMO_REPO, "wf-authfail")
    with pytest.raises(subprocess.CalledProcessError) as exc:
        execute_plan(plan, live=True)

    # The error is surfaced with its exit code and the auth hint intact.
    assert exc.value.returncode == 1
    assert "gh auth login" in exc.value.stderr


def test_no_command_runs_after_a_failed_one(monkeypatch):
    # command 4 of 5 is `git push -u origin <branch>` - fail there.
    fake = _FakeRun(fail_on="push", stderr="fatal: Authentication failed")
    monkeypatch.setattr(subprocess, "run", fake)

    plan = create_plan(DEMO_REPO, "wf-pushfail")
    with pytest.raises(subprocess.CalledProcessError):
        execute_plan(plan, live=True)

    # checkout, add, commit, push were attempted; `gh pr create` was NOT.
    assert len(fake.calls) == 4
    assert not any("gh" in call for call in fake.calls)


def test_a_dry_run_is_unaffected_by_a_broken_gh(monkeypatch):
    fake = _FakeRun(fail_on="*", stderr=GH_AUTH_STDERR)  # would raise on any call
    monkeypatch.setattr(subprocess, "run", fake)

    plan = create_plan(DEMO_REPO, "wf-dry")
    rows = execute_plan(plan)  # no live= -> dry run

    assert [r["status"] for r in rows] == ["DRY_RUN"] * 5
    assert fake.calls == []  # the broken gh was never called


def test_a_failed_live_run_is_recorded_as_verified_then_failed(tmp_path, monkeypatch):
    db = tmp_path / "audit.db"
    state = _record_prefix(db, "wf-gh", ["SCANNED", "PROPOSED", "APPROVED", "VERIFIED"])

    fake = _FakeRun(fail_on="--draft", stderr=GH_AUTH_STDERR)
    monkeypatch.setattr(subprocess, "run", fake)

    plan = create_plan(DEMO_REPO, "wf-gh")
    try:
        execute_plan(plan, live=True)
        raised = None
    except subprocess.CalledProcessError as exc:
        raised = exc

    assert raised is not None
    failed_command = raised.cmd

    # The workflow never reached DRAFT_PR_CREATED - the PR was not created.
    # It fails closed from VERIFIED.
    record_terminal_state(
        db, state, "FAILED",
        reason="GitHub command failed",
        details={
            "failed_command": failed_command,
            "returncode": raised.returncode,
            "stderr": raised.stderr,
        },
    )

    events = list_events(db, "wf-gh")
    assert events[-1]["state"] == "FAILED"
    assert events[-1]["event_type"] == "workflow_failed"
    assert events[-1]["payload"]["failed_command"][:3] == ["gh", "pr", "create"]
    assert "DRAFT_PR_CREATED" not in {e["state"] for e in events}
    assert _assert_legal_walk(db, "wf-gh") == [
        "DISCOVERED", "SCANNED", "PROPOSED", "APPROVED", "VERIFIED", "FAILED",
    ]


def test_all_commands_succeeding_is_the_positive_control(monkeypatch):
    fake = _FakeRun()  # never fails
    monkeypatch.setattr(subprocess, "run", fake)

    plan = create_plan(DEMO_REPO, "wf-ok")
    rows = execute_plan(plan, live=True)

    assert [r["status"] for r in rows] == ["EXECUTED"] * 5
    assert [call[0] for call in fake.calls] == ["git", "git", "git", "git", "gh"]


def test_rollback_commands_are_run_manually_so_a_failure_reaches_the_operator():
    # rollback has no executor - the operator runs the two commands and
    # sees any `gh` / `git` error directly. This keeps that fact pinned.
    import rollback

    plan = rollback_plan(DEMO_REPO, 17, "agentguard/workflow-17", merged=False)
    assert len(plan) == 2
    assert not hasattr(rollback, "execute_rollback")
    assert not hasattr(rollback, "subprocess")
