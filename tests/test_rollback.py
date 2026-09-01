"""Tests for rollback.py.

Day 8 Lab 2: the pre-merge rollback command plan - close the draft PR,
delete its feature branch. rollback_plan() returns command token-lists
for review and runs nothing.

Day 8 Lab 3: rollback_plan() now requires a keyword-only ``merged`` flag;
``merged=True`` refuses (a merged change needs a reviewed revert, not an
automated rewrite).
"""

import pytest

import rollback
from audit_db import list_events
from rollback import ROLLBACK_COMMENT, rollback_plan
from workflow import WorkflowState, record_terminal_state

REPO = "justintinlei/agentguard-remediation-demo"
BRANCH = "agentguard/workflow-17"

# Tokens that must never appear in a rollback command: a merge, a forced
# update, a history rewrite, an auto-merge. Pre-merge rollback is only a
# PR close + a branch delete.
FORBIDDEN_TOKENS = {
    "merge", "--merge", "rebase", "--auto", "--force", "-f",
    "reset", "--hard", "revert", "checkout", "-w", "--web", "ready",
}

# The Lab 2 plan shape, unchanged by Lab 3 for the unmerged path.
EXPECTED_PLAN = [
    ["gh", "pr", "close", "17", "--repo", REPO, "--comment", ROLLBACK_COMMENT],
    ["git", "push", "origin", "--delete", BRANCH],
]


# --- happy path (unmerged) ---------------------------------------------

def test_plan_is_exactly_close_then_delete_branch():
    assert rollback_plan(REPO, 17, BRANCH, merged=False) == EXPECTED_PLAN


def test_plan_has_two_commands():
    assert len(rollback_plan(REPO, 17, BRANCH, merged=False)) == 2


def test_pr_number_is_rendered_as_a_string_token():
    close_cmd = rollback_plan(REPO, 42, BRANCH, merged=False)[0]
    assert "42" in close_cmd
    assert 42 not in close_cmd


def test_close_command_names_the_repo_and_the_fixed_comment():
    plan = rollback_plan(REPO, 17, BRANCH, merged=False)
    close_cmd = plan[0]
    assert close_cmd[:3] == ["gh", "pr", "close"]
    assert close_cmd[close_cmd.index("--repo") + 1] == REPO
    assert close_cmd[close_cmd.index("--comment") + 1] == ROLLBACK_COMMENT


# --- safety: no forbidden token, branch delete only ------------------

def test_no_forbidden_token_in_any_command():
    flat = [t for command in rollback_plan(REPO, 17, BRANCH, merged=False) for t in command]
    assert FORBIDDEN_TOKENS.isdisjoint(flat)


def test_branch_delete_targets_the_agentguard_branch_never_main():
    delete_cmd = rollback_plan(REPO, 17, BRANCH, merged=False)[1]
    assert delete_cmd == ["git", "push", "origin", "--delete", BRANCH]
    assert delete_cmd[-1].startswith("agentguard/")
    assert delete_cmd[-1] not in {"main", "master", "HEAD"}


def test_only_git_command_is_a_branch_delete_push():
    git_cmds = [c for c in rollback_plan(REPO, 17, BRANCH, merged=False) if c[0] == "git"]
    assert git_cmds == [["git", "push", "origin", "--delete", BRANCH]]


# --- input validation ------------------------------------------------

@pytest.mark.parametrize(
    "bad_repo",
    [
        "owner/repo",                       # OWNER/REPO shaped but not allowlisted
        "justintinlei/some-other-repo",     # right owner, wrong repo
        "not a safe repo value",            # spaces / not OWNER/REPO shaped
        "justintinlei/demo; rm -rf /",      # shell metacharacters
        "",                                 # empty
    ],
)
def test_unapproved_repository_is_blocked(bad_repo):
    with pytest.raises(ValueError):
        rollback_plan(bad_repo, 17, BRANCH, merged=False)


@pytest.mark.parametrize(
    "bad_branch",
    [
        "main",                     # never delete main
        "master",
        "agentguard/UPPER",         # uppercase not allowed by the pattern
        "agentguard/wf/nested",     # nested slash
        "release/agentguard/wf",    # wrong prefix
        "agentguard/",              # empty id part
        "agentguard/wf 17",         # space
        "",                         # empty
    ],
)
def test_unapproved_branch_is_blocked(bad_branch):
    with pytest.raises(ValueError):
        rollback_plan(REPO, 17, bad_branch, merged=False)


@pytest.mark.parametrize("bad_number", [0, -1, "17", 3.0, True, None])
def test_bad_pr_number_is_blocked(bad_number):
    with pytest.raises(ValueError, match="positive integer"):
        rollback_plan(REPO, bad_number, BRANCH, merged=False)


# --- Day 8 Lab 3: refuse rollback after merge -----------------------

def test_merged_pull_request_refuses_automatic_rollback():
    with pytest.raises(ValueError, match="refused after merge"):
        rollback_plan(REPO, 17, BRANCH, merged=True)


def test_refusal_message_points_to_a_reviewed_revert():
    with pytest.raises(ValueError, match="reviewed revert workflow"):
        rollback_plan(REPO, 17, BRANCH, merged=True)


def test_merged_true_refuses_even_with_fully_valid_inputs():
    # repo, branch and pr_number are all valid here - merge state alone refuses.
    with pytest.raises(ValueError, match="refused after merge"):
        rollback_plan(REPO, 1, "agentguard/x", merged=True)


def test_merged_true_produces_no_command():
    result = None
    try:
        result = rollback_plan(REPO, 17, BRANCH, merged=True)
    except ValueError:
        pass
    assert result is None


def test_merged_is_keyword_only():
    # Positional 4th arg is a TypeError - you must type merged=...
    with pytest.raises(TypeError):
        rollback_plan(REPO, 17, BRANCH, True)


def test_merged_is_required():
    with pytest.raises(TypeError):
        rollback_plan(REPO, 17, BRANCH)


@pytest.mark.parametrize("not_a_bool", ["yes", "false", 1, 0, None, []])
def test_merged_must_be_a_bool(not_a_bool):
    with pytest.raises(ValueError, match="merged must be a bool"):
        rollback_plan(REPO, 17, BRANCH, merged=not_a_bool)


def test_unmerged_path_is_unchanged_by_lab_3():
    # Explicit regression: merged=False still yields the exact Lab 2 plan.
    assert rollback_plan(REPO, 17, BRANCH, merged=False) == EXPECTED_PLAN


# --- purity: the plan is data, not an action -----------------------

def test_rollback_module_never_imports_subprocess():
    assert not hasattr(rollback, "subprocess")


def test_rollback_plan_has_no_side_effects_and_is_repeatable():
    first = rollback_plan(REPO, 17, BRANCH, merged=False)
    second = rollback_plan(REPO, 17, BRANCH, merged=False)
    assert first == second
    # mutating a returned plan does not affect the next call
    first[0][0] = "MUTATED"
    assert rollback_plan(REPO, 17, BRANCH, merged=False)[0][0] == "gh"


# --- Day 8 Lab 4: a completed rollback is recorded as ROLLED_BACK ------

def test_a_completed_rollback_is_recorded_as_rolled_back(tmp_path):
    db = tmp_path / "audit.db"
    state = WorkflowState("wf-1", "DRAFT_PR_CREATED")

    state = record_terminal_state(
        db,
        state,
        "ROLLED_BACK",
        reason="draft PR closed and branch deleted",
        details={"pr_number": 17},
    )

    assert state.state == "ROLLED_BACK"
    (event,) = list_events(db, "wf-1")
    assert event["state"] == "ROLLED_BACK"
    assert event["event_type"] == "workflow_rolled_back"
    assert event["payload"] == {
        "pr_number": 17,
        "reason": "draft PR closed and branch deleted",
    }


def test_the_rollback_plan_and_its_audit_record_are_separate_steps(tmp_path):
    # Building the command plan writes nothing - it takes no db and is pure.
    db = tmp_path / "audit.db"
    plan = rollback_plan(REPO, 17, BRANCH, merged=False)
    assert plan == EXPECTED_PLAN
    assert list_events(db, "wf-1") == []          # plan alone recorded nothing

    # The audit row appears only when the workflow layer records the ending.
    record_terminal_state(
        db, WorkflowState("wf-1", "DRAFT_PR_CREATED"), "ROLLED_BACK",
        reason="rolled back",
    )
    assert [e["event_type"] for e in list_events(db, "wf-1")] == ["workflow_rolled_back"]


# --- Day 10 Lab 4: demonstrate closing the loop on an unmerged draft ---
#
# Everything below is built already (Days 7-8). These tests just walk the
# whole "close the loop safely" path end to end, as one readable story, so
# the demonstration is pinned and not only described in the log.

DEMO_BRANCH = "agentguard/wf-demo01"


def test_close_the_loop_from_draft_pr_to_rolled_back(tmp_path):
    # A draft PR (#7) is open on the demo repo; the workflow is at
    # DRAFT_PR_CREATED. Someone decides to undo it before any merge.
    db = tmp_path / "audit.db"
    state = WorkflowState("wf-demo01", "DRAFT_PR_CREATED")

    # 1. Build the rollback plan - two reversible commands, nothing run.
    plan = rollback_plan(REPO, 7, DEMO_BRANCH, merged=False)
    assert plan == [
        ["gh", "pr", "close", "7", "--repo", REPO, "--comment", ROLLBACK_COMMENT],
        ["git", "push", "origin", "--delete", DEMO_BRANCH],
    ]

    # 2. After a human runs those two commands, the workflow layer records
    #    the ending - the audit trail never goes silent on a rollback.
    state = record_terminal_state(
        db,
        state,
        "ROLLED_BACK",
        reason="draft PR #7 closed and branch deleted",
        details={"pr_number": 7, "branch": DEMO_BRANCH},
    )

    assert state.state == "ROLLED_BACK"
    (event,) = list_events(db, "wf-demo01")
    assert event["event_type"] == "workflow_rolled_back"
    assert event["state"] == "ROLLED_BACK"
    assert event["payload"] == {
        "pr_number": 7,
        "branch": DEMO_BRANCH,
        "reason": "draft PR #7 closed and branch deleted",
    }


def test_once_a_draft_pr_is_open_the_only_recorded_ending_is_rolled_back(tmp_path):
    # The state machine allows exactly one arrow out of DRAFT_PR_CREATED:
    # -> ROLLED_BACK. FAILED / REJECTED endings are not reachable from here,
    # so a draft PR can only ever be closed by a rollback.
    db = tmp_path / "audit.db"

    for wrong_ending in ("FAILED", "REJECTED"):
        with pytest.raises(ValueError):
            record_terminal_state(
                db,
                WorkflowState("wf-demo01", "DRAFT_PR_CREATED"),
                wrong_ending,
                reason="not a legal ending from DRAFT_PR_CREATED",
            )
    assert list_events(db, "wf-demo01") == []  # nothing was written

    ended = record_terminal_state(
        db,
        WorkflowState("wf-demo01", "DRAFT_PR_CREATED"),
        "ROLLED_BACK",
        reason="the one legal ending",
    )
    assert ended.state == "ROLLED_BACK"


def test_rolling_back_a_merged_draft_is_refused_at_the_plan_step():
    # If the PR was already merged, the loop is NOT closed automatically:
    # rollback_plan produces no command at all. A merged change lives in
    # shared history and needs a new reviewed `git revert` PR.
    with pytest.raises(ValueError, match="refused after merge"):
        rollback_plan(REPO, 7, DEMO_BRANCH, merged=True)
