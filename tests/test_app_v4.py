"""Tests for app_v4.py - the v4 Streamlit page.

Day 2 Lab 3: a safety-boundary list + a GitHub-CLI auth panel (which must
never surface a token, however `gh` formats its output).
Day 9 Lab 1: JOURNEY_STAGES, the read-only six-stage map.
Day 9 Lab 2: build_ui_proposal() - agent + allowlisted template -> a
RemediationProposal + its hashes, nothing applied.

Importing app_v4 is side-effect free: render() only runs under the
`__main__` guard.
"""

import json
from pathlib import Path

import pytest

import app_v4
import github_plan
import workflow
from remediation_templates import RemediationProposal

APP_SOURCE = (Path(__file__).resolve().parent.parent / "app_v4.py").read_text()

# A fake, token-shaped string built at runtime so this file never contains
# a contiguous literal matching scripts/check_no_secrets.py's pattern
# (same rule tests/test_app_v3.py follows).
FAKE_TOKEN = "gho_" + "A" * 36


def test_app_v4_compiles():
    compile(APP_SOURCE, "app_v4.py", "exec")


def test_boundary_notes_state_the_pledge():
    joined = " ".join(app_v4.BOUNDARY_NOTES).lower()
    assert "synthetic" in joined
    assert "dry-run" in joined
    assert "draft" in joined
    assert "no github token is stored" in joined
    assert "sole authority" in joined


def test_auth_status_strips_any_token_line(monkeypatch):
    fake_output = (
        "github.com\n"
        "  Logged in to github.com account octocat\n"
        f"  - Token: {FAKE_TOKEN}\n"
        "  - Token scopes: 'gist', 'read:org', 'repo'\n"
    )

    class _Completed:
        returncode = 0
        stdout = ""
        stderr = fake_output

    monkeypatch.setattr(app_v4.shutil, "which", lambda _name: "/usr/bin/gh")
    monkeypatch.setattr(app_v4.subprocess, "run", lambda *a, **k: _Completed())

    status = app_v4.github_auth_status()
    assert status["gh_installed"] is True
    assert status["authenticated"] is True
    # The token value line is dropped entirely...
    assert FAKE_TOKEN not in status["summary"]
    assert "- Token: " not in status["summary"]
    # ...but non-secret context (account, scopes) is kept for the viewer.
    assert "Logged in to github.com account octocat" in status["summary"]
    assert "Token scopes" in status["summary"]


def test_auth_status_handles_gh_not_installed(monkeypatch):
    monkeypatch.setattr(app_v4.shutil, "which", lambda _name: None)
    status = app_v4.github_auth_status()
    assert status == {
        "gh_installed": False,
        "authenticated": False,
        "summary": "GitHub CLI (`gh`) is not installed. Run `brew install gh`.",
    }


def test_render_is_guarded_not_run_on_import():
    # If render() ran on import, importing app_v4 above would have raised a
    # Streamlit "missing ScriptRunContext" / set_page_config error path.
    assert callable(app_v4.render)
    assert 'if __name__ == "__main__":' in APP_SOURCE


# --- Day 9 Lab 1: the remediation journey map ------------------------------

STAGE_KEYS = {"step", "name", "does", "produces", "authority", "state"}
EXPECTED_NAMES = ["Discovery", "Proposal", "Approval", "Verification", "Plan", "Audit"]


def test_journey_has_the_six_stages_in_order():
    stages = app_v4.JOURNEY_STAGES
    assert [s["name"] for s in stages] == EXPECTED_NAMES
    assert [s["step"] for s in stages] == [1, 2, 3, 4, 5, 6]


def test_every_stage_has_all_the_fields_filled_in():
    for stage in app_v4.JOURNEY_STAGES:
        assert set(stage) == STAGE_KEYS
        assert isinstance(stage["step"], int)
        for key in STAGE_KEYS - {"step"}:
            assert isinstance(stage[key], str) and stage[key].strip()


def test_each_stage_state_is_a_real_workflow_state():
    # The map cannot drift from the state machine: every `state` token is one
    # of workflow.STATES, and together they are the six non-error states in
    # workflow order.
    stage_states = [s["state"] for s in app_v4.JOURNEY_STAGES]
    for state in stage_states:
        assert state in workflow.STATES
    assert stage_states == [
        "DISCOVERED", "PROPOSED", "APPROVED", "VERIFIED", "DRAFT_PR_CREATED", "ROLLED_BACK",
    ]


def test_the_map_states_the_authority_invariants():
    by_name = {s["name"]: s for s in app_v4.JOURNEY_STAGES}

    discovery = by_name["Discovery"]["authority"].lower()
    assert "scanner.py" in discovery and "sole authority" in discovery

    proposal = by_name["Proposal"]["authority"].lower()
    assert "allowlisted" in proposal and "free-form" in proposal
    assert "never apply or score" in proposal

    approval = by_name["Approval"]["authority"].lower()
    assert "approves intent" in approval

    verification = by_name["Verification"]["authority"].lower()
    assert "require_verified()" in verification and "fail closed" in verification

    plan = by_name["Plan"]["authority"].lower()
    assert "draft pr only" in plan
    assert "no merge" in plan and "--force" in plan

    audit = by_name["Audit"]["authority"].lower()
    assert "immutable" in audit or "append-only" in audit


def test_render_iterates_the_journey_stages():
    # render() must actually show the map, not just define the constant.
    assert "JOURNEY_STAGES" in APP_SOURCE
    assert "The v4 remediation journey" in APP_SOURCE


def test_app_v4_imports_only_the_expected_engine_modules_so_far():
    # Labs 2-4 wired in remediation_templates, proposal_hash, approval,
    # verifier, and github_plan. The SQLite audit trail and the
    # v4_service orchestrator are Day 10 and must NOT be imported yet.
    for forbidden in ("v4_service", "audit_db"):
        assert f"import {forbidden}" not in APP_SOURCE


# --- Day 9 Lab 2: build_ui_proposal + the proposal controls ---------------

PROPOSAL_KEYS = {"proposal", "proposal_sha256", "source_sha256"}
HEX64 = "^[0-9a-f]{64}$"


def _env():
    """A small synthetic environment with the three template scenarios."""
    return {
        "environment_name": "UI Proposal Test",
        "source_system": "synthetic",
        "agents": [
            {
                "agent_name": "Ownerless Agent",
                "owner": "",
                "identity": "a1",
                "tools": ["read_ticket"],
                "sensitive_data_access": False,
                "human_approval_required": False,
            },
            {
                "agent_name": "Broad Agent",
                "owner": "Ops",
                "identity": "a2",
                "tools": ["*", "admin_reset", "read_log"],
                "sensitive_data_access": False,
                "human_approval_required": False,
            },
        ],
    }


def test_load_environment_returns_the_connected_demo_inventory():
    env = app_v4.load_environment()
    assert isinstance(env, dict)
    assert isinstance(env["agents"], list) and env["agents"]
    assert all(isinstance(a, dict) and "agent_name" in a for a in env["agents"])


def test_require_human_approval_proposal_shape_and_hashes():
    import re

    built = app_v4.build_ui_proposal(_env(), "Ownerless Agent", "REQUIRE_HUMAN_APPROVAL")
    assert set(built) == PROPOSAL_KEYS
    assert built["proposal"]["template_id"] == "REQUIRE_HUMAN_APPROVAL"
    assert built["proposal"]["agent_name"] == "Ownerless Agent"
    assert built["proposal"]["field_changes"] == {"human_approval_required": True}
    assert re.match(HEX64, built["proposal_sha256"])
    assert re.match(HEX64, built["source_sha256"])


def test_assign_owner_uses_the_validated_owner_value():
    built = app_v4.build_ui_proposal(
        _env(), "Ownerless Agent", "ASSIGN_OWNER", owner_value="  Security Operations  "
    )
    assert built["proposal"]["field_changes"] == {"owner": "Security Operations"}


@pytest.mark.parametrize("bad_owner", ["", "   ", "x" * 201, "line one\nline two"])
def test_assign_owner_rejects_a_malformed_owner_value(bad_owner):
    with pytest.raises(ValueError):
        app_v4.build_ui_proposal(_env(), "Ownerless Agent", "ASSIGN_OWNER", owner_value=bad_owner)


def test_an_unallowlisted_template_is_refused_before_touching_an_agent():
    with pytest.raises(ValueError, match="not allowlisted"):
        app_v4.build_ui_proposal(_env(), "Ownerless Agent", "DELETE_EVERYTHING")


@pytest.mark.parametrize("missing", ["No Such Agent", ""])
def test_an_agent_name_that_matches_zero_agents_is_refused(missing):
    with pytest.raises(ValueError, match="exactly one agent"):
        app_v4.build_ui_proposal(_env(), missing, "REQUIRE_HUMAN_APPROVAL")


def test_remove_broad_admin_tool_filters_the_tool_list():
    built = app_v4.build_ui_proposal(_env(), "Broad Agent", "REMOVE_BROAD_ADMIN_TOOL")
    assert built["proposal"]["field_changes"] == {"tools": ["read_log"]}


def test_remove_broad_admin_tool_refuses_an_agent_with_nothing_broad_to_remove():
    with pytest.raises(ValueError):
        app_v4.build_ui_proposal(_env(), "Ownerless Agent", "REMOVE_BROAD_ADMIN_TOOL")


def test_build_ui_proposal_is_deterministic():
    a = app_v4.build_ui_proposal(_env(), "Ownerless Agent", "REQUIRE_HUMAN_APPROVAL")
    b = app_v4.build_ui_proposal(_env(), "Ownerless Agent", "REQUIRE_HUMAN_APPROVAL")
    assert a == b


def test_build_ui_proposal_describes_and_does_not_apply():
    env = _env()
    before = json.loads(json.dumps(env))
    app_v4.build_ui_proposal(env, "Ownerless Agent", "REQUIRE_HUMAN_APPROVAL")
    assert env == before  # the source inventory is untouched


def test_render_still_references_the_proposal_controls():
    assert "build_ui_proposal" in APP_SOURCE
    assert "Build proposal" in APP_SOURCE
    assert "st.selectbox" in APP_SOURCE


# --- Day 9 Lab 3: approve_and_verify + the evidence display ---------------

RUN_KEYS = {
    "workflow_id", "proposal", "proposal_sha256", "source_sha256",
    "approval", "approval_current", "verification", "verification_summary",
    "final_state", "events",
}


def _env_already_approved():
    """Like _env() but the target agent already requires human approval,
    so REQUIRE_HUMAN_APPROVAL is a no-op and verification must fail."""
    env = _env()
    env["agents"][0]["human_approval_required"] = True
    return env


def test_proposal_from_selection_returns_the_object_and_the_source_hash():
    proposal, source_hash = app_v4._proposal_from_selection(
        _env(), "Ownerless Agent", "REQUIRE_HUMAN_APPROVAL"
    )
    assert isinstance(proposal, RemediationProposal)
    import re

    assert re.match("^[0-9a-f]{64}$", source_hash)


def test_approve_and_verify_happy_path_exposes_all_the_evidence():
    run = app_v4.approve_and_verify(
        _env(), "Ownerless Agent", "REQUIRE_HUMAN_APPROVAL", "Dana", "looks right", "APPROVE"
    )
    assert set(run) == RUN_KEYS

    # the approval is visibly bound to the exact hashes shown
    assert run["approval"]["decision"] == "APPROVE"
    assert run["approval"]["reviewer"] == "Dana"
    assert run["approval"]["proposal_sha256"] == run["proposal_sha256"]
    assert run["approval"]["source_sha256"] == run["source_sha256"]
    assert run["approval_current"] is True

    assert run["verification"]["passed"] is True
    assert "PASSED" in run["verification_summary"]
    assert run["final_state"] == "VERIFIED"
    assert [e["state"] for e in run["events"]] == ["PROPOSED", "APPROVED", "VERIFIED"]


def test_reject_records_the_decision_and_skips_verification():
    run = app_v4.approve_and_verify(
        _env(), "Ownerless Agent", "REQUIRE_HUMAN_APPROVAL", "Dana", "tool list too broad", "REJECT"
    )
    assert run["approval"]["decision"] == "REJECT"
    assert run["verification"] is None
    assert run["verification_summary"] is None
    assert run["final_state"] == "REJECTED"
    assert [e["state"] for e in run["events"]] == ["PROPOSED", "REJECTED"]


def test_a_failed_verification_is_reported_not_raised():
    run = app_v4.approve_and_verify(
        _env_already_approved(), "Ownerless Agent", "REQUIRE_HUMAN_APPROVAL", "Dana", "x", "APPROVE"
    )
    assert run["verification"]["passed"] is False
    assert run["final_state"] == "FAILED"
    last = run["events"][-1]
    assert last["name"] == "verification_failed"
    assert last["state"] == "FAILED"
    assert last["detail"]["failed_checks"]  # names the check that failed


@pytest.mark.parametrize("bad_decision", ["approve", "Approve", " APPROVE ", "MAYBE", ""])
def test_a_decision_that_is_not_exactly_approve_or_reject_raises(bad_decision):
    with pytest.raises(ValueError):
        app_v4.approve_and_verify(
            _env(), "Ownerless Agent", "REQUIRE_HUMAN_APPROVAL", "Dana", "reason", bad_decision
        )


@pytest.mark.parametrize("blank", ["", "   "])
def test_a_blank_reviewer_or_reason_raises(blank):
    with pytest.raises(ValueError):
        app_v4.approve_and_verify(
            _env(), "Ownerless Agent", "REQUIRE_HUMAN_APPROVAL", blank, "reason", "APPROVE"
        )
    with pytest.raises(ValueError):
        app_v4.approve_and_verify(
            _env(), "Ownerless Agent", "REQUIRE_HUMAN_APPROVAL", "Dana", blank, "APPROVE"
        )


def test_bad_selection_input_raises_before_any_decision():
    with pytest.raises(ValueError, match="not allowlisted"):
        app_v4.approve_and_verify(_env(), "Ownerless Agent", "NOPE", "Dana", "r", "APPROVE")
    with pytest.raises(ValueError, match="exactly one agent"):
        app_v4.approve_and_verify(_env(), "Ghost", "REQUIRE_HUMAN_APPROVAL", "Dana", "r", "APPROVE")
    with pytest.raises(ValueError):
        app_v4.approve_and_verify(
            _env(), "Ownerless Agent", "ASSIGN_OWNER", "Dana", "r", "APPROVE", owner_value=""
        )


def test_approve_and_verify_does_not_mutate_the_environment():
    env = _env()
    before = json.loads(json.dumps(env))
    app_v4.approve_and_verify(env, "Ownerless Agent", "REQUIRE_HUMAN_APPROVAL", "Dana", "r", "APPROVE")
    assert env == before


def test_each_run_gets_a_fresh_workflow_id_but_stable_hashes():
    a = app_v4.approve_and_verify(_env(), "Ownerless Agent", "REQUIRE_HUMAN_APPROVAL", "Dana", "r", "APPROVE")
    b = app_v4.approve_and_verify(_env(), "Ownerless Agent", "REQUIRE_HUMAN_APPROVAL", "Dana", "r", "APPROVE")
    assert a["workflow_id"] != b["workflow_id"]
    assert a["proposal_sha256"] == b["proposal_sha256"]
    assert a["source_sha256"] == b["source_sha256"]


def test_render_references_the_evidence_display():
    for marker in ("approve_and_verify", "Approve & verify", "Content hashes", "Event timeline"):
        assert marker in APP_SOURCE


# --- Day 9 Lab 4: github_dry_run_plan + the safety warnings ---------------

PLAN_KEYS = {"repository", "branch", "file_path", "title", "commands", "dry_run", "warnings"}
FORBIDDEN_PLAN_TOKENS = {
    "merge", "--merge", "rebase", "--auto", "--force", "-f", "reset", "--hard",
    "-w", "--web", "ready",
}
WF = "abc123def456"


def test_safety_warnings_are_a_nonempty_tuple_of_strings():
    warnings = app_v4.GITHUB_SAFETY_WARNINGS
    assert isinstance(warnings, tuple) and warnings
    assert all(isinstance(w, str) and w.strip() for w in warnings)
    joined = " ".join(warnings).lower()
    assert "dry run" in joined
    assert "draft" in joined
    assert "never a production" in joined
    # live execution is framed as a separate opt-in, not something the page offers
    assert "separate" in joined and "opt-in" in joined


def test_github_dry_run_plan_shape_and_target():
    plan = app_v4.github_dry_run_plan(WF)
    assert set(plan) == PLAN_KEYS
    assert plan["repository"] == app_v4.DEMO_REPO
    assert plan["branch"] == f"agentguard/{WF}"
    assert plan["file_path"] == "connected_environment/agents.json"
    assert plan["warnings"] is app_v4.GITHUB_SAFETY_WARNINGS


def test_the_plan_is_exactly_five_commands_ending_in_a_draft_pr():
    commands = app_v4.github_dry_run_plan(WF)["commands"]
    assert len(commands) == 5
    assert commands[0] == ["git", "checkout", "-b", f"agentguard/{WF}"]
    assert commands[-1][:3] == ["gh", "pr", "create"]
    assert "--draft" in commands[-1]


def test_no_plan_command_contains_a_forbidden_token():
    commands = app_v4.github_dry_run_plan(WF)["commands"]
    flat = [token for command in commands for token in command]
    assert FORBIDDEN_PLAN_TOKENS.isdisjoint(flat)
    # exactly one gh command, exactly one git push, targeting the agentguard branch
    assert sum(1 for c in commands if c[0] == "gh") == 1
    pushes = [c for c in commands if c[:2] == ["git", "push"]]
    assert len(pushes) == 1
    assert pushes[0][-1] == f"agentguard/{WF}"
    assert pushes[0][-1] not in {"main", "master", "HEAD"}


def test_the_dry_run_marks_every_command_dry_run():
    dry = app_v4.github_dry_run_plan(WF)["dry_run"]
    assert len(dry) == 5
    assert all(row["status"] == "DRY_RUN" for row in dry)


def test_github_dry_run_plan_never_shells_out(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("github_dry_run_plan must not call subprocess")

    monkeypatch.setattr(github_plan.subprocess, "run", boom)
    plan = app_v4.github_dry_run_plan(WF)  # must not raise
    assert len(plan["commands"]) == 5


@pytest.mark.parametrize("bad_id", ["wf 1", "wf/1", "x" * 70, "", "wf$(x)"])
def test_a_non_branch_safe_workflow_id_is_refused(bad_id):
    # (an all-caps id is fine - branch_name() lower-cases it before the check)
    with pytest.raises(ValueError):
        app_v4.github_dry_run_plan(bad_id)


def test_a_verified_run_feeds_straight_into_a_plan():
    run = app_v4.approve_and_verify(
        _env(), "Ownerless Agent", "REQUIRE_HUMAN_APPROVAL", "Dana", "ok", "APPROVE"
    )
    assert run["final_state"] == "VERIFIED"
    plan = app_v4.github_dry_run_plan(run["workflow_id"])
    assert plan["branch"] == f"agentguard/{run['workflow_id']}"


def test_render_gates_the_plan_on_verified_and_has_no_live_execution():
    assert "github_dry_run_plan" in APP_SOURCE
    assert "GITHUB_SAFETY_WARNINGS" in APP_SOURCE
    assert "GitHub dry-run plan" in APP_SOURCE
    assert 'run["final_state"] == "VERIFIED"' in APP_SOURCE
    # the page never runs a live GitHub action
    assert "live=True" not in APP_SOURCE.replace(" ", "")
    assert "execute_plan(plan,live=True)" not in APP_SOURCE.replace(" ", "")


# --- Day 10 Lab 2: the full scenario on the real connected inventory ------
#
# Every end-to-end test above uses the tiny hand-written _env() fixture.
# This one walks the *actual* connected_environment/agents.json - the
# inventory the browser page loads - through the whole chain, so the
# scenario a user clicks through ("a finding becomes a verified proposal
# and a dry-run plan") is pinned exactly once against real data.


def test_full_scenario_finding_to_verified_proposal_to_dry_run_plan():
    # 1. Discovery: the real synthetic inventory. Two agents scan HIGH -
    #    "Customer Support Agent" (destructive tool + sensitive data, no
    #    human gate) and "Deployment Agent".
    env = app_v4.load_environment()
    unchanged = json.loads(json.dumps(env))

    # 2-4. Proposal -> human APPROVE -> verification, in one call.
    run = app_v4.approve_and_verify(
        env,
        "Customer Support Agent",
        "REQUIRE_HUMAN_APPROVAL",
        "Priya Nair",
        "Destructive tool and sensitive-data access with no human gate; require approval.",
        "APPROVE",
    )
    assert set(run) == RUN_KEYS

    # the proposal is the one bounded field change the template allows
    assert run["proposal"]["field_changes"] == {"human_approval_required": True}

    # the approval is visibly bound to the exact hashes the page shows
    assert run["approval"]["decision"] == "APPROVE"
    assert run["approval"]["reviewer"] == "Priya Nair"
    assert run["approval"]["proposal_sha256"] == run["proposal_sha256"]
    assert run["approval"]["source_sha256"] == run["source_sha256"]
    assert run["approval_current"] is True

    # verification ran on an isolated copy and the finding really dropped:
    # 2 HIGH-risk agents before, 1 after (Deployment Agent is untouched).
    assert run["verification"]["passed"] is True
    assert run["verification"]["before_high_count"] == 2
    assert run["verification"]["after_high_count"] == 1
    assert "PASSED" in run["verification_summary"]

    assert run["final_state"] == "VERIFIED"
    assert [e["state"] for e in run["events"]] == ["PROPOSED", "APPROVED", "VERIFIED"]

    # 5. Plan: the verified run feeds straight into a dry-run draft-PR plan.
    plan = app_v4.github_dry_run_plan(run["workflow_id"])
    assert set(plan) == PLAN_KEYS
    assert plan["repository"] == app_v4.DEMO_REPO
    assert plan["branch"] == f"agentguard/{run['workflow_id']}"
    assert plan["file_path"] == "connected_environment/agents.json"
    assert len(plan["commands"]) == 5
    assert plan["commands"][0] == ["git", "checkout", "-b", f"agentguard/{run['workflow_id']}"]
    assert plan["commands"][-1][:3] == ["gh", "pr", "create"]
    assert "--draft" in plan["commands"][-1]
    assert [row["status"] for row in plan["dry_run"]] == ["DRY_RUN"] * 5

    # nothing in the whole scenario mutated the source inventory
    assert env == unchanged
