"""Adapter between MCP's discovered agent shape and v1's Agent type.

discovery_core.list_agents() returns plain dicts, parsed straight from
whatever JSON a connected registry happens to contain - an external
schema this project doesn't control. v1's scanner.py, unchanged since
v1, only ever accepts its own Agent dataclass. Handing a raw dict
somewhere the scanner expected an Agent would mean a future MCP schema
change (a renamed field, a missing one) fails silently or deep inside
the scanner's own logic, instead of loudly and in one obvious place.

This lab (Day 7, Lab 1) defined that one boundary: converting a single
MCP-shaped agent dict into a single Agent, checking that all required
keys are present. Lab 2 (this one) goes further: presence alone isn't
enough, because a present-but-wrong-typed value sails through
unnoticed and can either crash or, worse, silently mislead v1's rules.
If `tools` contained a non-string entry, scanner.py's own
`tool.startswith(...)` calls would crash with an obscure
AttributeError deep inside a rule. If `sensitive_data_access` were the
*string* "false" instead of the boolean False, Python treats a
non-empty string as truthy - AG-003 would silently treat a "no
sensitive access" agent as if it had sensitive access, a wrong
security classification with no crash to reveal it. Python dataclasses
never enforce their own type hints at runtime, so nothing but this
adapter stops either scenario.

Lab 3 (this one) goes from one agent to the whole discovered
environment. discovery_core.list_agents() returns a dict wrapping an
`agents` list plus metadata (environment_name, count, provenance
fields) - but v1's scanner has no concept of an "environment" at all.
Every real caller of it in this codebase (app.py, app_v2.py,
v2_service.py, every test) builds a plain list[Agent] by hand and
calls evaluate_agent() per item. "The exact v1 scanner shape" this lab
produces is that flat list - nothing about environment_name or other
metadata is part of it, because v1 never asked for it. Provenance
(source_sha256, correlation_id) travels separately - preserving it
alongside the agent list is explicitly Lab 4's job.

Lab 4 (this one) preserves provenance - source_name, source_sha256,
correlation_id - kept deliberately separate from list[Agent], since
v1's Agent and ScanResult have no provenance field and never will
(scanner.py stays unchanged). That data has to travel alongside a
future risk report, not inside it; attaching it to a real combined
report is Lab 5's job.

Lab 5 (this one) is the integration point Labs 1-4 built toward: run
v1's real, unmodified evaluate_agent() against MCP-discovered agents.
Nothing about v1's five deterministic rules changes or gets
reimplemented here - the same function app.py and v2_service.py
already call is called again, just fed Agent objects that originated
from MCP instead of a JSON file. That reuse, unchanged, is the whole
point: v1's policy doesn't need to know or care where its input came
from.

Lab 6 (this one) composes MCP discovery with v2's full pipeline -
scan, retrieve policy evidence, generate a grounded mock/live
explanation, validate it - by calling v2_service.analyze_agent()
unchanged, the same single real entry point every other caller
already uses. Nothing about retrieval or explanation is reimplemented
here; this function only supplies MCP-discovered agents as input.

Lab 7 (this one) audits the full test suite rather than adding new
behavior, and found one real bug in the process: if mcp_output itself
wasn't a dict at all (a string, None, a list), mcp_inventory_to_agents()
and extract_provenance() both called .get(...) directly and crashed
with a raw AttributeError instead of the same clean ValueError every
other malformed case produces. Fixed with a one-line isinstance guard
in both functions, matching the defensive style already used
throughout this file. Nothing here changes scanner.py or v2_service.py.

Day 9 security review: the adapter validated field *presence* and
*type* but never *size* or *count*, even though docs/v3_data_contract.md
wrote those limits down and both it and docs/v3_threat_model.md claimed
the adapter enforced them. A compromised or swapped MCP server could
therefore hand v1's scanner an unbounded agent list or a multi-megabyte
string. Closed here: MAX_AGENTS / MAX_FIELD_CHARS / MAX_TOOLS /
MAX_TOOL_NAME_CHARS, checked before any value reaches evaluate_agent().
"""

from __future__ import annotations

from analysis_schema import GroundedAnalysis
from claude_analyst import UsageRecord
from scanner import REQUIRED_FIELDS, Agent, evaluate_agent
from v2_service import analyze_agent


# Size and count limits, straight from docs/v3_data_contract.md's
# "Required fields and maximum sizes" table. The Day 9 security review
# found that table was written but never enforced anywhere - presence
# and type were checked, size and count were not - so a compromised or
# swapped MCP server could hand v1's scanner an unbounded list or a
# multi-megabyte string. These constants close that gap at the one
# boundary that owns it: the adapter, before any value reaches
# scanner.evaluate_agent().
MAX_AGENTS = 50
MAX_FIELD_CHARS = 200
MAX_TOOLS = 20
MAX_TOOL_NAME_CHARS = 100


def mcp_agent_to_agent(mcp_agent: dict) -> Agent:
    """Convert one MCP-discovered agent dict into v1's Agent dataclass.

    Reuses scanner.REQUIRED_FIELDS - the same list v1's own
    load_agents() checks against - as the single source of truth for
    what an agent record must contain, rather than redeclaring a
    separate copy that could drift out of sync. Every field's value is
    checked against the exact type scanner.Agent itself declares, not
    just its presence.
    """
    for required_field in REQUIRED_FIELDS:
        if required_field not in mcp_agent:
            raise ValueError(f"MCP agent is missing required field '{required_field}': {mcp_agent}")

    agent_name = mcp_agent["agent_name"]
    owner = mcp_agent["owner"]
    identity = mcp_agent["identity"]
    tools = mcp_agent["tools"]
    sensitive_data_access = mcp_agent["sensitive_data_access"]
    human_approval_required = mcp_agent["human_approval_required"]

    if not isinstance(agent_name, str):
        raise ValueError(f"agent_name must be a string, got {agent_name!r}")
    if not isinstance(owner, str):
        raise ValueError(f"owner must be a string, got {owner!r}")
    if not isinstance(identity, str):
        raise ValueError(f"identity must be a string, got {identity!r}")
    if not isinstance(tools, list) or not all(isinstance(tool, str) for tool in tools):
        raise ValueError(f"tools must be a list of strings, got {tools!r}")
    if not isinstance(sensitive_data_access, bool):
        raise ValueError(f"sensitive_data_access must be true or false, got {sensitive_data_access!r}")
    if not isinstance(human_approval_required, bool):
        raise ValueError(f"human_approval_required must be true or false, got {human_approval_required!r}")

    # Size limits (docs/v3_data_contract.md). Messages report len(), never
    # the value itself - echoing a multi-megabyte string back would be the
    # same unbounded-data problem one layer up.
    for field_name, value in (("agent_name", agent_name), ("owner", owner), ("identity", identity)):
        if len(value) > MAX_FIELD_CHARS:
            raise ValueError(
                f"{field_name} is {len(value)} characters, over the {MAX_FIELD_CHARS} limit"
            )
    if len(tools) > MAX_TOOLS:
        raise ValueError(f"tools has {len(tools)} entries, over the {MAX_TOOLS} limit")
    for tool in tools:
        if len(tool) > MAX_TOOL_NAME_CHARS:
            raise ValueError(
                f"a tool name is {len(tool)} characters, over the {MAX_TOOL_NAME_CHARS} limit"
            )

    return Agent(
        agent_name=agent_name,
        owner=owner,
        identity=identity,
        tools=tools,
        sensitive_data_access=sensitive_data_access,
        human_approval_required=human_approval_required,
    )


def mcp_inventory_to_agents(mcp_output: dict) -> list[Agent]:
    """Convert a full MCP-discovered inventory into a list[Agent] -
    the exact shape v1's scanner accepts everywhere it's actually
    called, in the same order the agents were discovered.

    Reuses mcp_agent_to_agent() for each entry rather than
    re-implementing its checks, and adds the index of any failing
    agent to the error - a list of several agents needs to say which
    one is bad, not just that one is.
    """
    if not isinstance(mcp_output, dict):
        raise ValueError(f"MCP inventory must be an object, got {mcp_output!r}")
    agents = mcp_output.get("agents")
    if not isinstance(agents, list):
        raise ValueError(f"MCP inventory must contain an 'agents' list, got {agents!r}")
    if len(agents) > MAX_AGENTS:
        raise ValueError(f"MCP inventory has {len(agents)} agents, over the {MAX_AGENTS} limit")

    converted = []
    for index, mcp_agent in enumerate(agents):
        if not isinstance(mcp_agent, dict):
            raise ValueError(f"Agent at index {index} is not an object: {mcp_agent!r}")
        try:
            converted.append(mcp_agent_to_agent(mcp_agent))
        except ValueError as exc:
            raise ValueError(f"Agent at index {index} is invalid: {exc}") from exc
    return converted


PROVENANCE_FIELDS = ("source_name", "source_sha256", "correlation_id")


def extract_provenance(mcp_output: dict) -> dict:
    """Extract the provenance fields from an MCP inventory response, so
    they can travel alongside a future risk report without living
    inside v1's Agent/ScanResult, which were never designed to hold
    them and never will be.

    Missing fields raise rather than default to "" - a missing hash
    silently defaulted to an empty string would look like "verified,
    empty" instead of "never provided", which is exactly the kind of
    quiet audit-trail gap this adapter exists to prevent.
    """
    if not isinstance(mcp_output, dict):
        raise ValueError(f"MCP inventory must be an object, got {mcp_output!r}")
    provenance = {}
    for field in PROVENANCE_FIELDS:
        if field not in mcp_output:
            raise ValueError(f"MCP inventory is missing required provenance field '{field}'")
        value = mcp_output[field]
        if not isinstance(value, str):
            raise ValueError(f"{field} must be a string, got {value!r}")
        # The data contract's tables don't cover provenance, but on the
        # MCP path the server supplies these and correlation_id is written
        # to the audit log - an oversized value is a log-bloat vector, so
        # the same MAX_FIELD_CHARS bound is applied defensively.
        if len(value) > MAX_FIELD_CHARS:
            raise ValueError(
                f"{field} is {len(value)} characters, over the {MAX_FIELD_CHARS} limit"
            )
        provenance[field] = value
    return provenance


def scan_mcp_inventory(mcp_output: dict) -> dict:
    """Run v1's unchanged evaluate_agent() against every MCP-discovered
    agent, preserving provenance alongside the results.

    Nothing about v1's deterministic rules is reimplemented here - the
    same evaluate_agent() app.py and v2_service.py already call is
    called again, unmodified, just fed agents that originated from MCP
    instead of a JSON file.
    """
    agents = mcp_inventory_to_agents(mcp_output)
    provenance = extract_provenance(mcp_output)
    results = [evaluate_agent(agent) for agent in agents]
    return {"results": results, "provenance": provenance}


def analyze_mcp_inventory(
    mcp_output: dict, mode: str | None = None
) -> list[tuple[GroundedAnalysis, UsageRecord]]:
    """Run v2's unchanged full pipeline - scan, retrieve, explain,
    validate - for every MCP-discovered agent.

    mode passes straight through with no new default logic:
    analyze_agent() already defaults safely to "mock" when mode is
    None, so this function neither needs nor adds its own default.
    """
    agents = mcp_inventory_to_agents(mcp_output)
    return [analyze_agent(agent, mode=mode) for agent in agents]
