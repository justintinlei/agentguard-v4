"""AgentGuard v4 failure-injection evaluation.

The opposite of a normal test suite: every check *injects* a bad input -
a skipped workflow state, a rollback of an already-merged PR, a
risk-raising remediation, a drifted approval, a broken `gh` command, an
unapproved repository - and passes only if v4 **refuses** it (raises,
returns False, stops, or records FAILED). Running them all and getting
"every injection was refused" is the concrete proof that v4 fails closed.

A few positive controls are kept too - a valid remediation still verifies
and still reaches a five-command plan, a dry run is still all DRY_RUN -
so "fails closed" is not just "broken closed".

Standalone:  python evals/run_v4_evals.py
Exit 0 = every injection was caught; non-zero = something got through.

No network, no real `git` / `gh` (subprocess.run is patched), no API
money. All data is synthetic; the SQLite audit log is a throwaway temp
file. The v4 release gate does not run this yet (Day 10 Lab 1 candidate);
each refusal here is also covered by a Day 3-8 pytest test.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from approval import approval_is_current, decide
from audit_db import list_events
from github_plan import create_plan, execute_plan
from proposal_hash import sha256_value
from remediation_templates import RemediationProposal, build_proposal
from rollback import rollback_plan
from verifier import require_verified, verify
from workflow import WorkflowState, record_terminal_state, transition

# The one allowlisted synthetic demo repo (Day 7). A valid create_plan()
# uses this; "owner/repo" is used deliberately as one of the injections.
DEMO_REPO = "justintinlei/agentguard-remediation-demo"
SAFE_BRANCH = "agentguard/workflow-8"

# A synthetic, low-risk starting environment.
ENV = {
    "environment_name": "Failure Injection Demo",
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


def _raises(fn, exc=Exception) -> bool:
    """True if calling `fn()` raises `exc` (or a subclass)."""
    try:
        fn()
        return False
    except exc:
        return True


# --- injections: each returns True when v4 refused the bad input ----------


def state_skipping_is_refused() -> bool:
    # You cannot jump PROPOSED -> VERIFIED and skip human approval.
    return _raises(
        lambda: transition(WorkflowState("wf", "PROPOSED"), "VERIFIED"), ValueError
    )


def rollback_after_merge_is_refused() -> bool:
    # A merged change is shared history - no automated rollback.
    return _raises(
        lambda: rollback_plan(DEMO_REPO, 17, SAFE_BRANCH, merged=True), ValueError
    )


def an_unapproved_repository_is_refused() -> bool:
    # create_plan enforces the exact allowlisted repo, not just the shape.
    return _raises(lambda: create_plan("owner/repo", "wf"), ValueError)


def a_risk_raising_remediation_is_blocked() -> bool:
    # A proposal that would give the agent a destructive tool + sensitive
    # data (still no approval) makes it HIGH risk. verify() must fail it,
    # and require_verified() must then stop GitHub planning.
    bad = RemediationProposal(
        template_id="REQUIRE_HUMAN_APPROVAL",
        agent_name="Billing Agent",
        field_changes={"tools": ["delete_invoice"], "sensitive_data_access": True},
        rationale="failure-injection: raise the risk",
        source_sha256="0" * 64,
    )
    result = verify(ENV, bad)
    return (not result.passed) and _raises(
        lambda: require_verified(result), ValueError
    )


def a_drifted_approval_is_no_longer_current() -> bool:
    source_hash = sha256_value(ENV)
    proposal = build_proposal("REQUIRE_HUMAN_APPROVAL", ENV["agents"][0], source_hash)
    proposal_hash = sha256_value(proposal.to_dict())
    record = decide("wf", proposal_hash, source_hash, "Reviewer", "APPROVE", "reviewed")

    drifted_hash = sha256_value({**ENV, "environment_name": "Changed After Sign-off"})
    return approval_is_current(record, proposal_hash, source_hash) and not approval_is_current(
        record, proposal_hash, drifted_hash
    )


def a_broken_gh_stops_with_no_partial_continuation() -> bool:
    calls: list[list[str]] = []

    def fake_run(args, **kwargs):
        calls.append(list(args))
        if "push" in args:  # command 4 of 5: `git push -u origin <branch>`
            raise subprocess.CalledProcessError(
                1, list(args), stderr="fatal: Authentication failed for GitHub"
            )
        return subprocess.CompletedProcess(list(args), 0, stdout="", stderr="")

    plan = create_plan(DEMO_REPO, "wf")
    with patch("subprocess.run", fake_run):
        stopped = _raises(
            lambda: execute_plan(plan, live=True), subprocess.CalledProcessError
        )

    # checkout/add/commit/push were attempted (4); `gh pr create` (5th) was not.
    return stopped and len(calls) == 4 and not any("gh" in call for call in calls)


def a_dry_run_never_shells_out() -> bool:
    shelled: list[int] = []

    def boom(*args, **kwargs):
        shelled.append(1)
        raise AssertionError("dry run must not call subprocess")

    plan = create_plan(DEMO_REPO, "wf")
    with patch("subprocess.run", boom):
        rows = execute_plan(plan)  # no live= -> dry run

    return not shelled and all(row["status"] == "DRY_RUN" for row in rows)


def a_failed_run_is_recorded_as_a_terminal_state() -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "audit.db"
        ended = record_terminal_state(
            db,
            WorkflowState("wf", "VERIFIED"),
            "FAILED",
            reason="failure-injection: github command failed",
            details={"stage": "github"},
        )
        rows = list_events(db, "wf")

    return (
        ended.state == "FAILED"
        and len(rows) == 1
        and rows[0]["event_type"] == "workflow_failed"
        and rows[0]["payload"]["reason"] == "failure-injection: github command failed"
    )


def no_plan_has_merge_force_or_non_agentguard_push() -> bool:
    forbidden = {
        "merge", "--merge", "rebase", "--auto", "--force", "-f",
        "reset", "--hard", "--web", "-w", "ready",
    }
    plan = create_plan(DEMO_REPO, "wf")
    flat = [token for command in plan.commands for token in command]
    pushes = [c for c in plan.commands if tuple(c[:2]) == ("git", "push")]

    return (
        forbidden.isdisjoint(flat)
        and len(pushes) == 1
        and pushes[0][-1].startswith("agentguard/")
    )


# --- positive controls: each returns True when the good path still works --


def a_valid_remediation_verifies_and_reaches_a_plan() -> bool:
    good = build_proposal("REQUIRE_HUMAN_APPROVAL", ENV["agents"][0], sha256_value(ENV))
    result = require_verified(verify(ENV, good))  # returns iff it passed
    plan = create_plan(DEMO_REPO, "wf")
    return result.passed and len(plan.commands) == 5


CHECKS = [
    ("state-skipping is refused", state_skipping_is_refused),
    ("rollback after merge is refused", rollback_after_merge_is_refused),
    ("an unapproved repository is refused", an_unapproved_repository_is_refused),
    ("a risk-raising remediation is blocked before planning", a_risk_raising_remediation_is_blocked),
    ("a drifted approval is no longer current", a_drifted_approval_is_no_longer_current),
    ("a broken gh stops the run with no partial continuation", a_broken_gh_stops_with_no_partial_continuation),
    ("a dry run never shells out", a_dry_run_never_shells_out),
    ("a failed run is recorded as a terminal state", a_failed_run_is_recorded_as_a_terminal_state),
    ("no plan has merge / --force / a non-agentguard push", no_plan_has_merge_force_or_non_agentguard_push),
    ("[control] a valid remediation verifies and reaches a plan", a_valid_remediation_verifies_and_reaches_a_plan),
]


def main() -> None:
    print("=== AgentGuard v4 Failure-Injection Evaluation ===\n")
    results = [(name, bool(fn())) for name, fn in CHECKS]
    for name, passed in results:
        print(f"{'PASS' if passed else 'FAIL'}: {name}")

    failed = [name for name, passed in results if not passed]
    if failed:
        raise SystemExit(
            f"\nV4 FAILURE-INJECTION EVAL FAILED: "
            f"{len(failed)} of {len(results)} checks did not hold - {failed}"
        )
    print(
        f"\nV4 FAILURE-INJECTION EVAL PASS: "
        f"{len(results)} of {len(results)} checks held (fails closed)"
    )


if __name__ == "__main__":
    main()
