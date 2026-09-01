"""Tests for github_plan.py.

Day 2 Lab 6: the branch rule + PR template.
Day 7 Lab 1: the repository / branch / file-path allowlist.
Day 7 Lab 2: the GitHubPlan data contract.
create_plan / execute_plan / rollback are Day 7 Lab 3+ / Day 8.
"""

import json
import subprocess
from dataclasses import FrozenInstanceError

import pytest

import github_plan
from github_plan import GitHubPlan, create_plan, execute_plan


# --- branch naming rule --------------------------------------------------

def test_branch_name_uses_the_agentguard_prefix_and_lowercases():
    assert github_plan.branch_name("ABC123") == "agentguard/abc123"
    assert github_plan.branch_name("wf-9f2a1c") == "agentguard/wf-9f2a1c"


@pytest.mark.parametrize(
    "bad_id",
    [
        "",                       # empty
        "../evil",                # path traversal characters
        "wf/123",                 # slash
        "wf 123",                 # space
        "wf_123",                 # underscore not allowed by the pattern
        "x" * 61,                 # over the 60-char bound
        "wf$(rm -rf)",            # shell metacharacters
    ],
)
def test_branch_name_rejects_unsafe_ids(bad_id):
    with pytest.raises(ValueError):
        github_plan.branch_name(bad_id)


def test_branch_name_of_a_plain_word_id_is_still_safely_prefixed():
    # A workflow id like "main" can never yield a bare `main` branch - it is
    # always prepended with `agentguard/`.
    assert github_plan.branch_name("main") == "agentguard/main"


def test_safe_branch_regex_blocks_main_and_paths_and_uppercase():
    assert github_plan.SAFE_BRANCH.fullmatch("agentguard/wf-12ab")
    assert not github_plan.SAFE_BRANCH.fullmatch("main")
    assert not github_plan.SAFE_BRANCH.fullmatch("agentguard/")
    assert not github_plan.SAFE_BRANCH.fullmatch("agentguard/UPPER")
    assert not github_plan.SAFE_BRANCH.fullmatch("agentguard/wf/nested")
    assert not github_plan.SAFE_BRANCH.fullmatch("release/agentguard/wf")


# --- pull request template --------------------------------------------------

def test_pr_title_is_the_fixed_shape():
    assert github_plan.pr_title("abc123") == "AgentGuard remediation abc123"


def _sample_fields():
    return dict(
        workflow_id="abc123",
        template_id="REQUIRE_HUMAN_APPROVAL",
        agent_name="Customer Support Agent",
        finding="AG-003 human approval not required",
        predicted_score="0",
        source_sha256="a" * 64,
        proposal_sha256="b" * 64,
    )


def test_pr_body_has_every_review_field_and_the_fixed_footer():
    body = github_plan.render_pr_body(**_sample_fields())
    lower = body.lower()
    for label in ("workflow id", "template", "target agent", "finding addressed",
                  "predicted risk score", "source environment sha-256",
                  "proposal sha-256"):
        assert label in lower
    # the fixed footer: always a draft, no merge capability, synthetic
    assert "draft" in lower
    assert "no merge capability" in lower
    assert "synthetic" in lower
    # the supplied values are actually substituted
    assert "abc123" in body
    assert "Customer Support Agent" in body


def test_pr_body_requires_every_field():
    fields = _sample_fields()
    del fields["source_sha256"]
    with pytest.raises(KeyError):
        github_plan.render_pr_body(**fields)


# --- Day 7 Lab 1: the GitHub allowlist -------------------------------------

DEMO_REPO = "justintinlei/agentguard-remediation-demo"
DEMO_FILE = "connected_environment/agents.json"


def test_the_allowlist_constants_are_frozensets_with_the_expected_values():
    assert isinstance(github_plan.ALLOWLISTED_REPOSITORIES, frozenset)
    assert github_plan.ALLOWLISTED_REPOSITORIES == {DEMO_REPO}
    assert isinstance(github_plan.ALLOWLISTED_FILE_PATHS, frozenset)
    assert github_plan.ALLOWLISTED_FILE_PATHS == {DEMO_FILE}


# repository ---------------------------------------------------------------

def test_require_allowlisted_repository_accepts_the_demo_repo():
    assert github_plan.require_allowlisted_repository(DEMO_REPO) == DEMO_REPO


@pytest.mark.parametrize("repo", ["owner/repo", "justintinlei/other-repo", "octocat/hello-world"])
def test_a_well_shaped_but_unlisted_repo_is_rejected(repo):
    with pytest.raises(ValueError, match="not allowlisted"):
        github_plan.require_allowlisted_repository(repo)


@pytest.mark.parametrize(
    "repo",
    [
        "no-slash",
        "a/b/c",
        "owner /repo",
        "owner/repo; rm -rf ~",
        "owner/$(id)",
        "owner/repo && curl evil",
        "owner/repo\nmalicious",
        "owner/`whoami`",
    ],
)
def test_a_malformed_repo_is_rejected_on_shape(repo):
    with pytest.raises(ValueError, match="OWNER/REPO"):
        github_plan.require_allowlisted_repository(repo)


# branch -----------------------------------------------------------------------

def test_require_allowlisted_branch_accepts_an_agentguard_branch():
    assert github_plan.require_allowlisted_branch("agentguard/wf-9f2a1c") == "agentguard/wf-9f2a1c"


@pytest.mark.parametrize(
    "branch",
    ["main", "agentguard/", "agentguard/UPPER", "release/agentguard/x", "agentguard/wf/nested", "agentguard/" + "x" * 61],
)
def test_a_non_agentguard_branch_is_rejected(branch):
    with pytest.raises(ValueError):
        github_plan.require_allowlisted_branch(branch)


# file path ------------------------------------------------------------------

def test_require_allowlisted_file_path_accepts_the_demo_file():
    assert github_plan.require_allowlisted_file_path(DEMO_FILE) == DEMO_FILE


@pytest.mark.parametrize(
    "path",
    ["README.md", "../../etc/passwd", ".github/workflows/deploy.yml", "/connected_environment/agents.json", "connected_environment/agents.json "],
)
def test_a_non_allowlisted_file_path_is_rejected(path):
    with pytest.raises(ValueError, match="not allowlisted"):
        github_plan.require_allowlisted_file_path(path)


# non-string inputs ----------------------------------------------------------

@pytest.mark.parametrize(
    "validator",
    [
        github_plan.require_allowlisted_repository,
        github_plan.require_allowlisted_branch,
        github_plan.require_allowlisted_file_path,
    ],
)
@pytest.mark.parametrize("value", [None, 123, ["owner/repo"]])
def test_validators_reject_non_strings_with_valueerror(validator, value):
    with pytest.raises(ValueError):
        validator(value)


# --- Day 7 Lab 2: the GitHubPlan data contract ----------------------------

BRANCH = "agentguard/wf-9f2a1c"
TITLE = "AgentGuard remediation wf-9f2a1c"


def _plan(**overrides) -> GitHubPlan:
    fields = dict(repository=DEMO_REPO, branch=BRANCH, file_path=DEMO_FILE, title=TITLE)
    fields.update(overrides)
    return GitHubPlan(**fields)


def test_a_valid_plan_holds_its_fields_and_starts_with_no_commands():
    plan = _plan()
    assert plan.repository == DEMO_REPO
    assert plan.branch == BRANCH
    assert plan.file_path == DEMO_FILE
    assert plan.title == TITLE
    assert plan.commands == ()


def test_commands_are_normalised_to_a_tuple_of_tuples():
    plan = _plan(commands=[["git", "checkout", "-b", BRANCH], ["git", "add", DEMO_FILE]])
    assert plan.commands == (
        ("git", "checkout", "-b", BRANCH),
        ("git", "add", DEMO_FILE),
    )


def test_to_dict_has_the_five_keys_and_is_json_serialisable():
    plan = _plan(commands=[["git", "status"]])
    as_dict = plan.to_dict()
    assert set(as_dict) == {"repository", "branch", "file_path", "title", "commands"}
    json.dumps(as_dict)  # must not raise


def test_a_plan_is_frozen():
    plan = _plan()
    with pytest.raises(FrozenInstanceError):
        plan.repository = "someone/else"


def test_mutating_the_passed_in_command_list_does_not_change_the_plan():
    commands = [["git", "add", DEMO_FILE]]
    plan = _plan(commands=commands)
    commands[0].append("--force")
    commands.append(["gh", "pr", "merge"])
    assert plan.commands == (("git", "add", DEMO_FILE),)


@pytest.mark.parametrize(
    "overrides",
    [
        {"repository": "owner/repo"},              # off-allowlist repo
        {"repository": "owner/repo; rm -rf ~"},    # injection shape
        {"branch": "main"},                        # not an agentguard/ branch
        {"branch": "agentguard/UPPER"},
        {"file_path": "README.md"},                # off-allowlist file
        {"title": "   "},                          # blank title
        {"title": 123},                            # non-string title
    ],
)
def test_an_invalid_field_makes_the_plan_unconstructable(overrides):
    with pytest.raises(ValueError):
        _plan(**overrides)


@pytest.mark.parametrize(
    "bad_commands",
    [
        ["git checkout -b x"],          # a bare string, not a token list
        [[]],                           # an empty command
        [["git", "", "add"]],           # an empty token
        [["git", 3, "add"]],            # a non-string token
        [{"git": "add"}],               # not a sequence
    ],
)
def test_a_malformed_command_makes_the_plan_unconstructable(bad_commands):
    with pytest.raises(ValueError):
        _plan(commands=bad_commands)


# --- Day 7 Lab 3: safe branch and commit commands -------------------------

WF = "wf-9f2a1c"
WF_BRANCH = "agentguard/wf-9f2a1c"


def test_create_plan_fills_the_fields_from_the_workflow_id():
    plan = create_plan(DEMO_REPO, WF)
    assert isinstance(plan, GitHubPlan)
    assert plan.repository == DEMO_REPO
    assert plan.branch == WF_BRANCH
    assert plan.file_path == DEMO_FILE          # default
    assert plan.title == "AgentGuard remediation wf-9f2a1c"


def test_create_plan_builds_the_four_git_commands_then_the_draft_pr_command():
    plan = create_plan(DEMO_REPO, WF)
    assert plan.commands == (
        ("git", "checkout", "-b", WF_BRANCH),
        ("git", "add", DEMO_FILE),
        ("git", "commit", "-m", "AgentGuard remediation wf-9f2a1c"),
        ("git", "push", "-u", "origin", WF_BRANCH),
        ("gh", "pr", "create", "--draft", "--repo", DEMO_REPO,
         "--title", "AgentGuard remediation wf-9f2a1c", "--body-file", github_plan.PR_BODY_PATH),
    )


def test_the_first_four_are_git_and_the_last_is_gh_pr_create():
    plan = create_plan(DEMO_REPO, WF)
    assert [c[0] for c in plan.commands[:4]] == ["git"] * 4
    assert plan.commands[-1][:3] == ("gh", "pr", "create")


def test_git_add_stages_only_the_one_file_never_a_wildcard():
    plan = create_plan(DEMO_REPO, WF)
    (add_command,) = [c for c in plan.commands if c[:2] == ("git", "add")]
    assert add_command == ("git", "add", DEMO_FILE)
    assert "." not in add_command
    assert "-A" not in add_command and "--all" not in add_command


def test_no_command_can_touch_main():
    plan = create_plan(DEMO_REPO, WF)
    tokens = [token for command in plan.commands for token in command]
    for forbidden in ("main", "master", "merge", "--force", "-f", "reset"):
        assert forbidden not in tokens
    assert ("git", "push", "-u", "origin", "main") not in plan.commands


def test_the_branch_appears_only_in_checkout_and_push():
    plan = create_plan(DEMO_REPO, WF)
    using_branch = [c for c in plan.commands if WF_BRANCH in c]
    assert [c[1] for c in using_branch] == ["checkout", "push"]


def test_the_workflow_id_is_lowercased_into_the_branch():
    plan = create_plan(DEMO_REPO, "WF-ABC")
    assert plan.branch == "agentguard/wf-abc"


@pytest.mark.parametrize("bad_id", ["", "wf 123", "wf/123", "wf_123", "x" * 61])
def test_create_plan_rejects_an_unsafe_workflow_id(bad_id):
    with pytest.raises(ValueError):
        create_plan(DEMO_REPO, bad_id)


def test_create_plan_rejects_an_off_allowlist_repository():
    with pytest.raises(ValueError):
        create_plan("owner/repo", WF)


def test_create_plan_rejects_an_off_allowlist_file_path():
    with pytest.raises(ValueError):
        create_plan(DEMO_REPO, WF, "README.md")


# --- Day 7 Lab 4: the draft PR command -----------------------------------

TITLE = "AgentGuard remediation wf-9f2a1c"


def _pr_command():
    return create_plan(DEMO_REPO, WF).commands[-1]


def test_the_last_command_is_the_exact_draft_pr_command():
    assert _pr_command() == (
        "gh", "pr", "create", "--draft",
        "--repo", DEMO_REPO,
        "--title", TITLE,
        "--body-file", github_plan.PR_BODY_PATH,
    )


def test_the_pr_command_is_marked_draft_before_the_repo_is_named():
    command = _pr_command()
    assert "--draft" in command
    assert command.index("--draft") < command.index("--repo")


def test_the_pr_command_flags_carry_the_expected_values():
    command = _pr_command()
    assert command[command.index("--repo") + 1] == DEMO_REPO
    assert command[command.index("--title") + 1] == TITLE
    assert command[command.index("--body-file") + 1] == github_plan.PR_BODY_PATH


def test_the_pr_command_has_no_auto_merge_or_web_flags():
    command = _pr_command()
    for forbidden in ("--auto", "merge", "-w", "--web", "--fill"):
        assert forbidden not in command


def test_the_pr_body_file_is_never_staged_by_git_add():
    assert github_plan.PR_BODY_PATH == ".agentguard/pr_body.md"
    plan = create_plan(DEMO_REPO, WF)
    add_commands = [c for c in plan.commands if c[:2] == ("git", "add")]
    for command in add_commands:
        assert github_plan.PR_BODY_PATH not in command


def test_the_draft_pr_command_still_cannot_touch_main():
    tokens = [t for command in create_plan(DEMO_REPO, WF).commands for t in command]
    for forbidden in ("main", "master", "merge", "--force", "-f", "reset", "--auto"):
        assert forbidden not in tokens


# --- Day 7 Lab 5: dry-run is the default ---------------------------------


def test_execute_plan_defaults_to_dry_run_and_lists_every_command():
    plan = create_plan(DEMO_REPO, WF)
    results = execute_plan(plan)
    assert [r["command"] for r in results] == [list(c) for c in plan.commands]
    assert all(r["status"] == "DRY_RUN" for r in results)
    assert all(set(r) == {"command", "status"} for r in results)


def test_live_false_is_the_same_as_the_default():
    plan = create_plan(DEMO_REPO, WF)
    assert execute_plan(plan, live=False) == execute_plan(plan)


def test_no_result_is_marked_executed_in_a_dry_run():
    results = execute_plan(create_plan(DEMO_REPO, WF))
    assert not any(r["status"] == "EXECUTED" for r in results)


def test_the_dry_run_result_is_json_serialisable():
    json.dumps(execute_plan(create_plan(DEMO_REPO, WF)))


def test_a_dry_run_never_shells_out(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("subprocess.run must not be called in a dry run")

    monkeypatch.setattr(subprocess, "run", boom)
    results = execute_plan(create_plan(DEMO_REPO, WF))
    assert all(r["status"] == "DRY_RUN" for r in results)


def test_the_draft_pr_command_is_just_another_dry_run_entry():
    results = execute_plan(create_plan(DEMO_REPO, WF))
    pr_entry = results[-1]
    assert pr_entry["command"][:3] == ["gh", "pr", "create"]
    assert pr_entry["status"] == "DRY_RUN"


# --- Day 7 Lab 6: explicit opt-in live execution -------------------------
#
# EVERY test here monkeypatches subprocess.run - a real live run would
# create a branch / commit / push in this repo.


class _FakeRun:
    """Records calls and returns a successful CompletedProcess."""

    def __init__(self, fail_on=None):
        self.calls = []
        self.fail_on = fail_on  # 1-based call index to raise on, or None

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self.fail_on is not None and len(self.calls) == self.fail_on:
            raise subprocess.CalledProcessError(1, args[0])
        return subprocess.CompletedProcess(args[0], 0, stdout="ok\n", stderr="")


def test_live_true_runs_every_command_and_marks_it_executed(monkeypatch):
    fake = _FakeRun()
    monkeypatch.setattr(subprocess, "run", fake)
    plan = create_plan(DEMO_REPO, WF)

    results = execute_plan(plan, live=True)

    assert [r["command"] for r in results] == [list(c) for c in plan.commands]
    assert all(r["status"] == "EXECUTED" for r in results)
    assert all(r["stdout"] == "ok" for r in results)


def test_live_true_calls_subprocess_once_per_command_in_order(monkeypatch):
    fake = _FakeRun()
    monkeypatch.setattr(subprocess, "run", fake)
    plan = create_plan(DEMO_REPO, WF)

    execute_plan(plan, live=True)

    assert [call[0][0] for call in fake.calls] == [list(c) for c in plan.commands]


def test_live_execution_never_uses_a_shell(monkeypatch):
    fake = _FakeRun()
    monkeypatch.setattr(subprocess, "run", fake)
    execute_plan(create_plan(DEMO_REPO, WF), live=True)

    for _args, kwargs in fake.calls:
        assert not kwargs.get("shell")
        assert kwargs.get("check") is True
        assert kwargs.get("capture_output") is True


def test_live_is_keyword_only(monkeypatch):
    monkeypatch.setattr(subprocess, "run", _FakeRun())
    with pytest.raises(TypeError):
        execute_plan(create_plan(DEMO_REPO, WF), True)


def test_live_execution_stops_at_the_first_failed_command(monkeypatch):
    fake = _FakeRun(fail_on=2)
    monkeypatch.setattr(subprocess, "run", fake)

    with pytest.raises(subprocess.CalledProcessError):
        execute_plan(create_plan(DEMO_REPO, WF), live=True)

    assert len(fake.calls) == 2  # stopped, did not run command 3+


def test_only_live_true_reaches_subprocess(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("subprocess.run reached without live=True")

    monkeypatch.setattr(subprocess, "run", boom)
    # plan generation and a dry run have no action authority:
    plan = create_plan(DEMO_REPO, WF)
    assert all(r["status"] == "DRY_RUN" for r in execute_plan(plan))


# --- Day 7 Lab 7: block unapproved inputs at the command boundary --------
#
# create_plan validates repository, file path, and workflow id BEFORE it
# builds any command token. Nothing unapproved reaches a `git` / `gh`
# argument.

FIXED_TOKENS = {
    "git", "gh", "checkout", "-b", "add", "commit", "-m", "push", "-u",
    "origin", "pr", "create", "--draft", "--repo", "--title", "--body-file",
}


@pytest.mark.parametrize(
    "bad_repo",
    [
        "owner/repo",                               # not the demo repo
        "octocat/hello-world",
        "justintinlei/agentguard-v4",               # the AgentGuard SOURCE repo
        "justintinlei/agentguard-remediation-demos",  # near-miss typo
        "owner/repo; rm -rf ~",
        "owner/$(id)",
        "owner/repo && curl evil",
        "owner/repo\nmalicious",
        "owner/`whoami`",
        "no-slash",
        "a/b/c",
        "",
        "   ",
    ],
)
def test_create_plan_blocks_an_unapproved_repository(bad_repo):
    with pytest.raises(ValueError):
        create_plan(bad_repo, WF)


@pytest.mark.parametrize(
    "bad_id",
    ["", "wf/1", "wf 1", "wf_1", "wf;rm", "../wf", "wf$(x)", "x" * 61],
)
def test_create_plan_blocks_an_unsafe_workflow_id(bad_id):
    with pytest.raises(ValueError):
        create_plan(DEMO_REPO, bad_id)


def test_a_workflow_id_of_main_is_still_a_safe_agentguard_branch():
    # "main" as an id -> branch "agentguard/main"; it is prefixed, so it
    # can never be the real `main`.
    plan = create_plan(DEMO_REPO, "main")
    assert plan.branch == "agentguard/main"


@pytest.mark.parametrize(
    "branch",
    ["main", "master", "feature/x", "agentguard/UPPER", "agentguard/wf/nested", ""],
)
def test_a_githubplan_cannot_hold_an_unapproved_branch(branch):
    with pytest.raises(ValueError):
        GitHubPlan(DEMO_REPO, branch, DEMO_FILE, "t")


def test_a_githubplan_cannot_hold_an_unapproved_repository():
    with pytest.raises(ValueError):
        GitHubPlan("owner/repo", "agentguard/x", DEMO_FILE, "t")


@pytest.mark.parametrize(
    "bad_path",
    [
        "README.md",
        ".github/workflows/deploy.yml",
        "/etc/passwd",
        "../../secrets",
        "connected_environment/agents.json/../../x",
        "connected_environment/agents.json ",      # trailing space
        "Connected_Environment/agents.json",       # wrong case
        "",
    ],
)
def test_create_plan_blocks_an_unapproved_file_path(bad_path):
    with pytest.raises(ValueError):
        create_plan(DEMO_REPO, WF, bad_path)


def test_no_unvalidated_string_can_appear_as_a_command_token():
    plan = create_plan(DEMO_REPO, WF)
    allowed = FIXED_TOKENS | {
        plan.repository, plan.file_path, plan.branch, plan.title, github_plan.PR_BODY_PATH
    }
    for command in plan.commands:
        for token in command:
            assert token in allowed, f"unexpected command token: {token!r}"


def test_valid_inputs_still_produce_a_plan():
    plan = create_plan(DEMO_REPO, WF)
    assert isinstance(plan, GitHubPlan)
    assert plan.repository == DEMO_REPO
    assert plan.branch == WF_BRANCH
    assert plan.file_path == DEMO_FILE


# --- Day 7 Lab 8: draft-only and dry-run guarantees ---------------------
#
# Negative tests: prove the dangerous commands are ABSENT, over a matrix
# of plans - not just one example. NO test here runs `live=True` unmocked.

FORBIDDEN_TOKENS = {
    "merge", "--merge", "rebase", "--auto",
    "--force", "-f", "reset", "--hard",
    "ready", "-w", "--web",
}

FORBIDDEN_COMMANDS = {
    ("git", "push", "-u", "origin", "main"),
    ("git", "push", "origin", "main"),
    ("git", "checkout", "main"),
    ("git", "checkout", "master"),
}

GOOD_IDS = ["wf-1", "wf-9f2a1c", "abc123", "main", "x" * 60]


def _flatten(plan):
    return [token for command in plan.commands for token in command]


def test_the_draft_only_and_dry_run_property():
    # The starter's canonical Day 7 assertion.
    plan = create_plan(DEMO_REPO, "abc123")
    flattened = _flatten(plan)
    assert "--draft" in flattened
    assert "merge" not in flattened
    assert all(row["status"] == "DRY_RUN" for row in execute_plan(plan))


@pytest.mark.parametrize("workflow_id", GOOD_IDS)
def test_no_plan_contains_a_forbidden_token(workflow_id):
    tokens = set(_flatten(create_plan(DEMO_REPO, workflow_id)))
    assert tokens & FORBIDDEN_TOKENS == set()


@pytest.mark.parametrize("workflow_id", GOOD_IDS)
def test_no_plan_contains_a_forbidden_command(workflow_id):
    for command in create_plan(DEMO_REPO, workflow_id).commands:
        assert command not in FORBIDDEN_COMMANDS
        assert command[:3] != ("gh", "pr", "merge")
        assert command[:3] != ("gh", "pr", "ready")


@pytest.mark.parametrize("workflow_id", GOOD_IDS)
def test_every_plan_has_one_gh_command_and_it_is_a_draft_pr_create(workflow_id):
    commands = create_plan(DEMO_REPO, workflow_id).commands
    gh_commands = [c for c in commands if c[0] == "gh"]
    assert len(gh_commands) == 1
    assert gh_commands[0][:3] == ("gh", "pr", "create")
    assert "--draft" in gh_commands[0]


@pytest.mark.parametrize("workflow_id", GOOD_IDS)
def test_every_plan_is_the_same_five_commands_in_the_same_order(workflow_id):
    commands = create_plan(DEMO_REPO, workflow_id).commands
    assert len(commands) == 5
    assert [c[:2] for c in commands] == [
        ("git", "checkout"),
        ("git", "add"),
        ("git", "commit"),
        ("git", "push"),
        ("gh", "pr"),
    ]


def test_the_only_push_targets_the_feature_branch():
    plan = create_plan(DEMO_REPO, WF)
    (push,) = [c for c in plan.commands if c[:2] == ("git", "push")]
    assert push[-1] == plan.branch
    assert plan.branch.startswith("agentguard/")
    assert push[-1] not in ("main", "master", "HEAD")


def test_the_only_checkout_creates_the_feature_branch():
    plan = create_plan(DEMO_REPO, WF)
    (checkout,) = [c for c in plan.commands if c[:2] == ("git", "checkout")]
    assert checkout == ("git", "checkout", "-b", plan.branch)


def test_the_default_dry_run_is_side_effect_free(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("subprocess.run must not run in a dry run")

    monkeypatch.setattr(subprocess, "run", boom)
    plan = create_plan(DEMO_REPO, WF)
    for _ in range(5):
        assert all(row["status"] == "DRY_RUN" for row in execute_plan(plan))


def test_the_dry_run_output_still_shows_the_draft_flag():
    rows = execute_plan(create_plan(DEMO_REPO, WF))
    assert "--draft" in rows[-1]["command"]


def test_live_execution_requires_the_named_keyword():
    with pytest.raises(TypeError):
        execute_plan(create_plan(DEMO_REPO, WF), True)


# --- Day 10 Lab 3: write the PR body file for a live draft PR -----------
#
# create_plan names `.agentguard/pr_body.md` in the `gh pr create
# --body-file` command, but nothing wrote that file. write_pr_body()
# does - into a caller-named directory (the demo-repo working tree), just
# before a live run. No test here runs git / gh.


def _body_fields():
    return dict(
        workflow_id="wf-9f2a1c",
        template_id="REQUIRE_HUMAN_APPROVAL",
        agent_name="Customer Support Agent",
        finding="AG-002 destructive tool without human approval",
        predicted_score="10",
        source_sha256="a" * 64,
        proposal_sha256="b" * 64,
    )


def test_write_pr_body_writes_the_rendered_body_at_the_constant_path(tmp_path):
    path = github_plan.write_pr_body(tmp_path, **_body_fields())
    assert path == tmp_path / github_plan.PR_BODY_PATH
    assert path.read_text(encoding="utf-8") == github_plan.render_pr_body(**_body_fields())


def test_write_pr_body_creates_the_agentguard_directory(tmp_path):
    assert not (tmp_path / ".agentguard").exists()
    github_plan.write_pr_body(tmp_path, **_body_fields())
    assert (tmp_path / ".agentguard").is_dir()


def test_write_pr_body_overwrites_a_stale_body(tmp_path):
    github_plan.write_pr_body(tmp_path, **_body_fields())
    path = github_plan.write_pr_body(
        tmp_path, **{**_body_fields(), "agent_name": "Deployment Agent"}
    )
    body = path.read_text(encoding="utf-8")
    assert "Deployment Agent" in body
    assert "Customer Support Agent" not in body


def test_write_pr_body_requires_every_field_before_writing_anything(tmp_path):
    fields = _body_fields()
    del fields["proposal_sha256"]
    with pytest.raises(KeyError):
        github_plan.write_pr_body(tmp_path, **fields)
    assert not (tmp_path / ".agentguard").exists()  # nothing was written


def test_write_pr_body_keeps_the_fixed_draft_no_merge_synthetic_footer(tmp_path):
    body = github_plan.write_pr_body(tmp_path, **_body_fields()).read_text(encoding="utf-8")
    lower = body.lower()
    assert "draft" in lower
    assert "no merge capability" in lower
    assert "synthetic" in lower


def test_write_pr_body_has_no_default_directory():
    # The caller must name the target dir, so this can never write into the
    # AgentGuard source repo by accident.
    with pytest.raises(TypeError):
        github_plan.write_pr_body(**_body_fields())
