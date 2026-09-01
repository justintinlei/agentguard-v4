"""Tests for verifier.py - Day 6 Labs 2-3.

Lab 2: `isolated_candidate_file` does its work in a system temp directory
and deletes it on exit.
Lab 3: the candidate is the environment with the proposal applied, built
by a deep copy - the source and every non-target agent are untouched, and
the proposal is applied in exactly one place.
"""

import copy
import json
import tempfile
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from github_plan import GitHubPlan, create_plan
from proposal_hash import sha256_value
from remediation_templates import RemediationProposal, build_proposal
from verifier import (
    VerificationResult,
    isolated_candidate_file,
    require_verified,
    rescan_before_and_after,
    scan_high_count,
    structural_checks,
    target_and_key_checks,
    verify,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

ENV = {
    "environment_name": "Verify Demo",
    "source_system": "synthetic-agent-registry",
    "agents": [
        {
            "agent_name": "Customer Support Agent",
            "owner": "",
            "identity": "support-agent-prod",
            "tools": ["read_ticket", "send_email", "delete_customer_record"],
            "sensitive_data_access": True,
            "human_approval_required": False,
        },
        {
            "agent_name": "Research Agent",
            "owner": "Product Research",
            "identity": "research-agent-readonly",
            "tools": ["web_search", "read_public_document"],
            "sensitive_data_access": False,
            "human_approval_required": False,
        },
    ],
}

# Turn on human approval for the FIRST agent.
PROPOSAL = build_proposal("REQUIRE_HUMAN_APPROVAL", ENV["agents"][0], sha256_value(ENV))


def _repo_files() -> set:
    return {p for p in REPO_ROOT.rglob("*") if p.is_file() and ".venv" not in p.parts}


def _leftover_verify_dirs() -> list:
    return list(Path(tempfile.gettempdir()).glob("agentguard-verify-*"))


# --- isolation (Lab 2, adapted) -------------------------------------------

def test_the_candidate_file_is_a_real_file_inside_the_block():
    with isolated_candidate_file(ENV, PROPOSAL) as (candidate, path):
        assert path.is_file()
        assert json.loads(path.read_text(encoding="utf-8")) == candidate


def test_the_temp_directory_is_outside_the_repo():
    with isolated_candidate_file(ENV, PROPOSAL) as (_candidate, path):
        assert str(path).startswith(tempfile.gettempdir())
        assert str(REPO_ROOT) not in str(path)
        assert path.parent.name.startswith("agentguard-verify-")


def test_the_directory_is_deleted_when_the_block_ends():
    with isolated_candidate_file(ENV, PROPOSAL) as (_candidate, path):
        saved = path
    assert not saved.exists()
    assert not saved.parent.exists()


def test_the_directory_is_deleted_even_when_the_block_raises():
    saved = None
    with pytest.raises(RuntimeError):
        with isolated_candidate_file(ENV, PROPOSAL) as (_candidate, path):
            saved = path
            raise RuntimeError("boom")
    assert saved is not None and not saved.exists()


def test_no_file_is_created_anywhere_in_the_repo():
    before = _repo_files()
    with isolated_candidate_file(ENV, PROPOSAL) as (_candidate, path):
        assert path.is_file()
    assert _repo_files() == before


# --- candidate production (Lab 3) ----------------------------------------

def test_the_candidate_has_the_proposal_applied():
    with isolated_candidate_file(ENV, PROPOSAL) as (candidate, path):
        assert candidate["agents"][0]["human_approval_required"] is True
        assert json.loads(path.read_text(encoding="utf-8")) == candidate


def test_the_source_environment_is_not_touched():
    before = json.loads(json.dumps(ENV))
    agents_obj = ENV["agents"]
    with isolated_candidate_file(ENV, PROPOSAL) as (_candidate, _path):
        pass
    assert ENV == before
    assert ENV["agents"][0]["human_approval_required"] is False
    assert ENV["agents"] is agents_obj  # same object, no copy-back


def test_only_the_target_agent_changed():
    with isolated_candidate_file(ENV, PROPOSAL) as (candidate, _path):
        # the non-target agent is byte-identical
        assert candidate["agents"][1] == ENV["agents"][1]
        # the target agent differs only in the one proposed field
        target_before = dict(ENV["agents"][0])
        target_after = dict(candidate["agents"][0])
        assert target_after.pop("human_approval_required") is True
        target_before.pop("human_approval_required")
        assert target_after == target_before


def test_a_proposal_with_no_matching_agent_raises_and_leaves_no_temp_dir():
    orphan = build_proposal(
        "REQUIRE_HUMAN_APPROVAL",
        {"agent_name": "Nonexistent Agent"},
        sha256_value(ENV),
    )
    before = set(_leftover_verify_dirs())
    with pytest.raises(ValueError, match="exactly one agent"):
        with isolated_candidate_file(ENV, orphan) as (_candidate, _path):
            pass
    assert set(_leftover_verify_dirs()) == before


# --- re-scan before and after (Lab 4) ----------------------------------------

def _agent(name, **overrides):
    base = {
        "agent_name": name,
        "owner": "Owning Team",
        "identity": f"{name.lower().replace(' ', '-')}",
        "tools": ["read_document"],
        "sensitive_data_access": False,
        "human_approval_required": False,
    }
    base.update(overrides)
    return base


def test_the_source_has_one_high_risk_agent():
    # Agent 1: destructive tool + sensitive data + no approval -> HIGH.
    assert scan_high_count(ENV) == 1


def test_the_remediated_candidate_has_zero_high_risk_agents():
    with isolated_candidate_file(ENV, PROPOSAL) as (candidate, _path):
        assert scan_high_count(candidate) == 0


def test_rescan_reports_the_before_and_after_counts():
    with isolated_candidate_file(ENV, PROPOSAL) as (candidate, _path):
        result = rescan_before_and_after(ENV, candidate)
    assert result == {
        "before_high_count": 1,
        "after_high_count": 0,
        "high_count_did_not_increase": True,
    }


def test_a_change_that_would_add_a_high_risk_agent_fails_the_check():
    before_env = {"agents": [_agent("A"), _agent("B")]}
    # "after" has an extra HIGH agent (destructive tool, sensitive, no approval)
    after_env = {
        "agents": [
            _agent("A"),
            _agent("B"),
            _agent("C", tools=["delete_records"], sensitive_data_access=True),
        ]
    }
    result = rescan_before_and_after(before_env, after_env)
    assert result["before_high_count"] == 0
    assert result["after_high_count"] == 1
    assert result["high_count_did_not_increase"] is False


def test_a_neutral_change_passes_the_check():
    env = {"agents": [_agent("A"), _agent("B")]}
    result = rescan_before_and_after(env, env)
    assert result["high_count_did_not_increase"] is True


def test_scan_high_count_leaves_no_temp_directory_behind():
    before = set(_leftover_verify_dirs())
    scan_high_count(ENV)
    assert set(_leftover_verify_dirs()) == before


# --- Day 6 Lab 5: structural + serialization checks -------------------------

def _row(rows, name):
    return next(r for r in rows if r["name"] == name)


def test_a_well_formed_candidate_passes_every_structural_check():
    with isolated_candidate_file(ENV, PROPOSAL) as (candidate, _path):
        rows = structural_checks(candidate)
    assert len(rows) == 4
    assert all(set(r) == {"name", "passed"} for r in rows)
    assert all(r["passed"] is True for r in rows)


@pytest.mark.parametrize("not_an_object", [[], None, "candidate", 42])
def test_a_non_object_candidate_fails_the_object_check_without_raising(not_an_object):
    rows = structural_checks(not_an_object)
    assert _row(rows, "candidate is a JSON object")["passed"] is False


def test_a_candidate_with_no_agents_key_fails_the_agents_list_check():
    rows = structural_checks({"environment_name": "E"})
    assert _row(rows, "candidate has an agents list")["passed"] is False


def test_a_candidate_whose_agents_is_not_a_list_fails():
    rows = structural_checks({"agents": {"agent_name": "A"}})
    assert _row(rows, "candidate has an agents list")["passed"] is False


def test_an_incomplete_agent_record_fails_the_completeness_check():
    incomplete = {k: v for k, v in ENV["agents"][0].items() if k != "identity"}
    rows = structural_checks({"agents": [incomplete]})
    assert _row(rows, "candidate has an agents list")["passed"] is True
    assert _row(rows, "every agent record is complete")["passed"] is False


def test_a_non_dict_agent_entry_fails_the_completeness_check():
    rows = structural_checks({"agents": ["not-an-agent"]})
    assert _row(rows, "every agent record is complete")["passed"] is False


def test_a_non_serialisable_candidate_fails_the_round_trip_check_without_raising():
    rows = structural_checks({"agents": [], "leftover": {1, 2, 3}})
    assert _row(rows, "candidate serialises and re-reads unchanged")["passed"] is False


def test_a_candidate_that_changes_on_round_trip_fails():
    rows = structural_checks({"agents": [], 2: "int key becomes a string"})
    assert _row(rows, "candidate serialises and re-reads unchanged")["passed"] is False


# --- Day 6 Lab 6: target-count + allowlisted-key checks --------------------


def _candidate(mutate=None):
    """A well-formed candidate (ENV + PROPOSAL applied); `mutate` may edit it."""
    with isolated_candidate_file(ENV, PROPOSAL) as (candidate, _path):
        candidate = copy.deepcopy(candidate)
    if mutate:
        mutate(candidate)
    return candidate


def test_a_surgical_candidate_passes_every_target_and_key_check():
    candidate = _candidate()
    rows = target_and_key_checks(ENV, candidate, PROPOSAL)
    assert len(rows) == 4
    assert all(set(r) == {"name", "passed"} for r in rows)
    assert all(r["passed"] is True for r in rows)


def test_an_added_agent_fails_count_and_only_target_changed():
    def add(c):
        c["agents"].append(dict(ENV["agents"][1], agent_name="Sneaky Agent"))

    rows = target_and_key_checks(ENV, _candidate(add), PROPOSAL)
    assert _row(rows, "agent count unchanged")["passed"] is False
    assert _row(rows, "only the target agent changed")["passed"] is False


def test_a_removed_agent_fails_the_count_check():
    rows = target_and_key_checks(ENV, _candidate(lambda c: c["agents"].pop()), PROPOSAL)
    assert _row(rows, "agent count unchanged")["passed"] is False


def test_an_extra_top_level_key_fails_the_allowlist_check():
    rows = target_and_key_checks(
        ENV, _candidate(lambda c: c.__setitem__("injected", "x")), PROPOSAL
    )
    assert _row(rows, "only allowlisted top-level keys")["passed"] is False


def test_changing_a_non_target_agent_fails_only_the_target_agent_changed():
    def touch_other(c):
        c["agents"][1]["owner"] = "Reassigned"

    rows = target_and_key_checks(ENV, _candidate(touch_other), PROPOSAL)
    assert _row(rows, "only the target agent changed")["passed"] is False


def test_the_target_name_appearing_twice_fails_the_target_count_check():
    def duplicate(c):
        c["agents"].append(dict(c["agents"][0]))

    rows = target_and_key_checks(ENV, _candidate(duplicate), PROPOSAL)
    assert _row(rows, "proposal targets exactly one agent")["passed"] is False


def test_renaming_the_target_agent_fails_only_the_target_agent_changed():
    def rename(c):
        c["agents"][0]["agent_name"] = "Renamed Agent"

    rows = target_and_key_checks(ENV, _candidate(rename), PROPOSAL)
    assert _row(rows, "proposal targets exactly one agent")["passed"] is False
    assert _row(rows, "only the target agent changed")["passed"] is False


def test_a_no_op_candidate_fails_only_the_target_agent_changed():
    rows = target_and_key_checks(ENV, copy.deepcopy(ENV), PROPOSAL)
    assert _row(rows, "only the target agent changed")["passed"] is False


# --- Day 6 Lab 7: VerificationResult / verify() ----------------------------

EXPECTED_CHECK_NAMES = {
    "candidate is a JSON object",
    "candidate serialises and re-reads unchanged",
    "candidate has an agents list",
    "every agent record is complete",
    "isolated write and reread succeeded",
    "high-risk count did not increase",
    "agent count unchanged",
    "only allowlisted top-level keys",
    "proposal targets exactly one agent",
    "only the target agent changed",
}


def _hand_proposal(agent_name, field_changes):
    return RemediationProposal(
        template_id="REQUIRE_HUMAN_APPROVAL",
        agent_name=agent_name,
        field_changes=field_changes,
        rationale="synthetic verifier failure-path test",
        source_sha256="0" * 64,
    )


def test_verify_of_a_good_proposal_passes_every_check():
    result = verify(ENV, PROPOSAL)
    assert isinstance(result, VerificationResult)
    assert result.passed is True
    assert isinstance(result.checks, tuple)
    assert all(set(c) == {"name", "passed"} for c in result.checks)
    assert all(c["passed"] for c in result.checks)
    assert {c["name"] for c in result.checks} == EXPECTED_CHECK_NAMES


def test_verify_reports_the_before_and_after_high_counts():
    result = verify(ENV, PROPOSAL)
    assert result.before_high_count == 1
    assert result.after_high_count == 0


def test_verify_carries_the_candidate_environment():
    result = verify(ENV, PROPOSAL)
    assert result.candidate_environment["agents"][0]["human_approval_required"] is True


def test_verification_result_is_frozen():
    result = verify(ENV, PROPOSAL)
    with pytest.raises(FrozenInstanceError):
        result.passed = False


def test_to_dict_is_the_audit_form_and_is_json_serialisable():
    result = verify(ENV, PROPOSAL)
    as_dict = result.to_dict()
    assert set(as_dict) == {
        "passed",
        "checks",
        "before_high_count",
        "after_high_count",
        "candidate_environment",
    }
    json.dumps(as_dict)  # must not raise


def test_summary_is_the_display_form():
    result = verify(ENV, PROPOSAL)
    text = result.summary()
    assert "PASSED" in text
    for check in result.checks:
        assert check["name"] in text


def test_a_no_op_proposal_fails_verification():
    no_op = _hand_proposal("Customer Support Agent", {"human_approval_required": False})
    result = verify(ENV, no_op)
    assert result.passed is False
    assert _row(result.checks, "only the target agent changed")["passed"] is False
    assert "FAILED" in result.summary()


def test_a_proposal_that_raises_the_high_risk_count_fails_verification():
    # Research Agent is currently low risk; give it a destructive tool and
    # sensitive-data access with no approval -> it becomes HIGH.
    dangerous = _hand_proposal(
        "Research Agent",
        {"tools": ["delete_dataset"], "sensitive_data_access": True},
    )
    result = verify(ENV, dangerous)
    assert result.passed is False
    assert _row(result.checks, "high-risk count did not increase")["passed"] is False
    assert result.after_high_count > result.before_high_count


# --- Day 6 Lab 8: a proposal cannot advance when any required check fails ----

DANGEROUS = _hand_proposal(
    "Research Agent", {"tools": ["delete_dataset"], "sensitive_data_access": True}
)
NO_OP = _hand_proposal("Customer Support Agent", {"human_approval_required": False})


def test_a_valid_proposal_passes_every_check():
    result = verify(ENV, PROPOSAL)
    assert result.passed is True
    assert len(result.checks) == 10
    assert all(c["passed"] for c in result.checks)
    assert (result.before_high_count, result.after_high_count) == (1, 0)


@pytest.mark.parametrize("proposal", [PROPOSAL, NO_OP, DANGEROUS])
def test_passed_is_exactly_the_and_of_the_check_rows(proposal):
    result = verify(ENV, proposal)
    assert result.passed == all(c["passed"] for c in result.checks)


def test_one_failing_check_is_enough_to_block_verification():
    result = verify(ENV, NO_OP)
    failed = [c["name"] for c in result.checks if not c["passed"]]
    assert failed == ["only the target agent changed"]
    assert result.passed is False


def test_an_extra_top_level_environment_key_blocks_verification():
    result = verify({**ENV, "note": "not allowed here"}, PROPOSAL)
    assert _row(result.checks, "only allowlisted top-level keys")["passed"] is False
    assert result.passed is False


def test_renaming_the_target_through_field_changes_blocks_verification():
    rename = _hand_proposal("Customer Support Agent", {"agent_name": "Renamed Agent"})
    result = verify(ENV, rename)
    assert _row(result.checks, "proposal targets exactly one agent")["passed"] is False
    assert result.passed is False


def test_a_malformed_candidate_is_gated_out_before_the_scan():
    leaky = _hand_proposal("Customer Support Agent", {5: "leaked int key"})
    result = verify(ENV, leaky)
    assert result.passed is False
    assert result.before_high_count is None
    assert result.after_high_count is None
    check_names = {c["name"] for c in result.checks}
    assert "high-risk count did not increase" not in check_names
    assert len(result.checks) <= 5


def test_a_failed_verification_still_names_the_failed_checks():
    result = verify(ENV, DANGEROUS)
    failed = [c["name"] for c in result.checks if not c["passed"]]
    assert failed  # non-empty
    text = result.summary()
    assert "FAILED" in text
    assert any(line.strip().startswith("[ ]") for line in text.splitlines())
    json.dumps(result.to_dict())  # audit form still serialises


def test_verification_does_not_touch_the_source_even_when_it_fails():
    before = copy.deepcopy(ENV)
    agents_obj = ENV["agents"]
    verify(ENV, DANGEROUS)
    assert ENV == before
    assert ENV["agents"] is agents_obj


# --- Day 8 Lab 5: require_verified - the stop-planning gate -----------------
#
# verify() decides pass/fail; require_verified() is the gate a caller must
# clear before building a GitHub plan. A failed VerificationResult raises
# here, so a change that did not verify never reaches create_plan().

DEMO_REPO = "justintinlei/agentguard-remediation-demo"


def test_require_verified_returns_a_passing_result_unchanged():
    result = verify(ENV, PROPOSAL)
    assert result.passed is True
    assert require_verified(result) is result


def test_require_verified_raises_on_a_result_that_raised_the_high_count():
    result = verify(ENV, DANGEROUS)
    assert result.passed is False
    with pytest.raises(ValueError, match="GitHub planning is blocked") as exc:
        require_verified(result)
    assert "high-risk count did not increase" in str(exc.value)


def test_require_verified_raises_on_a_no_op_result():
    result = verify(ENV, NO_OP)
    with pytest.raises(ValueError, match="GitHub planning is blocked") as exc:
        require_verified(result)
    assert "only the target agent changed" in str(exc.value)


def test_the_gate_message_lists_every_failed_check_and_no_passing_one():
    result = VerificationResult(
        passed=False,
        checks=(
            {"name": "check one", "passed": False},
            {"name": "check two", "passed": True},
            {"name": "check three", "passed": False},
        ),
        before_high_count=0,
        after_high_count=0,
        candidate_environment={},
    )
    with pytest.raises(ValueError) as exc:
        require_verified(result)
    message = str(exc.value)
    assert "check one" in message
    assert "check three" in message
    assert "check two" not in message


@pytest.mark.parametrize("not_a_result", ["not a result", None, True, {"passed": True}])
def test_require_verified_rejects_a_non_verificationresult(not_a_result):
    with pytest.raises(TypeError, match="VerificationResult"):
        require_verified(not_a_result)


def _plan_after_verify(environment, proposal, repository, workflow_id):
    """The real order: verify, gate, then (only if the gate passed) plan."""
    require_verified(verify(environment, proposal))
    return create_plan(repository, workflow_id)


def test_a_verified_proposal_reaches_a_github_plan():
    plan = _plan_after_verify(ENV, PROPOSAL, DEMO_REPO, "wf-ok")
    assert isinstance(plan, GitHubPlan)
    assert len(plan.commands) == 5


@pytest.mark.parametrize("bad_proposal", [DANGEROUS, NO_OP])
def test_a_failed_verification_stops_before_create_plan(bad_proposal):
    with pytest.raises(ValueError, match="GitHub planning is blocked"):
        _plan_after_verify(ENV, bad_proposal, DEMO_REPO, "wf-bad")
