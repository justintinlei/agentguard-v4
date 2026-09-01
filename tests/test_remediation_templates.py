"""Tests for remediation_templates.py.

Day 3 Lab 2: the closed set, the metadata, and the allowlist gate.
Day 3 Lab 3: the RemediationProposal data contract.
Day 3 Labs 4-6: build_proposal for all three templates
  (REQUIRE_HUMAN_APPROVAL, ASSIGN_OWNER, REMOVE_BROAD_ADMIN_TOOL).
apply_proposal_to_environment (Lab 7) is tested when it is added.
"""

import copy
from dataclasses import FrozenInstanceError

import pytest

import remediation_templates as rt
import scanner

# The v1 scanner's rule ids (scanner.py, AG-001 .. AG-005).
V1_RULE_IDS = {"AG-001", "AG-002", "AG-003", "AG-004", "AG-005"}

EXPECTED_IDS = {"REQUIRE_HUMAN_APPROVAL", "ASSIGN_OWNER", "REMOVE_BROAD_ADMIN_TOOL"}


def test_exactly_three_allowlisted_templates():
    assert set(rt.ALLOWED_TEMPLATES) == EXPECTED_IDS
    assert set(rt.TEMPLATE_INFO) == EXPECTED_IDS


def test_every_template_has_a_real_rationale_and_addresses():
    for template_id, info in rt.TEMPLATE_INFO.items():
        assert info.template_id == template_id
        assert info.rationale.strip().endswith(".")
        assert len(info.rationale) > 20
        assert info.addresses, template_id
        assert set(info.addresses) <= V1_RULE_IDS, template_id


def test_the_templates_cover_the_v1_findings_they_exist_for():
    covered = set().union(*(info.addresses for info in rt.TEMPLATE_INFO.values()))
    # AG-001 (broad tools), AG-002/003/004 (no human approval), AG-005 (no owner)
    assert {"AG-001", "AG-002", "AG-003", "AG-005"} <= covered


def test_only_assign_owner_needs_a_user_value():
    assert rt.TEMPLATE_INFO["ASSIGN_OWNER"].needs_input == "owner"
    assert rt.TEMPLATE_INFO["REQUIRE_HUMAN_APPROVAL"].needs_input is None
    assert rt.TEMPLATE_INFO["REMOVE_BROAD_ADMIN_TOOL"].needs_input is None


def test_require_allowlisted_returns_the_info_for_each_of_the_three():
    for template_id in EXPECTED_IDS:
        assert rt.require_allowlisted(template_id) is rt.TEMPLATE_INFO[template_id]


@pytest.mark.parametrize(
    "bad_id",
    ["RUN_SHELL", "DROP_TABLE", "", "require_human_approval", "REQUIRE_HUMAN_APPROVAL ", None],
)
def test_require_allowlisted_refuses_anything_not_on_the_list(bad_id):
    with pytest.raises(ValueError):
        rt.require_allowlisted(bad_id)


# --- Day 3, Lab 3: the RemediationProposal data contract -----------------

def _valid_proposal(**overrides):
    kwargs = dict(
        template_id="REQUIRE_HUMAN_APPROVAL",
        agent_name="Customer Support Agent",
        field_changes={"human_approval_required": True},
        rationale="Require a human checkpoint before this agent acts.",
        source_sha256="a" * 64,
    )
    kwargs.update(overrides)
    return rt.RemediationProposal(**kwargs)


def test_proposal_carries_the_five_contract_fields():
    proposal = _valid_proposal()
    assert proposal.to_dict() == {
        "template_id": "REQUIRE_HUMAN_APPROVAL",
        "agent_name": "Customer Support Agent",
        "field_changes": {"human_approval_required": True},
        "rationale": "Require a human checkpoint before this agent acts.",
        "source_sha256": "a" * 64,
    }


def test_proposal_is_frozen():
    proposal = _valid_proposal()
    with pytest.raises(FrozenInstanceError):
        proposal.template_id = "ASSIGN_OWNER"


def test_proposal_rejects_a_non_allowlisted_template():
    with pytest.raises(ValueError):
        _valid_proposal(template_id="RUN_SHELL")


@pytest.mark.parametrize(
    "bad",
    [
        {"agent_name": ""},
        {"agent_name": "   "},
        {"agent_name": None},
        {"field_changes": {}},
        {"field_changes": ["not", "a", "dict"]},
        {"rationale": ""},
        {"rationale": "   "},
        {"source_sha256": ""},
        {"source_sha256": None},
    ],
)
def test_proposal_rejects_a_malformed_contract(bad):
    with pytest.raises(ValueError):
        _valid_proposal(**bad)


# --- Day 3, Lab 4: build_proposal (REQUIRE_HUMAN_APPROVAL) ----------------

_AGENT = {
    "agent_name": "Customer Support Agent",
    "owner": "",
    "tools": ["read_ticket", "send_email", "delete_customer_record"],
    "sensitive_data_access": True,
    "human_approval_required": False,
}


def test_build_proposal_require_human_approval_makes_one_field_change():
    proposal = rt.build_proposal("REQUIRE_HUMAN_APPROVAL", _AGENT, "s" * 64)
    assert proposal.template_id == "REQUIRE_HUMAN_APPROVAL"
    assert proposal.agent_name == "Customer Support Agent"
    assert proposal.field_changes == {"human_approval_required": True}
    assert proposal.rationale == rt.TEMPLATE_INFO["REQUIRE_HUMAN_APPROVAL"].rationale
    assert proposal.source_sha256 == "s" * 64


def test_build_proposal_is_deterministic():
    a = rt.build_proposal("REQUIRE_HUMAN_APPROVAL", _AGENT, "s" * 64)
    b = rt.build_proposal("REQUIRE_HUMAN_APPROVAL", _AGENT, "s" * 64)
    assert a == b


def test_build_proposal_does_not_touch_the_agent():
    before = dict(_AGENT)
    rt.build_proposal("REQUIRE_HUMAN_APPROVAL", _AGENT, "s" * 64)
    assert _AGENT == before  # the proposal only describes the change


def test_build_proposal_rejects_a_non_allowlisted_template():
    with pytest.raises(ValueError):
        rt.build_proposal("RUN_SHELL", _AGENT, "s" * 64)


# --- Day 3, Lab 5: build_proposal (ASSIGN_OWNER) with required input -----

def test_build_proposal_assign_owner_sets_the_owner_field():
    proposal = rt.build_proposal("ASSIGN_OWNER", _AGENT, "s" * 64, value="Security Operations")
    assert proposal.template_id == "ASSIGN_OWNER"
    assert proposal.agent_name == "Customer Support Agent"
    assert proposal.field_changes == {"owner": "Security Operations"}
    assert proposal.rationale == rt.TEMPLATE_INFO["ASSIGN_OWNER"].rationale


def test_build_proposal_assign_owner_strips_whitespace():
    proposal = rt.build_proposal("ASSIGN_OWNER", _AGENT, "s" * 64, value="  Security Ops  ")
    assert proposal.field_changes == {"owner": "Security Ops"}


def test_build_proposal_assign_owner_is_deterministic():
    a = rt.build_proposal("ASSIGN_OWNER", _AGENT, "s" * 64, value="Platform Team")
    b = rt.build_proposal("ASSIGN_OWNER", _AGENT, "s" * 64, value="Platform Team")
    assert a == b


def test_build_proposal_assign_owner_does_not_touch_the_agent():
    before = dict(_AGENT)
    rt.build_proposal("ASSIGN_OWNER", _AGENT, "s" * 64, value="Platform Team")
    assert _AGENT == before


@pytest.mark.parametrize(
    "bad_value",
    [
        None,               # not supplied
        "",                 # empty
        "   ",              # whitespace only
        123,                # not a string
        ["Platform Team"],  # not a string
        "x" * 201,          # over the 200-char limit
        "Team A\nTeam B",   # multi-line
        "Team\rB",          # carriage return
    ],
)
def test_build_proposal_assign_owner_rejects_a_bad_owner_value(bad_value):
    with pytest.raises(ValueError):
        rt.build_proposal("ASSIGN_OWNER", _AGENT, "s" * 64, value=bad_value)


# --- Day 3, Lab 6: build_proposal (REMOVE_BROAD_ADMIN_TOOL) --------------

_AGENT_BROAD = {
    "agent_name": "Ops Bot",
    "owner": "Platform",
    "identity": "ops-bot",
    "tools": ["*", "read_logs", "admin_delete_user", "send_alert"],
    "sensitive_data_access": False,
    "human_approval_required": True,
}


def test_remove_broad_admin_tool_drops_wildcard_and_admin_and_keeps_order():
    proposal = rt.build_proposal("REMOVE_BROAD_ADMIN_TOOL", _AGENT_BROAD, "s" * 64)
    assert proposal.field_changes == {"tools": ["read_logs", "send_alert"]}
    assert proposal.template_id == "REMOVE_BROAD_ADMIN_TOOL"
    assert proposal.agent_name == "Ops Bot"
    assert proposal.rationale == rt.TEMPLATE_INFO["REMOVE_BROAD_ADMIN_TOOL"].rationale


def test_remove_broad_admin_tool_is_deterministic_and_does_not_mutate():
    tools_before = list(_AGENT_BROAD["tools"])
    a = rt.build_proposal("REMOVE_BROAD_ADMIN_TOOL", _AGENT_BROAD, "s" * 64)
    b = rt.build_proposal("REMOVE_BROAD_ADMIN_TOOL", _AGENT_BROAD, "s" * 64)
    assert a == b
    assert _AGENT_BROAD["tools"] == tools_before  # read, never mutated


def test_remove_broad_admin_tool_allows_an_empty_result():
    agent = {**_AGENT_BROAD, "tools": ["*"]}
    proposal = rt.build_proposal("REMOVE_BROAD_ADMIN_TOOL", agent, "s" * 64)
    assert proposal.field_changes == {"tools": []}


@pytest.mark.parametrize(
    "tools",
    [
        ["read_logs", "send_alert"],   # nothing broad to remove -> no-op
        "everything",                  # not a list
        123,                           # not a list
    ],
)
def test_remove_broad_admin_tool_rejects_a_bad_or_pointless_tools_list(tools):
    agent = {**_AGENT_BROAD, "tools": tools}
    with pytest.raises(ValueError):
        rt.build_proposal("REMOVE_BROAD_ADMIN_TOOL", agent, "s" * 64)


def test_remove_broad_admin_tool_rejects_an_agent_with_no_tools_key():
    agent = {"agent_name": "No Tools Bot"}
    with pytest.raises(ValueError):
        rt.build_proposal("REMOVE_BROAD_ADMIN_TOOL", agent, "s" * 64)


def test_remove_broad_admin_tool_matches_only_the_exact_broad_shapes():
    agent = {**_AGENT_BROAD, "tools": ["admin_x", "administrator_x", "readmin_x", "*"]}
    proposal = rt.build_proposal("REMOVE_BROAD_ADMIN_TOOL", agent, "s" * 64)
    # admin_x and * are broad; administrator_x and readmin_x are not.
    assert proposal.field_changes == {"tools": ["administrator_x", "readmin_x"]}


def test_the_filtered_tools_clear_v1_finding_ag_001():
    def ag_001(tools):
        agent = scanner.Agent(
            agent_name="Ops Bot", owner="Platform", identity="ops-bot",
            tools=tools, sensitive_data_access=False, human_approval_required=True,
        )
        return any(f.rule_id == "AG-001" for f in scanner.evaluate_agent(agent).findings)

    assert ag_001(_AGENT_BROAD["tools"]) is True
    proposal = rt.build_proposal("REMOVE_BROAD_ADMIN_TOOL", _AGENT_BROAD, "s" * 64)
    assert ag_001(proposal.field_changes["tools"]) is False


# --- Day 3, Lab 7: apply_proposal_to_environment (deep copy only) -------

def _env():
    return {
        "environment_name": "Demo",
        "agents": [
            {
                "agent_name": "Customer Support Agent",
                "owner": "",
                "identity": "support-agent-prod",
                "tools": ["read_ticket", "send_email"],
                "sensitive_data_access": True,
                "human_approval_required": False,
            },
            {
                "agent_name": "Research Agent",
                "owner": "Product Research",
                "identity": "research-agent-readonly",
                "tools": ["web_search"],
                "sensitive_data_access": False,
                "human_approval_required": False,
            },
        ],
    }


def test_apply_puts_the_change_on_the_named_agent_in_the_returned_copy():
    env = _env()
    proposal = rt.build_proposal("REQUIRE_HUMAN_APPROVAL", env["agents"][0], "s" * 64)
    updated = rt.apply_proposal_to_environment(env, proposal)

    support = next(a for a in updated["agents"] if a["agent_name"] == "Customer Support Agent")
    assert support["human_approval_required"] is True
    # the other agent is untouched
    research = next(a for a in updated["agents"] if a["agent_name"] == "Research Agent")
    assert research["human_approval_required"] is False


def test_apply_never_mutates_the_input_environment():
    env = _env()
    snapshot = copy.deepcopy(env)
    proposal = rt.build_proposal("REQUIRE_HUMAN_APPROVAL", env["agents"][0], "s" * 64)

    updated = rt.apply_proposal_to_environment(env, proposal)

    assert env == snapshot                 # deep-equal to before the call
    assert updated is not env               # a new object
    assert updated["agents"][0] is not env["agents"][0]   # nested objects copied too


def test_apply_with_remove_broad_tool_leaves_the_original_wildcard_in_place():
    env = _env()
    env["agents"][0]["tools"] = ["*", "read_ticket"]
    proposal = rt.build_proposal("REMOVE_BROAD_ADMIN_TOOL", env["agents"][0], "s" * 64)

    updated = rt.apply_proposal_to_environment(env, proposal)

    assert updated["agents"][0]["tools"] == ["read_ticket"]
    assert env["agents"][0]["tools"] == ["*", "read_ticket"]  # source unchanged


def test_apply_rejects_a_proposal_that_matches_no_agent():
    env = _env()
    proposal = rt.build_proposal("REQUIRE_HUMAN_APPROVAL", {"agent_name": "Ghost Agent"}, "s" * 64)
    with pytest.raises(ValueError, match="exactly one agent"):
        rt.apply_proposal_to_environment(env, proposal)


def test_apply_rejects_an_environment_with_two_agents_of_the_same_name():
    env = _env()
    env["agents"].append(dict(env["agents"][0]))  # duplicate the support agent
    proposal = rt.build_proposal("REQUIRE_HUMAN_APPROVAL", env["agents"][0], "s" * 64)
    with pytest.raises(ValueError, match="exactly one agent"):
        rt.apply_proposal_to_environment(env, proposal)


# --- Day 3, Lab 8: template + immutability invariants -------------------
#
# These tests exist to FAIL if the two Day 3 guarantees ever stop holding:
#   (1) only the three allowlisted templates can run;
#   (2) each one changes only its single documented field.

# The one field each template is allowed to change.
_TEMPLATE_ALLOWED_KEYS = {
    "REQUIRE_HUMAN_APPROVAL": {"human_approval_required"},
    "ASSIGN_OWNER": {"owner"},
    "REMOVE_BROAD_ADMIN_TOOL": {"tools"},
}
# Fields a remediation must never touch.
_NEVER_CHANGED = {"agent_name", "identity", "sensitive_data_access"}


def _proposal_for(template_id):
    agent = {"agent_name": "Inv Bot", "identity": "inv-bot", "tools": ["*", "read_x"],
             "owner": "", "sensitive_data_access": True, "human_approval_required": False}
    value = "Security Operations" if template_id == "ASSIGN_OWNER" else None
    return rt.build_proposal(template_id, agent, "s" * 64, value=value)


@pytest.mark.parametrize("template_id,allowed", _TEMPLATE_ALLOWED_KEYS.items())
def test_each_template_changes_only_its_one_documented_field(template_id, allowed):
    proposal = _proposal_for(template_id)
    assert set(proposal.field_changes) == allowed


@pytest.mark.parametrize("template_id", _TEMPLATE_ALLOWED_KEYS)
def test_no_template_ever_changes_an_identity_field(template_id):
    proposal = _proposal_for(template_id)
    assert set(proposal.field_changes).isdisjoint(_NEVER_CHANGED)


def test_apply_changes_only_the_proposal_keys_on_only_the_target_agent():
    env = _env()
    proposal = rt.build_proposal("REQUIRE_HUMAN_APPROVAL", env["agents"][0], "s" * 64)
    updated = rt.apply_proposal_to_environment(env, proposal)

    before, after = env["agents"][0], updated["agents"][0]
    changed_keys = {k for k in after if before.get(k) != after.get(k)}
    assert changed_keys == set(proposal.field_changes)   # only the proposal's keys
    assert set(before) == set(after)                     # no key added or removed
    assert updated["agents"][1:] == env["agents"][1:]    # every other agent untouched


# --- only approved templates ------------------------------------------------

def test_allowed_templates_is_a_frozen_set():
    assert isinstance(rt.ALLOWED_TEMPLATES, frozenset)
    with pytest.raises(AttributeError):
        rt.ALLOWED_TEMPLATES.add("EVIL")


def test_the_template_registry_cannot_be_extended_at_runtime():
    new = rt.TemplateInfo("EVIL", "Do evil.", ("AG-001",), None)
    with pytest.raises(TypeError):
        rt.TEMPLATE_INFO["EVIL"] = new
    assert "EVIL" not in rt.ALLOWED_TEMPLATES


@pytest.mark.parametrize("bad", ["RUN_SHELL", "require_human_approval", "", None])
def test_build_proposal_and_gate_still_refuse_unapproved_ids(bad):
    with pytest.raises(ValueError):
        rt.require_allowlisted(bad)
    with pytest.raises(ValueError):
        rt.build_proposal(bad, {"agent_name": "A"}, "s" * 64)


# --- frozen records -----------------------------------------------------------

def test_template_info_records_are_frozen():
    with pytest.raises(FrozenInstanceError):
        rt.TEMPLATE_INFO["ASSIGN_OWNER"].rationale = "changed"


def test_proposal_field_changes_cannot_be_rebound():
    proposal = _valid_proposal()
    with pytest.raises(FrozenInstanceError):
        proposal.field_changes = {}


def test_mutating_the_source_dict_after_build_does_not_change_the_proposal():
    changes = {"human_approval_required": True}
    proposal = rt.RemediationProposal(
        template_id="REQUIRE_HUMAN_APPROVAL",
        agent_name="A",
        field_changes=changes,
        rationale="Reviewed.",
        source_sha256="a" * 64,
    )
    changes["owner"] = "sneaky"          # mutate what we passed in
    assert proposal.field_changes == {"human_approval_required": True}
