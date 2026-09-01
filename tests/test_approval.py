"""Tests for approval.py - the ApprovalRecord audit-evidence contract.

Covers: decide() input validation, the 7-field record shape (Day 4 Lab 5
adds workflow_id + decided_at), validate_approval() exact-match and
stale-approval rejection, and an end-to-end REQUIRE_HUMAN_APPROVAL flow
(build a proposal -> hash it -> approve -> validate).
"""

from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from approval import ApprovalRecord, approval_is_current, decide, validate_approval
from proposal_hash import sha256_value
from remediation_templates import apply_proposal_to_environment, build_proposal

ENV = {
    "environment_name": "E",
    "agents": [
        {
            "agent_name": "Customer Support Agent",
            "owner": "",
            "identity": "support-agent-prod",
            "tools": ["read_ticket", "send_email", "delete_customer_record"],
            "sensitive_data_access": True,
            "human_approval_required": False,
        }
    ],
}
AGENT = ENV["agents"][0]


# --- decide() -------------------------------------------------------------

def test_decide_records_who_and_why():
    record = decide("wf-1", "p", "s", "  Justin  ", "APPROVE", "  Reviewed the diff  ")
    assert isinstance(record, ApprovalRecord)
    assert record.reviewer == "Justin"          # stripped
    assert record.reason == "Reviewed the diff"  # stripped
    assert record.decision == "APPROVE"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"decision": "approve"},          # wrong case
        {"decision": "MAYBE"},            # not a valid decision
        {"reviewer": "   "},              # blank reviewer
        {"reason": ""},                   # blank reason
    ],
)
def test_decide_rejects_incomplete_decisions(kwargs):
    base = {"workflow_id": "wf-1", "proposal_sha256": "p", "source_sha256": "s",
            "reviewer": "Justin", "decision": "APPROVE", "reason": "Reviewed"}
    base.update(kwargs)
    with pytest.raises(ValueError):
        decide(**base)


# --- the audit-evidence contract (Day 4 Lab 5) ---------------------------------

def test_record_carries_all_seven_evidence_fields():
    record = decide("wf-42", "p", "s", "Justin", "APPROVE", "Reviewed")
    assert set(record.to_dict()) == {
        "workflow_id", "proposal_sha256", "source_sha256",
        "reviewer", "decision", "reason", "decided_at",
    }


def test_workflow_id_is_stored_verbatim():
    record = decide("run-2026-08-29-abc", "p", "s", "Justin", "APPROVE", "Reviewed")
    assert record.workflow_id == "run-2026-08-29-abc"


def test_decided_at_is_a_utc_iso_timestamp():
    record = decide("wf-1", "p", "s", "Justin", "APPROVE", "Reviewed")
    when = datetime.fromisoformat(record.decided_at)  # raises if not ISO-8601
    assert when.tzinfo is not None                    # timezone-aware
    assert when.utcoffset().total_seconds() == 0      # UTC


def test_an_approval_record_is_frozen():
    record = decide("wf-1", "p", "s", "Justin", "APPROVE", "Reviewed")
    with pytest.raises(FrozenInstanceError):
        record.decision = "REJECT"


# --- validate_approval() ------------------------------------------------------

def test_exact_approval_passes():
    record = decide("wf-1", "p", "s", "Justin", "APPROVE", "Reviewed")
    validate_approval(record, "p", "s")  # no exception


def test_a_reject_decision_is_not_an_approval():
    record = decide("wf-1", "p", "s", "Justin", "REJECT", "Not convinced")
    with pytest.raises(ValueError, match="not approved"):
        validate_approval(record, "p", "s")


def test_a_changed_proposal_makes_the_approval_stale():
    record = decide("wf-1", "p", "s", "Justin", "APPROVE", "Reviewed")
    with pytest.raises(ValueError, match="proposal changed"):
        validate_approval(record, "p-different", "s")


def test_a_changed_source_makes_the_approval_stale():
    record = decide("wf-1", "p", "s", "Justin", "APPROVE", "Reviewed")
    with pytest.raises(ValueError, match="source changed"):
        validate_approval(record, "p", "s-different")


def test_workflow_id_and_decided_at_are_not_part_of_the_match():
    # Two APPROVE records for the same proposal + source but different run
    # ids / timestamps both validate - the new fields are audit metadata.
    first = decide("wf-1", "p", "s", "Justin", "APPROVE", "Reviewed")
    second = decide("wf-2", "p", "s", "Dana", "APPROVE", "Reviewed again")
    validate_approval(first, "p", "s")
    validate_approval(second, "p", "s")
    assert first.workflow_id != second.workflow_id


# --- end to end: REQUIRE_HUMAN_APPROVAL --------------------------------------

def test_require_human_approval_proposal_can_be_approved_and_validated():
    source_hash = sha256_value(ENV)
    proposal = build_proposal("REQUIRE_HUMAN_APPROVAL", AGENT, source_hash)
    assert proposal.field_changes == {"human_approval_required": True}

    proposal_hash = sha256_value(proposal.to_dict())
    record = decide("wf-1", proposal_hash, source_hash, "Justin", "APPROVE", "Reviewed the one-field change")
    validate_approval(record, proposal_hash, source_hash)  # passes


def test_approval_does_not_carry_over_to_a_changed_environment():
    source_hash = sha256_value(ENV)
    proposal = build_proposal("REQUIRE_HUMAN_APPROVAL", AGENT, source_hash)
    proposal_hash = sha256_value(proposal.to_dict())
    record = decide("wf-1", proposal_hash, source_hash, "Justin", "APPROVE", "Reviewed")

    changed_env = {**ENV, "environment_name": "E2"}
    with pytest.raises(ValueError, match="source changed"):
        validate_approval(record, proposal_hash, sha256_value(changed_env))


# --- Day 4 Lab 6: the product records an explicit human choice ----------------
#
# "Approve" and "reject" are the two branches of one entry point, decide().
# The choice is never assumed: a missing, blank, or misspelled decision is
# refused, and a REJECT is stored as full evidence - same shape as an
# APPROVE, with who / why / when - not treated as an empty result.

APPROVE_KEYS = set(
    decide("wf-a", "p", "s", "Justin", "APPROVE", "Reviewed").to_dict()
)


def test_a_reject_is_recorded_as_full_evidence():
    record = decide("wf-9", "p", "s", "Dana", "REJECT", "Tool list still too broad")
    assert record.decision == "REJECT"
    assert record.reviewer == "Dana"
    assert record.reason == "Tool list still too broad"
    assert record.workflow_id == "wf-9"
    assert record.decided_at                       # populated, not blank
    assert set(record.to_dict()) == APPROVE_KEYS   # identical shape to an approval


def test_reject_also_requires_a_reason():
    with pytest.raises(ValueError, match="reviewer and reason are required"):
        decide("wf-9", "p", "s", "Dana", "REJECT", "   ")


@pytest.mark.parametrize("bad_decision", ["", "PENDING", "approve", "Approve", " APPROVE ", "YES", "NO", "rejected"])
def test_the_decision_must_be_spelled_exactly(bad_decision):
    # The product never guesses what a mistyped or empty choice meant.
    with pytest.raises(ValueError, match="decision must be APPROVE or REJECT"):
        decide("wf-9", "p", "s", "Dana", bad_decision, "A reason")


def test_approve_and_reject_records_have_the_same_shape():
    approved = decide("wf-1", "p", "s", "Justin", "APPROVE", "Looks right")
    rejected = decide("wf-1", "p", "s", "Justin", "REJECT", "Not yet")
    assert approved.to_dict().keys() == rejected.to_dict().keys()
    # Only the human's decision and reason differ.
    differing = {k for k in approved.to_dict() if approved.to_dict()[k] != rejected.to_dict()[k]}
    assert differing <= {"decision", "reason", "decided_at"}


# --- Day 4 Lab 7: stale approval is blocked automatically --------------------
#
# validate_approval() is the enforcement point. It runs right before a
# change would be applied and re-checks the two fingerprints the approval
# was bound to. If the proposal or the environment drifted since sign-off,
# it raises - no human has to notice.

TWO_AGENT_ENV = {
    "environment_name": "Drift Demo",
    "agents": [
        {
            "agent_name": "Customer Support Agent",
            "owner": "",
            "tools": ["read_ticket", "send_email", "delete_customer_record"],
            "sensitive_data_access": True,
            "human_approval_required": False,
        },
        {
            "agent_name": "Deployment Agent",
            "owner": "Platform Engineering",
            "tools": ["read_repository", "deploy_production"],
            "sensitive_data_access": True,
            "human_approval_required": False,
        },
    ],
}


def _approve_support_agent_change():
    """Return (record, proposal_hash, source_hash) for an APPROVED proposal
    that turns on human approval for the support agent."""
    env = {k: (v if k != "agents" else [dict(a) for a in v]) for k, v in TWO_AGENT_ENV.items()}
    source_hash = sha256_value(env)
    proposal = build_proposal("REQUIRE_HUMAN_APPROVAL", env["agents"][0], source_hash)
    proposal_hash = sha256_value(proposal.to_dict())
    record = decide("wf-1", proposal_hash, source_hash, "Justin", "APPROVE", "Reviewed the one-field change")
    return record, proposal_hash, source_hash


def test_source_drift_after_approval_is_rejected_automatically():
    record, proposal_hash, _ = _approve_support_agent_change()

    # Someone widens the deployment agent's tools after sign-off.
    drifted = {k: (v if k != "agents" else [dict(a) for a in v]) for k, v in TWO_AGENT_ENV.items()}
    drifted["agents"][1]["tools"] = drifted["agents"][1]["tools"] + ["admin_override"]

    with pytest.raises(ValueError, match="source changed"):
        validate_approval(record, proposal_hash, sha256_value(drifted))


def test_proposal_drift_after_approval_is_rejected_automatically():
    record, _, source_hash = _approve_support_agent_change()

    # A proposal is regenerated, this time targeting a different agent.
    other = build_proposal("REQUIRE_HUMAN_APPROVAL", TWO_AGENT_ENV["agents"][1], source_hash)
    with pytest.raises(ValueError, match="proposal changed"):
        validate_approval(record, sha256_value(other.to_dict()), source_hash)


def test_when_both_drift_the_proposal_is_reported_first():
    record, _, _ = _approve_support_agent_change()
    with pytest.raises(ValueError, match="proposal changed"):
        validate_approval(record, "different-proposal", "different-source")


def test_a_deterministic_rebuild_is_not_treated_as_drift():
    record, approved_hash, source_hash = _approve_support_agent_change()

    # Rebuild the identical proposal from the same untouched inputs.
    rebuilt = build_proposal("REQUIRE_HUMAN_APPROVAL", TWO_AGENT_ENV["agents"][0], source_hash)
    rebuilt_hash = sha256_value(rebuilt.to_dict())

    assert rebuilt_hash == approved_hash
    validate_approval(record, rebuilt_hash, source_hash)  # no exception - not stale


def test_validate_approval_is_a_guard_returning_none_on_success():
    record, proposal_hash, source_hash = _approve_support_agent_change()
    assert validate_approval(record, proposal_hash, source_hash) is None


# --- Day 4 Lab 8: an approval cannot be replayed -----------------------------
#
# An ApprovalRecord is a one-time authorization: valid for exactly one
# (decision == APPROVE, proposal hash, source hash) triple. These negative
# tests prove it cannot be reused for a different proposal, against the
# post-apply world, a second time, or by editing the record.

REPLAY_ENV = {
    "environment_name": "Replay Demo",
    "agents": [
        {
            "agent_name": "Customer Support Agent",
            "owner": "",
            "tools": ["read_ticket", "send_email", "delete_customer_record"],
            "sensitive_data_access": True,
            "human_approval_required": False,
        }
    ],
}


def _fresh_env():
    return {k: (v if k != "agents" else [dict(a) for a in v]) for k, v in REPLAY_ENV.items()}


def _approve():
    """Approve a REQUIRE_HUMAN_APPROVAL proposal for the support agent.
    Returns (record, proposal, proposal_hash, source_hash, env)."""
    env = _fresh_env()
    source_hash = sha256_value(env)
    proposal = build_proposal("REQUIRE_HUMAN_APPROVAL", env["agents"][0], source_hash)
    proposal_hash = sha256_value(proposal.to_dict())
    record = decide("wf-1", proposal_hash, source_hash, "Justin", "APPROVE", "Reviewed")
    return record, proposal, proposal_hash, source_hash, env


@pytest.mark.parametrize(
    "use_real_proposal, use_real_source, should_pass",
    [
        (True, True, True),     # the one exact match
        (False, True, False),   # proposal hash perturbed
        (True, False, False),   # source hash perturbed
        (False, False, False),  # both perturbed
    ],
)
def test_only_the_exact_triple_validates(use_real_proposal, use_real_source, should_pass):
    record, _, proposal_hash, source_hash, _ = _approve()
    p = proposal_hash if use_real_proposal else proposal_hash[:-1] + "0"
    s = source_hash if use_real_source else source_hash[:-1] + "0"
    if should_pass:
        assert validate_approval(record, p, s) is None
    else:
        with pytest.raises(ValueError):
            validate_approval(record, p, s)


def test_a_reject_token_never_validates_even_with_correct_hashes():
    _, _, proposal_hash, source_hash, _ = _approve()
    rejected = decide("wf-1", proposal_hash, source_hash, "Dana", "REJECT", "Too broad")
    with pytest.raises(ValueError, match="not approved"):
        validate_approval(rejected, proposal_hash, source_hash)


def test_an_approval_cannot_be_replayed_for_a_different_proposal():
    record, _, _, source_hash, env = _approve()
    # A different proposal built against the same environment (owner assign).
    other = build_proposal("ASSIGN_OWNER", env["agents"][0], source_hash, value="Support Lead")
    with pytest.raises(ValueError, match="proposal changed"):
        validate_approval(record, sha256_value(other.to_dict()), source_hash)


def test_an_approval_is_spent_once_the_change_is_applied():
    record, proposal, proposal_hash, source_hash, env = _approve()

    # Valid at apply time.
    validate_approval(record, proposal_hash, source_hash)

    # Apply it -> the world is now in the post-state.
    applied = apply_proposal_to_environment(env, proposal)
    assert applied["agents"][0]["human_approval_required"] is True

    # The same approval cannot be replayed against the post-apply world...
    with pytest.raises(ValueError, match="source changed"):
        validate_approval(record, proposal_hash, sha256_value(applied))

    # ...nor reused to apply a second time.
    with pytest.raises(ValueError, match="source changed"):
        validate_approval(record, proposal_hash, sha256_value(applied))


def test_a_stale_approval_cannot_be_repaired_by_editing_the_record():
    record, _, _, source_hash, _ = _approve()
    with pytest.raises(FrozenInstanceError):
        record.proposal_sha256 = "forged"
    # A fresh valid record can only come from decide(), which demands a
    # reviewer and reason and stamps its own timestamp.
    with pytest.raises(ValueError):
        decide("wf-1", "p", source_hash, "", "APPROVE", "")


# --- Day 8 Lab 6: approval_is_current - the non-raising freshness check ------
#
# validate_approval() enforces freshness (raises); approval_is_current()
# reports it (returns a bool), so a caller can branch or render a "re-review
# needed" banner without a try/except. The two are always consistent because
# approval_is_current() is defined in terms of validate_approval().


def test_approval_is_current_is_true_for_the_exact_triple():
    record, _, proposal_hash, source_hash, _ = _approve()
    assert approval_is_current(record, proposal_hash, source_hash) is True


@pytest.mark.parametrize(
    "perturb_proposal, perturb_source",
    [(True, False), (False, True), (True, True)],
)
def test_approval_is_current_is_false_when_either_hash_drifts(perturb_proposal, perturb_source):
    record, _, proposal_hash, source_hash, _ = _approve()
    p = proposal_hash[:-1] + "0" if perturb_proposal else proposal_hash
    s = source_hash[:-1] + "0" if perturb_source else source_hash
    assert approval_is_current(record, p, s) is False


def test_approval_is_current_is_false_for_a_reject_record():
    _, _, proposal_hash, source_hash, _ = _approve()
    rejected = decide("wf-1", proposal_hash, source_hash, "Dana", "REJECT", "Too broad")
    assert approval_is_current(rejected, proposal_hash, source_hash) is False


def test_a_deterministic_rebuild_is_still_current():
    record, approved_hash, source_hash = _approve_support_agent_change()
    rebuilt = build_proposal(
        "REQUIRE_HUMAN_APPROVAL", TWO_AGENT_ENV["agents"][0], source_hash
    )
    assert sha256_value(rebuilt.to_dict()) == approved_hash
    assert approval_is_current(record, approved_hash, source_hash) is True


@pytest.mark.parametrize("decision", ["APPROVE", "REJECT"])
@pytest.mark.parametrize("real_proposal", [True, False])
@pytest.mark.parametrize("real_source", [True, False])
def test_approval_is_current_agrees_with_validate_approval(decision, real_proposal, real_source):
    _, _, proposal_hash, source_hash, _ = _approve()
    record = decide("wf-1", proposal_hash, source_hash, "Justin", decision, "Reviewed")
    p = proposal_hash if real_proposal else proposal_hash[:-1] + "0"
    s = source_hash if real_source else source_hash[:-1] + "0"

    try:
        validate_approval(record, p, s)
        raised = False
    except ValueError:
        raised = True

    assert approval_is_current(record, p, s) is (not raised)
