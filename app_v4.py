"""AgentGuard v4 - Governed Remediation MVP. Streamlit page.

This page provides, top to bottom:

  - the safety boundary the whole v4 workflow runs under (BOUNDARY_NOTES)
    and a "GitHub CLI authentication" panel;
  - JOURNEY_STAGES - a read-only MAP of the six stages a remediation
    passes through, in order, with who holds authority at each one;
  - the proposal controls - pick one agent and one allowlisted template,
    click "Build proposal", and see the resulting RemediationProposal
    and its SHA-256. build_ui_proposal() is the pure helper behind it;
  - "Approve & verify" - enter a reviewer + reason, choose APPROVE /
    REJECT, and see the invisible control evidence made visible: the two
    content hashes the approval is bound to, the ApprovalRecord, the
    VerificationResult checklist, and an ordered event timeline.
    approve_and_verify() is the pure helper;
  - for a VERIFIED run only, the GitHub dry-run plan - the exact five
    git/gh commands a live run would execute, their DRY_RUN status, and
    GITHUB_SAFETY_WARNINGS. github_dry_run_plan() is the pure helper.
    The page runs none of the commands - it is a review surface, not a
    trigger.

The auth panel demonstrates a key point: the app can confirm that GitHub
access works *without ever holding a credential itself*. It shells out to
`gh auth status` and reads the summary text; the OAuth token that `gh`
obtained through the browser lives in the OS keyring, outside this repo,
and is never read, displayed, or stored by AgentGuard.

Live GitHub execution is a separate, deliberate command-line step; this
page never runs it. The page's event timeline is held in memory for
display; the durable SQLite audit trail (`audit_db.py`,
`workflow.record_terminal_state`) is exercised by the tests and evals
directly, and wiring it into this page is a documented post-MVP item
(`docs/post_mvp_backlog.md`). `v4_service` / `audit_db` are not imported
here.

Import-safe: render() only runs under `streamlit run app_v4.py` (the
`__main__` guard). A plain `import app_v4` (the tests) just reads the
module-level data and helpers - no Streamlit warnings, no subprocess.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from pathlib import Path

import streamlit as st

from approval import approval_is_current, decide
from github_plan import create_plan, execute_plan
from proposal_hash import sha256_value
from remediation_templates import TEMPLATE_INFO, build_proposal, require_allowlisted
from verifier import require_verified, verify


PAGE_TITLE = "AgentGuard v4 - Governed Remediation MVP"

# The synthetic connected-demo agent inventory. Read-only - the app never
# writes it.
CONNECTED_ENV_PATH = Path(__file__).resolve().parent / "connected_environment" / "agents.json"

# The one allowlisted synthetic demo repository (github_plan.py enforces
# this exact value).
DEMO_REPO = "justintinlei/agentguard-remediation-demo"

# Shown with every GitHub plan. Each line is a guarantee the code
# enforces - see github_plan.create_plan / execute_plan and their tests.
GITHUB_SAFETY_WARNINGS = (
    "Dry run: the commands below are shown, not executed. Nothing is pushed "
    "and no pull request is opened by this page.",
    "The pull request would be a DRAFT - it cannot merge until a human marks "
    "it ready for review.",
    "No command merges, force-pushes, resets, or touches `main`; the only "
    "`git push` targets the `agentguard/` remediation branch.",
    "The target is the dedicated private synthetic demo repository only - "
    "never a production repository.",
    "Live execution is a separate, deliberate opt-in run from the command "
    "line. This page can never run it.",
)

# Stated on the page so a viewer sees the limits before anything else. Every
# item here is a commitment the codebase enforces; see
# docs/v4_github_demo_setup.md and the no-production pledge in
# evidence/README.md.
BOUNDARY_NOTES = (
    "Synthetic demo - synthetic agent data only, no real account or registry.",
    "GitHub execution is dry-run by default and only ever produces a "
    "draft pull request on a dedicated demo repository - never a "
    "production repository, and never a merge.",
    "No GitHub token is stored in this project. `gh` holds it in the OS "
    "keyring; this app only reads `gh auth status`.",
    "v1's scanner.py stays the sole authority for the risk score - a "
    "proposal predicts a score, it never sets one.",
)

# The six stages a remediation passes through, in order. This is the
# read-only MAP shown on the page; the controls below walk a user through
# it. Each stage names what the user does, what
# the system produces, and - the point of the map - who holds authority
# there. The `state` field ties each stage back to workflow.STATES so the
# map cannot drift from the state machine.
JOURNEY_STAGES = (
    {
        "step": 1,
        "name": "Discovery",
        "does": "Load the synthetic agent inventory (read-only) and scan it.",
        "produces": "The agent list, a SHA-256 of the exact source, and v1's risk findings.",
        "authority": "Read-only. v1's scanner.py is the sole authority for the risk score.",
        "state": "DISCOVERED",
    },
    {
        "step": 2,
        "name": "Proposal",
        "does": "Pick one agent and one of the three allowlisted remediation templates.",
        "produces": "A bounded RemediationProposal and its SHA-256.",
        "authority": (
            "Deterministic allowlisted templates only - never a free-form AI patch. "
            "The AI layer may explain or propose, never apply or score."
        ),
        "state": "PROPOSED",
    },
    {
        "step": 3,
        "name": "Approval",
        "does": "A named human enters a reason and records an APPROVE or REJECT decision.",
        "produces": "An ApprovalRecord bound to the proposal hash AND the source hash.",
        "authority": (
            "The human approves intent. No real configuration is touched. "
            "A REJECT ends the workflow - recorded, not dropped."
        ),
        "state": "APPROVED",
    },
    {
        "step": 4,
        "name": "Verification",
        "does": "Apply the approved change to a throwaway copy and re-scan it.",
        "produces": "A VerificationResult - pass/fail plus every check row.",
        "authority": (
            "Software checks correctness. require_verified() blocks a failed result "
            "before any GitHub step. Fail closed -> FAILED."
        ),
        "state": "VERIFIED",
    },
    {
        "step": 5,
        "name": "Plan",
        "does": "Show the exact git/gh commands that would open a draft pull request.",
        "produces": "A GitHubPlan - five commands, dry-run by default.",
        "authority": (
            "Draft PR only, on the one allowlisted demo repo. No merge, no --force, "
            "no main push; a live run needs a separate explicit opt-in."
        ),
        "state": "DRAFT_PR_CREATED",
    },
    {
        "step": 6,
        "name": "Audit",
        "does": "List every step above, in the order it happened.",
        "produces": "Append-only rows in the SQLite workflow_events table.",
        "authority": (
            "Immutable by convention. A rejection, failure, or rollback is recorded "
            "as a terminal event - the trail is never silent."
        ),
        "state": "ROLLED_BACK",
    },
)


# Defensive: `gh auth status` already masks the token, but strip any line
# that mentions one before the text is shown or returned, so a future `gh`
# change can never surface a secret through this panel.
_TOKEN_LINE_MARKER = "Token:"


def _strip_token_lines(text: str) -> str:
    """Drop any line that names a token; keep everything else verbatim."""
    kept = [line for line in text.splitlines() if _TOKEN_LINE_MARKER not in line]
    return "\n".join(kept)


def github_auth_status() -> dict:
    """Report whether `gh` is installed and authenticated.

    Returns a dict with `gh_installed`, `authenticated`, and a `summary`
    string that has been stripped of any token line. Never returns,
    prints, or logs a credential.
    """
    if shutil.which("gh") is None:
        return {
            "gh_installed": False,
            "authenticated": False,
            "summary": "GitHub CLI (`gh`) is not installed. Run `brew install gh`.",
        }

    completed = subprocess.run(
        ["gh", "auth", "status"],
        capture_output=True,
        text=True,
        check=False,
    )
    # `gh auth status` writes its report to stderr on most versions and to
    # stdout on some; join both and let the caller read whatever is there.
    raw = (completed.stdout + completed.stderr).strip()
    return {
        "gh_installed": True,
        "authenticated": completed.returncode == 0,
        "summary": _strip_token_lines(raw),
    }


# --- the proposal controls ----------------------------------------------


def load_environment() -> dict:
    """Read the synthetic connected-demo agent inventory (read-only)."""
    return json.loads(CONNECTED_ENV_PATH.read_text(encoding="utf-8"))


def _proposal_from_selection(
    environment: dict,
    agent_name: str,
    template_id: str,
    owner_value: str | None = None,
):
    """Return ``(RemediationProposal, source_sha256)`` for the selection.

    Raises ``ValueError`` on: a ``template_id`` that is not one of the
    three allowlisted templates (checked before any agent is touched); an
    ``agent_name`` that does not match exactly one agent; or (for
    ``ASSIGN_OWNER``) a missing / over-long / multi-line owner value.
    """
    require_allowlisted(template_id)  # gate the intent before touching an agent
    matches = [
        a for a in environment.get("agents", []) if a.get("agent_name") == agent_name
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one agent named {agent_name!r}; found {len(matches)}."
        )
    source_sha256 = sha256_value(environment)
    proposal = build_proposal(template_id, matches[0], source_sha256, value=owner_value)
    return proposal, source_sha256


def build_ui_proposal(
    environment: dict,
    agent_name: str,
    template_id: str,
    owner_value: str | None = None,
) -> dict:
    """Turn the page's two selections into a proposal and its hashes.

    Returns ``{"proposal": <dict>, "proposal_sha256": <64 hex>,
    "source_sha256": <64 hex>}``; raises ``ValueError`` (see
    ``_proposal_from_selection``) on bad input. Nothing is applied - the
    returned proposal only *describes* one bounded change.
    """
    proposal, source_sha256 = _proposal_from_selection(
        environment, agent_name, template_id, owner_value
    )
    proposal_dict = proposal.to_dict()
    return {
        "proposal": proposal_dict,
        "proposal_sha256": sha256_value(proposal_dict),
        "source_sha256": source_sha256,
    }


def approve_and_verify(
    environment: dict,
    agent_name: str,
    template_id: str,
    reviewer: str,
    reason: str,
    decision: str,
    owner_value: str | None = None,
) -> dict:
    """Run proposal -> human decision -> (on APPROVE) verification, and
    return everything the page needs to *display*.

    Returned dict keys: ``workflow_id``, ``proposal``,
    ``proposal_sha256``, ``source_sha256``, ``approval`` (dict),
    ``approval_current`` (bool), ``verification`` (dict or None),
    ``verification_summary`` (str or None), ``final_state``, and
    ``events`` - an ordered list of ``{step, name, state, detail}``.

    Raises ``ValueError`` only for a bad *input*: an unallowlisted
    template, an agent that is not exactly one match, a malformed owner,
    a ``decision`` that is not exactly ``"APPROVE"`` / ``"REJECT"``, or a
    blank reviewer / reason. A REJECT decision and a failed verification
    are *outcomes* - reported in the returned dict and the timeline,
    never raised, because showing them is the whole point of the page.
    """
    workflow_id = uuid.uuid4().hex[:12]

    proposal, source_sha256 = _proposal_from_selection(
        environment, agent_name, template_id, owner_value
    )
    proposal_dict = proposal.to_dict()
    proposal_sha256 = sha256_value(proposal_dict)

    events = [
        {
            "step": 1,
            "name": "proposal_created",
            "state": "PROPOSED",
            "detail": {
                "template_id": template_id,
                "agent_name": agent_name,
                "field_changes": proposal_dict["field_changes"],
                "proposal_sha256": proposal_sha256,
            },
        }
    ]

    # The human decision. decide() raises ValueError for a bad decision
    # string or a blank reviewer / reason - those are input errors.
    record = decide(workflow_id, proposal_sha256, source_sha256, reviewer, decision, reason)
    approval = record.to_dict()

    if record.decision == "REJECT":
        events.append(
            {
                "step": 2,
                "name": "proposal_rejected",
                "state": "REJECTED",
                "detail": {"reviewer": record.reviewer, "reason": record.reason},
            }
        )
        return {
            "workflow_id": workflow_id,
            "proposal": proposal_dict,
            "proposal_sha256": proposal_sha256,
            "source_sha256": source_sha256,
            "approval": approval,
            "approval_current": False,
            "verification": None,
            "verification_summary": None,
            "final_state": "REJECTED",
            "events": events,
        }

    # approval_is_current re-checks that the recorded APPROVE still binds
    # to exactly this proposal and source (it always does here - the
    # decision was made against the hashes we just computed - but showing
    # the check is the point).
    approval_current = approval_is_current(record, proposal_sha256, source_sha256)
    events.append(
        {
            "step": 2,
            "name": "proposal_approved",
            "state": "APPROVED",
            "detail": {
                "reviewer": record.reviewer,
                "reason": record.reason,
                "bound_proposal_sha256": record.proposal_sha256,
                "bound_source_sha256": record.source_sha256,
                "approval_current": approval_current,
            },
        }
    )

    result = verify(environment, proposal)
    verification = result.to_dict()
    try:
        require_verified(result)
        gate_passed = True
    except ValueError:
        gate_passed = False
    final_state = "VERIFIED" if (gate_passed and approval_current) else "FAILED"
    events.append(
        {
            "step": 3,
            "name": "verification_passed" if final_state == "VERIFIED" else "verification_failed",
            "state": final_state,
            "detail": {
                "passed": result.passed,
                "before_high_count": result.before_high_count,
                "after_high_count": result.after_high_count,
                "failed_checks": [c["name"] for c in result.checks if not c["passed"]],
            },
        }
    )
    return {
        "workflow_id": workflow_id,
        "proposal": proposal_dict,
        "proposal_sha256": proposal_sha256,
        "source_sha256": source_sha256,
        "approval": approval,
        "approval_current": approval_current,
        "verification": verification,
        "verification_summary": result.summary(),
        "final_state": final_state,
        "events": events,
    }


def github_dry_run_plan(workflow_id: str) -> dict:
    """Build the draft-PR plan for a verified remediation and dry-run it.

    Returns ``{"repository", "branch", "file_path", "title",
    "commands": [[token, ...], ...], "dry_run": [{"command", "status"}, ...],
    "warnings": GITHUB_SAFETY_WARNINGS}``.

    Raises ``ValueError`` (from ``create_plan``) if ``workflow_id`` is not
    branch-safe, or the repo / file is not allowlisted. **Nothing runs** -
    the dry-run call only formats the commands for review; the page never
    asks for a real run.
    """
    plan = create_plan(DEMO_REPO, workflow_id)
    return {
        "repository": plan.repository,
        "branch": plan.branch,
        "file_path": plan.file_path,
        "title": plan.title,
        "commands": [list(command) for command in plan.commands],
        "dry_run": execute_plan(plan, live=False),
        "warnings": GITHUB_SAFETY_WARNINGS,
    }


def render() -> None:
    """Draw the whole page. Called only from the __main__ guard below."""
    st.set_page_config(page_title="AgentGuard v4", page_icon="checkmark", layout="wide")
    st.title(PAGE_TITLE)
    st.write(
        "This page shows the safety boundary, the map of the six-stage "
        "remediation journey, the proposal / approval / verification "
        "controls with their evidence, the GitHub dry-run plan for a "
        "verified remediation, and the GitHub CLI authentication state."
    )

    st.subheader("Safety boundary")
    for note in BOUNDARY_NOTES:
        st.markdown(f"- {note}")

    st.subheader("The v4 remediation journey")
    st.write(
        "Every remediation passes through these six stages in order. Each "
        "stage names what happens, what it produces, and - the point of the "
        "map - who holds authority there."
    )
    for stage in JOURNEY_STAGES:
        st.markdown(
            f"**{stage['step']}. {stage['name']}**  \n"
            f"{stage['does']}  \n"
            f"*Produces:* {stage['produces']}  \n"
            f"*Authority / boundary:* {stage['authority']}  \n"
            f"*State machine:* `{stage['state']}`"
        )

    st.subheader("Build a proposal (journey stages 1-2)")
    environment = load_environment()
    st.caption(
        f"Source: {environment.get('environment_name', '?')} - synthetic, read-only."
    )

    agent_name = st.selectbox("Agent", [a["agent_name"] for a in environment["agents"]])
    template_id = st.selectbox("Remediation template", list(TEMPLATE_INFO))
    info = TEMPLATE_INFO[template_id]
    st.caption(f"{info.rationale}  (clears {', '.join(info.addresses)})")

    owner_value = None
    if info.needs_input == "owner":
        owner_value = st.text_input("Owner to assign", "")

    if st.button("Build proposal", type="primary"):
        try:
            st.session_state["v4_proposal"] = build_ui_proposal(
                environment, agent_name, template_id, owner_value
            )
        except ValueError as exc:
            st.session_state.pop("v4_proposal", None)
            st.error(str(exc))

    built = st.session_state.get("v4_proposal")
    if built:
        st.write("**Proposal** - a description of one bounded change, not applied")
        st.json(built["proposal"])
        st.write(f"Proposal SHA-256: `{built['proposal_sha256']}`")
        st.write(f"Source SHA-256: `{built['source_sha256']}`")

    st.subheader("Approve and verify (journey stages 3-4)")
    reviewer = st.text_input("Reviewer name", "")
    reason = st.text_area("Decision reason", "")
    decision = st.radio("Decision", ["APPROVE", "REJECT"], horizontal=True)
    if st.button("Approve & verify", type="primary"):
        try:
            st.session_state["v4_run"] = approve_and_verify(
                environment, agent_name, template_id, reviewer, reason, decision, owner_value
            )
        except ValueError as exc:
            st.session_state.pop("v4_run", None)
            st.error(str(exc))

    run = st.session_state.get("v4_run")
    if run:
        st.markdown(
            "**Content hashes** - what the approval is cryptographically bound to"
        )
        st.code(
            f"proposal SHA-256 : {run['proposal_sha256']}\n"
            f"source   SHA-256 : {run['source_sha256']}",
            language="text",
        )

        st.markdown("**Approval record**")
        st.json(run["approval"])
        st.caption(
            f"Bound to this exact proposal + source; still current: {run['approval_current']}"
        )

        if run["verification"] is not None:
            st.markdown("**Verification** (deterministic, on an isolated copy)")
            st.text(run["verification_summary"])
            v = run["verification"]
            st.caption(
                f"HIGH-risk agents: before {v['before_high_count']} "
                f"-> after {v['after_high_count']}"
            )

        st.markdown("**Event timeline**")
        for event in run["events"]:
            st.markdown(f"{event['step']}. `{event['state']}` - **{event['name']}**")
            st.json(event["detail"])

        if run["final_state"] == "VERIFIED":
            st.subheader("GitHub dry-run plan (journey stage 5)")
            st.warning(
                "Review these commands. This page runs none of them - it is a "
                "review surface, not a trigger."
            )
            for line in GITHUB_SAFETY_WARNINGS:
                st.markdown(f"- {line}")

            plan = github_dry_run_plan(run["workflow_id"])
            st.caption(
                f"Repository `{plan['repository']}`  ·  branch `{plan['branch']}`  "
                f"·  file `{plan['file_path']}`"
            )
            st.markdown("**Commands a live run would execute, in order:**")
            for i, command in enumerate(plan["commands"], start=1):
                st.code(f"{i}. " + " ".join(command), language="bash")
            st.markdown("**Dry run - the status of each command right now:**")
            st.json(plan["dry_run"])
        else:
            st.info(
                f"No GitHub plan: verification did not pass (final state "
                f"**{run['final_state']}**). A plan is only produced for a "
                "VERIFIED remediation."
            )

    st.subheader("GitHub CLI authentication")
    status = github_auth_status()
    if not status["gh_installed"]:
        st.error(status["summary"])
    elif status["authenticated"]:
        st.success("`gh` is authenticated. AgentGuard never sees the token.")
        st.code(status["summary"], language="text")
    else:
        st.warning("`gh` is installed but not authenticated. Run `gh auth login`.")
        st.code(status["summary"], language="text")


# `streamlit run app_v4.py` executes this file as __main__, so the page
# draws. `import app_v4` (the tests) skips render() entirely.
if __name__ == "__main__":
    render()
