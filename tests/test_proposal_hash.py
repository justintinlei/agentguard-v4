"""Tests for proposal_hash.py - Day 4 Lab 2 (canonical JSON + sha256_value).

The property under test: identical structured data always produces an
identical fingerprint, regardless of how the dict was built or spaced;
any change to the content changes the fingerprint.
"""

import pytest

from approval import decide, validate_approval
from proposal_hash import canonical_json, sha256_value
from remediation_templates import RemediationProposal, build_proposal


# --- canonical_json: presentation cannot leak into the bytes ---------------

def test_key_order_does_not_change_canonical_text():
    assert canonical_json({"b": 2, "a": 1}) == canonical_json({"a": 1, "b": 2})


def test_nested_key_order_does_not_change_canonical_text():
    left = {"outer": {"z": 1, "a": 2}, "list": [{"y": 1, "x": 2}]}
    right = {"list": [{"x": 2, "y": 1}], "outer": {"a": 2, "z": 1}}
    assert canonical_json(left) == canonical_json(right)


def test_canonical_text_has_sorted_keys_and_no_incidental_spaces():
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'


def test_canonical_text_escapes_non_ascii():
    # ensure_ascii=True -> the character is written as a fixed \uXXXX escape
    assert canonical_json({"name": "é"}) == '{"name":"\\u00e9"}'


def test_non_json_types_raise_rather_than_being_coerced():
    with pytest.raises(TypeError):
        canonical_json({"when": object()})


# --- sha256_value: the fingerprint ---------------------------------------------

def test_digest_is_64_lowercase_hex_characters():
    digest = sha256_value({"a": 1})
    assert len(digest) == 64
    assert digest == digest.lower()
    int(digest, 16)  # raises ValueError if any char is not hex


def test_same_value_hashed_twice_is_identical():
    assert sha256_value({"a": 1, "b": [1, 2, 3]}) == sha256_value({"a": 1, "b": [1, 2, 3]})


def test_key_order_does_not_change_the_digest():
    assert sha256_value({"b": 2, "a": 1}) == sha256_value({"a": 1, "b": 2})


def test_any_content_change_changes_the_digest():
    assert sha256_value({"approved": False}) != sha256_value({"approved": True})


# --- ties to the real object this exists for ----------------------------------

def test_a_remediation_proposal_hashes_the_same_every_time():
    agent = {
        "agent_name": "Billing Agent",
        "owner": "",
        "tools": ["read_invoice", "issue_refund"],
        "sensitive_data_access": True,
        "human_approval_required": False,
    }
    source_hash = sha256_value({"agents": [agent]})
    first = build_proposal("REQUIRE_HUMAN_APPROVAL", agent, source_hash)
    second = build_proposal("REQUIRE_HUMAN_APPROVAL", agent, source_hash)
    assert sha256_value(first.to_dict()) == sha256_value(second.to_dict())


# --- Day 4 Lab 3: hashing the exact source environment ------------------------
#
# The "source environment" is the whole agent inventory a human reviews:
# every agent, every tool, every flag - and, for the list, in order.
# `sha256_value(environment)` is the fingerprint an approval is bound to.
# These tests prove that fingerprint reacts to *reviewed content* and to
# nothing else, and that binding an approval to it blocks a stale approval.


def _environment(support_approval: bool = False) -> dict:
    """A small synthetic 3-agent inventory in the connected_environment shape."""
    return {
        "environment_name": "Synthetic Demo Environment",
        "source_system": "synthetic-agent-registry",
        "agents": [
            {
                "agent_name": "Customer Support Agent",
                "owner": "",
                "identity": "support-agent-prod",
                "tools": ["read_ticket", "send_email", "delete_customer_record"],
                "sensitive_data_access": True,
                "human_approval_required": support_approval,
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


def test_source_environment_hash_is_stable_across_key_order():
    # Same inventory, keys inserted in a different order in every dict.
    reordered = {
        "agents": [
            {
                "human_approval_required": False,
                "sensitive_data_access": True,
                "tools": ["read_ticket", "send_email", "delete_customer_record"],
                "identity": "support-agent-prod",
                "owner": "",
                "agent_name": "Customer Support Agent",
            },
            {
                "human_approval_required": False,
                "sensitive_data_access": False,
                "tools": ["web_search", "read_public_document"],
                "identity": "research-agent-readonly",
                "owner": "Product Research",
                "agent_name": "Research Agent",
            },
        ],
        "source_system": "synthetic-agent-registry",
        "environment_name": "Synthetic Demo Environment",
    }
    assert sha256_value(_environment()) == sha256_value(reordered)


def test_reordering_the_agents_list_changes_the_hash():
    env = _environment()
    swapped = dict(env)
    swapped["agents"] = list(reversed(env["agents"]))
    # A list is ordered data - "the exact source" includes agent order.
    assert sha256_value(env) != sha256_value(swapped)


def test_changing_one_nested_agent_flag_changes_the_hash():
    assert sha256_value(_environment(support_approval=False)) != sha256_value(
        _environment(support_approval=True)
    )


def test_adding_one_tool_to_one_agent_changes_the_hash():
    env = _environment()
    changed = _environment()
    changed["agents"][1]["tools"] = env["agents"][1]["tools"] + ["download_file"]
    assert sha256_value(env) != sha256_value(changed)


def test_realistic_environment_still_yields_64_lowercase_hex():
    digest = sha256_value(_environment())
    assert len(digest) == 64 and digest == digest.lower()
    int(digest, 16)


def test_source_hash_binds_an_approval_to_the_reviewed_environment():
    env = _environment()
    source_hash = sha256_value(env)
    agent = env["agents"][0]

    proposal = build_proposal("REQUIRE_HUMAN_APPROVAL", agent, source_hash)
    proposal_hash = sha256_value(proposal.to_dict())
    record = decide("wf-1", proposal_hash, source_hash, "Justin", "APPROVE", "Reviewed the inventory")

    # Same environment at apply time -> approval still valid.
    validate_approval(record, proposal_hash, sha256_value(env))

    # Someone turned on approval for the support agent after review.
    moved_env = _environment(support_approval=True)
    with pytest.raises(ValueError, match="source changed"):
        validate_approval(record, proposal_hash, sha256_value(moved_env))


# --- Day 4 Lab 4: hashing the complete remediation proposal -------------------
#
# The proposal hash covers ALL FIVE fields of RemediationProposal, not just
# the diff: intent (template_id), target (agent_name), the field and the
# value inside field_changes, and rationale. Change any one of them and the
# digest changes, so an approval bound to the old digest is refused as
# stale ("proposal changed"). __post_init__ only requires field_changes to
# be a non-empty dict, so these tests can vary exactly one dimension at a
# time.

SOURCE_HASH = sha256_value({"agents": [{"agent_name": "A"}]})


def _proposal(**overrides) -> RemediationProposal:
    """A baseline valid proposal; override one field per test."""
    fields = {
        "template_id": "REQUIRE_HUMAN_APPROVAL",
        "agent_name": "Customer Support Agent",
        "field_changes": {"human_approval_required": True},
        "rationale": "Require an explicit human checkpoint.",
        "source_sha256": SOURCE_HASH,
    }
    fields.update(overrides)
    return RemediationProposal(**fields)


def _hash(proposal: RemediationProposal) -> str:
    return sha256_value(proposal.to_dict())


def test_two_identical_proposals_hash_equal():
    assert _hash(_proposal()) == _hash(_proposal())


def test_changing_the_target_agent_changes_the_proposal_hash():
    assert _hash(_proposal()) != _hash(_proposal(agent_name="Deployment Agent"))


def test_changing_the_field_changes_the_proposal_hash():
    # same template, but the field being written is different
    other = _proposal(field_changes={"owner": "Platform Engineering"})
    assert _hash(_proposal()) != _hash(other)


def test_changing_only_the_value_changes_the_proposal_hash():
    team_a = _proposal(field_changes={"owner": "Team A"})
    team_b = _proposal(field_changes={"owner": "Team B"})
    assert _hash(team_a) != _hash(team_b)


def test_changing_the_intent_template_changes_the_proposal_hash():
    assert _hash(_proposal()) != _hash(_proposal(template_id="ASSIGN_OWNER"))


def test_changing_only_the_rationale_changes_the_proposal_hash():
    # "complete" means the whole record - even the wording a reviewer read.
    assert _hash(_proposal()) != _hash(_proposal(rationale="A different justification."))


def test_changing_the_source_hash_changes_the_proposal_hash():
    other = sha256_value({"agents": [{"agent_name": "B"}]})
    assert _hash(_proposal()) != _hash(_proposal(source_sha256=other))


def test_a_changed_proposal_value_makes_the_approval_stale():
    approved = _proposal(field_changes={"owner": "Team A"})
    approved_hash = _hash(approved)
    record = decide("wf-1", approved_hash, SOURCE_HASH, "Justin", "APPROVE", "Reviewed owner = Team A")

    # Unchanged proposal at apply time -> still valid.
    validate_approval(record, approved_hash, SOURCE_HASH)

    # Someone edited the value after approval.
    edited_hash = _hash(_proposal(field_changes={"owner": "Team B"}))
    with pytest.raises(ValueError, match="proposal changed"):
        validate_approval(record, edited_hash, SOURCE_HASH)
