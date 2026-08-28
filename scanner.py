"""AgentGuard v1 scanner.

Loads AI agent records from a JSON file, runs five deterministic security
rules (AG-001 through AG-005) against each agent, and turns the results
into a score and a risk level. Everything used by app.py and the tests
lives in this one file, on purpose, to keep the project easy to follow.
"""

import json
from dataclasses import dataclass


REQUIRED_FIELDS = [
    "agent_name",
    "owner",
    "identity",
    "tools",
    "sensitive_data_access",
    "human_approval_required",
]


@dataclass
class Agent:
    agent_name: str
    owner: str
    identity: str
    tools: list
    sensitive_data_access: bool
    human_approval_required: bool


@dataclass
class Finding:
    rule_id: str
    severity: str
    points: int
    title: str
    explanation: str
    recommendation: str


@dataclass
class ScanResult:
    agent: Agent
    findings: list
    score: int
    risk_level: str


def load_agents(path) -> list:
    """Read a JSON file of agents and return a list of Agent objects."""
    with open(path, "r", encoding="utf-8") as f:
        raw_agents = json.load(f)

    agents = []
    for raw_agent in raw_agents:
        for required_field in REQUIRED_FIELDS:
            if required_field not in raw_agent:
                raise ValueError(
                    f"Agent record is missing required field '{required_field}': {raw_agent}"
                )
        agents.append(
            Agent(
                agent_name=raw_agent["agent_name"],
                owner=raw_agent["owner"],
                identity=raw_agent["identity"],
                tools=raw_agent["tools"],
                sensitive_data_access=raw_agent["sensitive_data_access"],
                human_approval_required=raw_agent["human_approval_required"],
            )
        )
    return agents


# --- AG-001: admin-level or wildcard tool access ---
def _check_ag_001(agent: Agent):
    matches = [t for t in agent.tools if t == "*" or t.startswith("admin_")]
    if not matches:
        return None
    return Finding(
        rule_id="AG-001",
        severity="HIGH",
        points=80,
        title="Agent has admin-level or wildcard tool access",
        explanation=(
            "This agent has at least one tool that grants broad admin-level "
            f"or wildcard access: {', '.join(matches)}. A tool like this can "
            "do almost anything, so a mistake or a compromised agent becomes "
            "extremely dangerous."
        ),
        recommendation=(
            "Replace the wildcard/admin_ tool with the smallest set of "
            "specific tools the agent actually needs."
        ),
    )


# --- AG-002: destructive or state-changing tool without human approval ---
_AG_002_PREFIXES = ("delete_", "deploy_", "write_", "change_", "terminate_", "revoke_")


def _check_ag_002(agent: Agent):
    matches = [t for t in agent.tools if t.startswith(_AG_002_PREFIXES)]
    if not matches or agent.human_approval_required:
        return None
    return Finding(
        rule_id="AG-002",
        severity="HIGH",
        points=60,
        title="Destructive action allowed without human approval",
        explanation=(
            "This agent can take a destructive or state-changing action "
            f"({', '.join(matches)}) and nothing requires a human to approve "
            "it first."
        ),
        recommendation=(
            "Turn on human approval for this agent, or remove the "
            "destructive tool."
        ),
    )


# --- AG-003: sensitive data access without human approval ---
def _check_ag_003(agent: Agent):
    if not agent.sensitive_data_access or agent.human_approval_required:
        return None
    return Finding(
        rule_id="AG-003",
        severity="HIGH",
        points=60,
        title="Sensitive data access without human approval",
        explanation=(
            "This agent can access sensitive data, but nothing requires a "
            "human to approve its actions."
        ),
        recommendation=(
            "Require human approval for this agent, or remove its access to "
            "sensitive data."
        ),
    )


# --- AG-004: outbound communication tool without human approval ---
_AG_004_PREFIXES = ("send_", "post_", "publish_")


def _check_ag_004(agent: Agent):
    matches = [t for t in agent.tools if t.startswith(_AG_004_PREFIXES)]
    if not matches or agent.human_approval_required:
        return None
    return Finding(
        rule_id="AG-004",
        severity="MEDIUM",
        points=30,
        title="Outbound communication without human approval",
        explanation=(
            "This agent can send outbound communication "
            f"({', '.join(matches)}) and nothing requires a human to "
            "approve it first."
        ),
        recommendation=(
            "Require human approval before this agent sends messages, "
            "posts, or publishes content."
        ),
    )


# --- AG-005: no owner assigned ---
def _check_ag_005(agent: Agent):
    if agent.owner and agent.owner.strip():
        return None
    return Finding(
        rule_id="AG-005",
        severity="LOW",
        points=10,
        title="Agent has no assigned owner",
        explanation=(
            "This agent has no owner listed, so it's unclear who is "
            "responsible for it."
        ),
        recommendation="Assign a specific person or team as the owner.",
    )


_RULES = [
    _check_ag_001,
    _check_ag_002,
    _check_ag_003,
    _check_ag_004,
    _check_ag_005,
]


def _risk_level(score: int) -> str:
    if score == 0:
        return "NO RISK FOUND"
    if score <= 29:
        return "LOW"
    if score <= 59:
        return "MEDIUM"
    return "HIGH"


def evaluate_agent(agent: Agent) -> ScanResult:
    """Run all five rules against one agent and return its scan result."""
    findings = [f for f in (rule(agent) for rule in _RULES) if f is not None]
    raw_score = sum(f.points for f in findings)
    score = min(raw_score, 100)
    return ScanResult(
        agent=agent,
        findings=findings,
        score=score,
        risk_level=_risk_level(score),
    )


def scan_environment(path) -> list:
    """Load every agent from a JSON file and evaluate each one."""
    return [evaluate_agent(a) for a in load_agents(path)]
