"""Isolated deterministic verification of an approved remediation.

A human approves *intent*; this module checks *correctness*. Every check
runs on a throwaway copy of the environment - the real agent inventory is
never touched, so a failed or half-finished check can never corrupt it.

Day 6 builds this file up:
  Lab 2  the throwaway temp directory
  Lab 3  isolated_candidate_file()  - produce the candidate and isolate it
  Lab 4  scan_high_count() / rescan_before_and_after()  - re-scan and compare
  Lab 5  structural_checks()  - catch malformed candidate data
  Lab 6  target_and_key_checks()  - the change touched exactly one agent
  Lab 7  verify() -> VerificationResult  - the pass/fail evidence object (this slice)
  Lab 8  the positive and failure tests

Day 8 Lab 5 adds `require_verified()` - the gate between a
`VerificationResult` and GitHub planning. A failed result raises here, so
a change that did not verify never reaches `github_plan.create_plan()`.

Per the Day 6 Lab 1 decision, v1's `scanner.py` is used unchanged. v1's
`scan_environment(path)` reads a *bare JSON list of agents*, so the
re-scan writes `environment["agents"]` to a temp file and counts the
agents it rates HIGH. `scanner.py` stays the sole risk authority - this
module only compares two of its outputs.
"""

from __future__ import annotations

import json
import tempfile
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path

from remediation_templates import RemediationProposal, apply_proposal_to_environment
from scanner import REQUIRED_FIELDS, scan_environment

# The only top-level keys an environment (and therefore a candidate) may have.
ALLOWED_ENVIRONMENT_KEYS = {"environment_name", "source_system", "agents"}


@contextmanager
def isolated_candidate_file(environment: dict, proposal: RemediationProposal):
    """Produce the candidate (environment + proposal applied) and write it
    to a JSON file in a fresh temporary directory. Yields
    `(candidate, candidate_path)`; deletes the directory on exit.

    The proposal is applied in exactly one place - here - and only to a
    deep copy: `apply_proposal_to_environment()` copies the environment,
    applies the change to the one matching agent, and returns the new
    dict. The caller's `environment` is never modified, and the candidate
    then lives only in the throwaway temp file.

    If the proposal does not name exactly one agent in `environment`,
    `apply_proposal_to_environment()` raises `ValueError` before any
    temporary directory is created - nothing is left on disk.
    """
    candidate = apply_proposal_to_environment(environment, proposal)
    with tempfile.TemporaryDirectory(prefix="agentguard-verify-") as tmp_dir:
        candidate_path = Path(tmp_dir) / "candidate.json"
        candidate_path.write_text(json.dumps(candidate, indent=2), encoding="utf-8")
        yield candidate, candidate_path
    # tempfile.TemporaryDirectory has now deleted tmp_dir and its contents.


def scan_high_count(environment: dict) -> int:
    """Run v1's scanner on `environment`'s agents and count the HIGH ones.

    v1's `scan_environment(path)` reads a bare JSON list of agents from a
    file, so the agent list is written to a throwaway temp file first.
    Returns the number of agents v1 rates ``"HIGH"``. Raises whatever v1
    raises on a malformed agent (a missing required field); `verify()`
    runs `structural_checks()` first so it never reaches here with a
    malformed candidate.
    """
    with tempfile.TemporaryDirectory(prefix="agentguard-verify-") as tmp_dir:
        agents_path = Path(tmp_dir) / "agents.json"
        agents_path.write_text(
            json.dumps(environment.get("agents", []), indent=2), encoding="utf-8"
        )
        results = scan_environment(agents_path)
    return sum(1 for result in results if result.risk_level == "HIGH")


def rescan_before_and_after(environment: dict, candidate: dict) -> dict:
    """Scan `environment` (before) and `candidate` (after) and compare.

    The core v4 rule: a remediation may reduce or keep the HIGH-risk
    count, never raise it. Returns the two counts and the pass boolean.
    """
    before = scan_high_count(environment)
    after = scan_high_count(candidate)
    return {
        "before_high_count": before,
        "after_high_count": after,
        "high_count_did_not_increase": after <= before,
    }


def structural_checks(candidate: object) -> list[dict]:
    """Confirm `candidate` is well-formed enough to trust and to scan.

    Returns one ``{"name": str, "passed": bool}`` row per check. This
    function never raises - a malformed candidate produces ``passed:
    False`` rows, which `verify()` (Lab 7) treats as a failed
    verification rather than a crash.

    The checks:
      - it is a JSON object (a dict), not a list / string / None;
      - it survives a JSON round-trip unchanged (catches non-JSON values
        like a set, and lossy cases like a non-string dict key);
      - it has an ``agents`` list;
      - every agent is a dict carrying all of v1's REQUIRED_FIELDS, so
        `scan_environment` will be able to load it.
    """
    is_object = isinstance(candidate, dict)

    try:
        round_trips = json.loads(json.dumps(candidate)) == candidate
    except (TypeError, ValueError):
        round_trips = False

    agents = candidate.get("agents") if is_object else None
    has_agent_list = isinstance(agents, list)
    agents_complete = has_agent_list and all(
        isinstance(agent, dict) and all(field in agent for field in REQUIRED_FIELDS)
        for agent in agents
    )

    return [
        {"name": "candidate is a JSON object", "passed": is_object},
        {"name": "candidate serialises and re-reads unchanged", "passed": round_trips},
        {"name": "candidate has an agents list", "passed": has_agent_list},
        {"name": "every agent record is complete", "passed": agents_complete},
    ]


def target_and_key_checks(
    environment: dict, candidate: dict, proposal: RemediationProposal
) -> list[dict]:
    """Confirm the proposal touched exactly one intended agent and nothing else.

    Returns one ``{"name": str, "passed": bool}`` row per check; never
    raises. `apply_proposal_to_environment` already enforces the
    one-match rule when it builds the candidate - this re-checks it on
    the candidate independently, because verification must not trust the
    code that produced the candidate.

    The checks:
      - the agent count is unchanged (nothing added or removed);
      - the candidate has only the allowlisted top-level keys;
      - exactly one agent carries the proposal's target name;
      - exactly one agent differs from the source, and it is the target
        (this also catches an added agent, whose name is not in the
        source, and a no-op change, where nothing differs at all).
    """
    source_agents = environment.get("agents", []) if isinstance(environment, dict) else []
    candidate_agents = candidate.get("agents", []) if isinstance(candidate, dict) else []
    target = proposal.agent_name

    count_unchanged = len(candidate_agents) == len(source_agents)

    extra_keys = set(candidate) - ALLOWED_ENVIRONMENT_KEYS if isinstance(candidate, dict) else {"<not-an-object>"}
    only_allowlisted_keys = not extra_keys

    target_hits = sum(
        1
        for agent in candidate_agents
        if isinstance(agent, dict) and agent.get("agent_name") == target
    )
    exactly_one_target = target_hits == 1

    source_by_name = {
        agent.get("agent_name"): agent
        for agent in source_agents
        if isinstance(agent, dict)
    }
    changed = [
        agent.get("agent_name")
        for agent in candidate_agents
        if isinstance(agent, dict) and agent != source_by_name.get(agent.get("agent_name"))
    ]
    only_target_changed = changed == [target]

    return [
        {"name": "agent count unchanged", "passed": count_unchanged},
        {"name": "only allowlisted top-level keys", "passed": only_allowlisted_keys},
        {"name": "proposal targets exactly one agent", "passed": exactly_one_target},
        {"name": "only the target agent changed", "passed": only_target_changed},
    ]


@dataclass(frozen=True)
class VerificationResult:
    """The evidence from one verification - a verdict plus its detail.

    Frozen: once produced, it stands as a record. `to_dict()` is the
    *audit* form (a row for `audit_db`); `summary()` is the *display*
    form (a checklist); `checks` is the per-check detail behind the
    single `passed` boolean.
    """

    passed: bool
    checks: tuple
    before_high_count: int | None
    after_high_count: int | None
    candidate_environment: dict

    def to_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        total = len(self.checks)
        done = sum(1 for check in self.checks if check["passed"])
        head = "PASSED" if self.passed else "FAILED"
        lines = [f"Verification {head} ({done}/{total} checks)"]
        for check in self.checks:
            mark = "x" if check["passed"] else " "
            lines.append(f"  [{mark}] {check['name']}")
        return "\n".join(lines)


def verify(environment: dict, proposal: RemediationProposal) -> VerificationResult:
    """Verify an approved proposal against `environment`, in isolation.

    Runs the structural checks first; only if the candidate is well-formed
    does it re-scan and run the target / key checks. Returns a frozen
    `VerificationResult`: `passed` is `True` only if every check row
    passed.
    """
    with isolated_candidate_file(environment, proposal) as (candidate, candidate_path):
        checks = list(structural_checks(candidate))

        reread = json.loads(candidate_path.read_text(encoding="utf-8"))
        checks.append(
            {"name": "isolated write and reread succeeded", "passed": reread == candidate}
        )

        before_high = after_high = None
        if all(row["passed"] for row in checks):
            counts = rescan_before_and_after(environment, candidate)
            before_high = counts["before_high_count"]
            after_high = counts["after_high_count"]
            checks.append(
                {
                    "name": "high-risk count did not increase",
                    "passed": counts["high_count_did_not_increase"],
                }
            )
            checks.extend(target_and_key_checks(environment, candidate, proposal))

    passed = all(row["passed"] for row in checks)
    return VerificationResult(passed, tuple(checks), before_high, after_high, candidate)


def require_verified(result: VerificationResult) -> VerificationResult:
    """Gate between verification and GitHub planning.

    Return `result` unchanged if it passed. Otherwise raise `ValueError`
    naming every failed check. A caller builds a GitHub plan only *after*
    this returns, so a change that did not verify never reaches
    `github_plan.create_plan()` - no branch, no commit, no draft PR is
    planned for it. Same "raise on failure" contract as
    `approval.validate_approval()`.
    """
    if not isinstance(result, VerificationResult):
        raise TypeError(
            f"require_verified expects a VerificationResult, got {type(result).__name__}"
        )
    if not result.passed:
        failed = [row["name"] for row in result.checks if not row["passed"]]
        raise ValueError(
            "Verification failed; GitHub planning is blocked. "
            f"Failed checks: {failed}"
        )
    return result
