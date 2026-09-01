"""Allowlisted deterministic remediation templates for AgentGuard v4.

There are exactly three templates, and this file is where "exactly three"
is enforced. Each one names the v1 scanner rule(s) it clears and carries a
one-line rationale a reviewer can read.

This lab (Day 3, Lab 2) defines the set, the metadata, and the allowlist
gate. The deterministic transformation for each template is added in Day 3
Labs 4-6; the RemediationProposal wrapper in Lab 3;
apply_proposal_to_environment in Lab 7. The rationale for allowlisting at
all - rather than letting a model write a free-form patch - is in the
Day 3 Lab 1 learning-log entry.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class TemplateInfo:
    """What a template is for. No behaviour here - see Labs 4-6."""

    template_id: str
    rationale: str
    addresses: tuple[str, ...]   # v1 rule ids this template clears (see scanner.py)
    needs_input: str | None      # a value the user must supply, or None


_TEMPLATE_INFO: dict[str, TemplateInfo] = {
    "REQUIRE_HUMAN_APPROVAL": TemplateInfo(
        template_id="REQUIRE_HUMAN_APPROVAL",
        rationale="Require an explicit human checkpoint before the agent takes a high-impact action.",
        addresses=("AG-002", "AG-003", "AG-004"),
        needs_input=None,
    ),
    "ASSIGN_OWNER": TemplateInfo(
        template_id="ASSIGN_OWNER",
        rationale="Give the agent an accountable human owner.",
        addresses=("AG-005",),
        needs_input="owner",
    ),
    "REMOVE_BROAD_ADMIN_TOOL": TemplateInfo(
        template_id="REMOVE_BROAD_ADMIN_TOOL",
        rationale="Replace wildcard or administrator tool access with the specific tools the agent uses.",
        addresses=("AG-001",),
        needs_input=None,
    ),
}

# A read-only view of the three template records. Making this a
# MappingProxyType means a fourth template cannot be added by mutating the
# module at runtime - `TEMPLATE_INFO["X"] = ...` raises TypeError.
TEMPLATE_INFO = MappingProxyType(_TEMPLATE_INFO)

# The closed set. `"X" in ALLOWED_TEMPLATES` is the membership check every
# later step relies on.
ALLOWED_TEMPLATES = frozenset(TEMPLATE_INFO)


def require_allowlisted(template_id: str) -> TemplateInfo:
    """Return the TemplateInfo for an allowlisted template id.

    Raise ValueError for anything else. This is the single gate every
    later step (build the proposal, apply it, plan the PR) calls before
    it touches an agent - a template id that is not one of the three
    never reaches any transformation code.
    """
    try:
        return TEMPLATE_INFO[template_id]
    except (KeyError, TypeError):
        raise ValueError(
            f"Template is not allowlisted: {template_id!r}. "
            f"Allowed: {sorted(ALLOWED_TEMPLATES)}"
        ) from None


@dataclass(frozen=True)
class RemediationProposal:
    """One bounded, reviewable change to exactly one agent.

    Five parts - the same five a human reviewer needs to judge it:

      template_id    the INTENT       - which allowlisted template (Lab 2)
      agent_name     the TARGET       - exactly one agent, by name
      field_changes  the CHANGES      - {field: new_value}, and nothing else
      rationale      the RATIONALE    - one plain sentence: why this change
      source_sha256  the SOURCE HASH  - identifies the exact environment this
                                        proposal was built against, so a later
                                        approval binds to a specific starting
                                        state. Day 4 computes the real SHA-256;
                                        here it is only required to be a
                                        non-empty string.

    Frozen: once built, a proposal cannot be edited in place. A different
    change is a different proposal (and, on Day 4, a different hash), so a
    reviewer can never have the content shift underneath them.
    """

    template_id: str
    agent_name: str
    field_changes: dict
    rationale: str
    source_sha256: str

    def __post_init__(self) -> None:
        # The core invariant: the intent must be one of the three templates.
        require_allowlisted(self.template_id)
        if not isinstance(self.agent_name, str) or not self.agent_name.strip():
            raise ValueError("agent_name must name exactly one agent")
        if not isinstance(self.field_changes, dict) or not self.field_changes:
            raise ValueError("field_changes must be a non-empty {field: value} dict")
        # Defensive copy: the proposal owns its field_changes, so a caller
        # mutating the dict it passed in cannot change the proposal later.
        object.__setattr__(self, "field_changes", dict(self.field_changes))
        if not isinstance(self.rationale, str) or not self.rationale.strip():
            raise ValueError("rationale must be a non-empty sentence")
        if not isinstance(self.source_sha256, str) or not self.source_sha256:
            raise ValueError("source_sha256 must be a non-empty string")

    def to_dict(self) -> dict:
        """A plain dict of the five fields - for hashing, display, and the audit log."""
        return asdict(self)


# The owner name a person supplies for ASSIGN_OWNER is bounded to the same
# limit as the `owner` field everywhere else in the system
# (docs/v3_data_contract.md; discovery_adapter.MAX_FIELD_CHARS).
MAX_OWNER_CHARS = 200


def _validate_owner(value: object) -> str:
    """Validate the user-supplied owner name before it enters a proposal.

    The owner is the only free-text value a template takes from a person,
    so it is checked here - not trusted. Returns the stripped owner;
    raises ValueError on anything malformed.
    """
    if not isinstance(value, str):
        raise ValueError("ASSIGN_OWNER requires an owner name (a string).")
    owner = value.strip()
    if not owner:
        raise ValueError("ASSIGN_OWNER requires a non-empty owner name.")
    if len(owner) > MAX_OWNER_CHARS:
        raise ValueError(
            f"owner name is {len(owner)} characters, over the {MAX_OWNER_CHARS} limit."
        )
    if "\n" in owner or "\r" in owner:
        raise ValueError("owner name must be a single line.")
    return owner


def _remove_broad_tools(tools: object) -> list:
    """Return `tools` with every wildcard ('*') and administrator ('admin_*')
    entry removed. Order and every other tool are preserved.

    This is the exact inverse of v1's AG-001 check, so applying the result
    clears that finding. It never adds a tool - the agent ends up able to
    do only the specific things it could already do (least privilege).

    Raises ValueError if `tools` is not a list, or if there is nothing
    broad to remove (a remediation must actually remediate something).
    """
    if not isinstance(tools, list):
        raise ValueError("REMOVE_BROAD_ADMIN_TOOL: agent 'tools' must be a list.")
    kept = [t for t in tools if t != "*" and not str(t).startswith("admin_")]
    if kept == tools:
        raise ValueError(
            "REMOVE_BROAD_ADMIN_TOOL: this agent has no wildcard or admin_ tool to remove."
        )
    return kept


def build_proposal(
    template_id: str,
    agent: dict,
    source_sha256: str,
    value: str | None = None,
) -> RemediationProposal:
    """Turn one allowlisted template + one agent into a RemediationProposal.

    Deterministic: the same template, agent, and source hash always
    produce an equal proposal. `value` is a user-supplied input some
    templates need - the owner name for ASSIGN_OWNER, validated by
    _validate_owner(); other templates ignore it.

    All three templates are implemented:
      REQUIRE_HUMAN_APPROVAL   -> {"human_approval_required": True}   (AG-002/003/004)
      ASSIGN_OWNER             -> {"owner": <validated value>}        (AG-005)
      REMOVE_BROAD_ADMIN_TOOL  -> {"tools": <filtered list>}          (AG-001)
    """
    info = require_allowlisted(template_id)
    agent_name = agent.get("agent_name", "")

    if template_id == "REQUIRE_HUMAN_APPROVAL":
        # One deterministic field change: turn on the human checkpoint.
        # This clears v1 findings AG-002 / AG-003 / AG-004.
        field_changes = {"human_approval_required": True}
    elif template_id == "ASSIGN_OWNER":
        # The user supplies the owner name; validate it before use.
        # This clears v1 finding AG-005.
        field_changes = {"owner": _validate_owner(value)}
    elif template_id == "REMOVE_BROAD_ADMIN_TOOL":
        # Drop every wildcard and admin_ tool, keep the rest. Clears AG-001.
        field_changes = {"tools": _remove_broad_tools(agent.get("tools", []))}
    else:  # pragma: no cover - require_allowlisted already gated this
        raise AssertionError(f"unhandled allowlisted template: {template_id!r}")

    return RemediationProposal(
        template_id=template_id,
        agent_name=agent_name,
        field_changes=field_changes,
        rationale=info.rationale,
        source_sha256=source_sha256,
    )


def apply_proposal_to_environment(
    environment: dict,
    proposal: RemediationProposal,
) -> dict:
    """Return a NEW environment with `proposal` applied - the input is never touched.

    This is the "planning" operation. To show a diff, or to re-scan and
    verify a change (Day 6), v4 needs to see the "after" state - but the
    real (synthetic) source must not move. So:

      1. `copy.deepcopy(environment)` - a fully independent copy. Every
         nested list and dict is duplicated, so mutating the copy can
         never reach `environment`. A shallow copy would share the
         `agents` list and the agent dicts.
      2. find the one agent the proposal targets. Exactly one match is
         required: zero means this is the wrong environment (or the agent
         was renamed); more than one is ambiguous.
      3. apply the proposal's bounded `field_changes` to that agent in the
         copy, and return the copy.
    """
    updated = copy.deepcopy(environment)
    matches = [
        agent
        for agent in updated.get("agents", [])
        if agent.get("agent_name") == proposal.agent_name
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Proposal must match exactly one agent; found {len(matches)} "
            f"named {proposal.agent_name!r}."
        )
    matches[0].update(proposal.field_changes)
    return updated
