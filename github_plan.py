"""GitHub plan helpers for v4 remediation.

Day 2 Lab 6 slice - the *review metadata* that makes every machine-proposed
remediation look the same to a reviewer:

  - branch_name(workflow_id): every remediation branch is `agentguard/<id>`
  - pr_title(workflow_id) / PR_BODY_TEMPLATE: a fixed PR title and body shape

Day 7 Lab 1 slice - the **allowlist**: the exact repository, branch shape,
and file path a machine-proposed change is permitted to touch
(`require_allowlisted_repository/branch/file_path`).

Day 7 Lab 2 slice - the **data contract**: `GitHubPlan`, a frozen record
of a repository, branch, file path, title, and the exact `git`/`gh`
token-lists that would be run. It validates itself, so an invalid plan
cannot be constructed.

Day 7 Lab 3-4, 7 slice - `create_plan()` builds a `GitHubPlan` with the
four `git` commands that isolate a remediation on its own `agentguard/`
branch and never touch `main`, plus a fifth `gh pr create --draft`
command that opens the pull request in review state. It validates the
repository, file path, and workflow id at its entry (Lab 7), so no
unapproved string reaches a command argument.

Day 7 Lab 5-6 slice - `execute_plan()` runs a plan **dry-run by
default**: it returns the exact commands for review and changes nothing.
`live=True` is a separate, deliberate, keyword-only opt-in that actually
runs the commands (Lab 6). `create_plan()` describes; only
`execute_plan(plan, live=True)` acts.

Day 10 Lab 3 slice - `write_pr_body()` writes the `render_pr_body()`
output to `PR_BODY_PATH` inside the checked-out demo-repo working tree,
just before a live run, so `gh pr create --body-file .agentguard/pr_body.md`
has a file to read. It is the last missing piece for the one optional
live draft PR; it still runs no `git` / `gh`.

The only function in this file that touches the network, `gh`, or git is
`execute_plan(plan, live=True)`. Everything else is string formatting,
regex validation, one immutable dataclass, and (Lab 3) one file write.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

# Every remediation branch name must match this exactly (note `fullmatch`
# semantics from the anchors). The fixed `agentguard/` prefix is a control,
# not just a convention:
#   - the workflow can never push to `main` or to an arbitrary branch;
#   - a reviewer, and a GitHub branch-protection rule, can tell an
#     AgentGuard-proposed branch from a human one at a glance;
#   - `[a-z0-9-]` blocks `/`, `..`, whitespace, and shell metacharacters in
#     the part of the name that comes from a workflow id;
#   - `{1,60}` bounds the length so an oversized id cannot become a branch.
BRANCH_PREFIX = "agentguard/"
SAFE_BRANCH = re.compile(r"^agentguard/[a-z0-9-]{1,60}$")


# --- The GitHub allowlist (Day 7 Lab 1) ------------------------------------
#
# Three pieces of *configuration* - they say *where* a machine-proposed
# change may go. They say nothing about *who* you are, so they grant no
# access and are safe to commit (docs/v4_github_demo_setup.md, "Configuration
# vs. secrets"). The GitHub token is the secret; `gh` holds it in the OS
# keyring, never in this repo.
#
# The allowlist does two jobs:
#   1. SHAPE checks (SAFE_REPO, SAFE_BRANCH) - a regex so a value containing
#      a space, ';', '&&', '$(...)', a backtick, a newline, or a second '/'
#      can never reach a `git` / `gh` argument. This is the command-injection
#      guard.
#   2. VALUE checks (ALLOWLISTED_REPOSITORIES, ALLOWLISTED_FILE_PATHS, the
#      `agentguard/` branch prefix) - exact membership, so the change can
#      only go to the one synthetic demo repo, an `agentguard/` branch (never
#      `main`), and the one synthetic file. This is the wrong-target guard.

SAFE_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

ALLOWLISTED_REPOSITORIES = frozenset({"justintinlei/agentguard-remediation-demo"})
ALLOWLISTED_FILE_PATHS = frozenset({"connected_environment/agents.json"})


def require_allowlisted_repository(repository: str) -> str:
    """Return `repository` if it is allowlisted; raise ValueError otherwise.

    Two gates: the OWNER/REPO *shape* (one '/', no spaces or shell
    metacharacters), then exact membership of ALLOWLISTED_REPOSITORIES.
    """
    if not isinstance(repository, str) or not SAFE_REPO.fullmatch(repository):
        raise ValueError(f"repository is not OWNER/REPO shaped: {repository!r}")
    if repository not in ALLOWLISTED_REPOSITORIES:
        raise ValueError(f"repository is not allowlisted: {repository!r}")
    return repository


def require_allowlisted_branch(branch: str) -> str:
    """Return `branch` if it matches ``^agentguard/[a-z0-9-]{1,60}$``; raise
    otherwise. This blocks a push to `main` or to any branch outside the
    `agentguard/` prefix, and blocks uppercase, nested `/`, and length abuse
    in the workflow-id part.
    """
    if not isinstance(branch, str) or not SAFE_BRANCH.fullmatch(branch):
        raise ValueError(f"branch is not an allowlisted agentguard/ branch: {branch!r}")
    return branch


def require_allowlisted_file_path(file_path: str) -> str:
    """Return `file_path` if it is allowlisted; raise ValueError otherwise.

    Exact membership of ALLOWLISTED_FILE_PATHS - stricter than a shape
    check: `..`, a leading `/`, and `.github/...` are simply not the one
    allowed string.
    """
    if not isinstance(file_path, str) or file_path not in ALLOWLISTED_FILE_PATHS:
        raise ValueError(f"file path is not allowlisted: {file_path!r}")
    return file_path


# --- The plan data contract (Day 7 Lab 2) ---------------------------------


@dataclass(frozen=True)
class GitHubPlan:
    """One reviewable GitHub remediation plan - data, not an action.

    Frozen: once built it cannot be edited, so it stands as the exact
    record of what would run. `__post_init__` validates every field
    against the Lab 1 allowlist, so an invalid `GitHubPlan` cannot be
    constructed.

      repository  OWNER/REPO, on the allowlist
      branch      an `agentguard/...` branch (never `main`)
      file_path   the one allowlisted file
      title       the commit / PR title
      commands    a tuple of token-lists, e.g.
                  (("git", "add", "connected_environment/agents.json"), ...).
                  Token-lists, never shell strings - there is no shell to
                  inject into. Empty until Lab 3-4 fill it in.
    """

    repository: str
    branch: str
    file_path: str
    title: str
    commands: tuple = ()

    def __post_init__(self) -> None:
        require_allowlisted_repository(self.repository)
        require_allowlisted_branch(self.branch)
        require_allowlisted_file_path(self.file_path)
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title must be a non-empty string")

        normalised = []
        for command in self.commands:
            if isinstance(command, str) or not isinstance(command, (list, tuple)):
                raise ValueError(f"each command must be a list of string tokens, not {command!r}")
            if not command:
                raise ValueError("a command must have at least one token")
            if not all(isinstance(token, str) and token for token in command):
                raise ValueError(f"command tokens must be non-empty strings: {command!r}")
            normalised.append(tuple(command))
        # Defensive, immutable copy: a caller mutating the list they
        # passed in cannot change this plan afterward.
        object.__setattr__(self, "commands", tuple(normalised))

    def to_dict(self) -> dict:
        return asdict(self)


# --- Build the plan (Day 7 Lab 3: git branch + commit commands) -----------

# The one file a remediation may edit - the sole member of
# ALLOWLISTED_FILE_PATHS, offered as a default so callers need not repeat it.
DEFAULT_FILE_PATH = "connected_environment/agents.json"

# `gh pr create --body-file` reads the PR description from this local file.
# Its content is what `render_pr_body()` (below) produces; it is written
# here just before live execution, not by `create_plan()`.
PR_BODY_PATH = ".agentguard/pr_body.md"


def create_plan(
    repository: str,
    workflow_id: str,
    file_path: str = DEFAULT_FILE_PATH,
) -> GitHubPlan:
    """Build the GitHubPlan for one remediation - five commands.

    The four `git` steps keep the change *off* `main`:

      1. `git checkout -b agentguard/<id>`  - a new branch off the current
         HEAD; the remediation lives only here.
      2. `git add <file_path>`              - stage exactly the one
         allowlisted file, never `git add .` / `-A`.
      3. `git commit -m <title>`            - commit on the new branch.
      4. `git push -u origin agentguard/<id>` - push *that branch* to the
         remote; never `git push origin main`.

    Then one `gh` step opens the pull request:

      5. `gh pr create --draft --repo <repo> --title <title> --body-file
         <PR_BODY_PATH>` - a **draft** PR. A draft PR cannot be merged
         (the merge button is disabled) until a human clicks "Ready for
         review", so the machine-created PR *begins in review state* - it
         is a proposal, not an applied change.

    There is no `git merge`, no `git checkout main`, no `--force`, and no
    `gh` `--auto` / auto-merge anywhere: the only thing that ever moves
    `main` is a human merging the draft PR.

    Input validation is at the boundary: `create_plan` refuses an
    unapproved `repository`, `file_path`, or `workflow_id` *before* it
    builds any command token, and `GitHubPlan.__post_init__` re-checks
    all three (defence in depth). No unvalidated string ever becomes a
    `git` / `gh` argument.
    """
    require_allowlisted_repository(repository)
    require_allowlisted_file_path(file_path)
    branch = branch_name(workflow_id)  # validates the branch and the id shape
    title = pr_title(workflow_id)
    commands = (
        ("git", "checkout", "-b", branch),
        ("git", "add", file_path),
        ("git", "commit", "-m", title),
        ("git", "push", "-u", "origin", branch),
        ("gh", "pr", "create", "--draft", "--repo", repository, "--title", title, "--body-file", PR_BODY_PATH),
    )
    return GitHubPlan(repository, branch, file_path, title, commands)


# --- Execute the plan (Day 7 Lab 5-6: dry-run default, opt-in live) -------


def execute_plan(plan: GitHubPlan, *, live: bool = False) -> list[dict]:
    """Run `plan`. **Dry-run by default: this changes nothing.**

    With no `live` flag, it returns one row per command -
    ``{"command": [...tokens...], "status": "DRY_RUN"}`` - so a person can
    read every `git` / `gh` call that *would* run: no branch is created,
    nothing is pushed, no pull request is opened, no file is written, and
    there is no network call. Safe to call any number of times.

    `live=True` is the **only** path that carries out the commands, and it
    is deliberate: `live` is keyword-only, so `execute_plan(plan, True)`
    is a `TypeError` - you must type `live=True`. It runs each command
    with `subprocess` as a **token list (no shell)** and `check=True`, so
    a non-zero exit raises `CalledProcessError` and stops the run rather
    than continuing past a failed step. `create_plan()` only describes a
    change; this call is where action authority lives.
    """
    if not live:
        return [{"command": list(command), "status": "DRY_RUN"} for command in plan.commands]

    results = []
    for command in plan.commands:
        completed = subprocess.run(
            list(command), check=True, text=True, capture_output=True
        )
        results.append(
            {
                "command": list(command),
                "status": "EXECUTED",
                "stdout": completed.stdout.strip(),
            }
        )
    return results


def branch_name(workflow_id: str) -> str:
    """Return the branch a remediation must use: `agentguard/<workflow_id>`,
    lower-cased. Raise ValueError if the result is not a SAFE_BRANCH."""
    name = f"{BRANCH_PREFIX}{workflow_id.lower()}"
    if not SAFE_BRANCH.fullmatch(name):
        raise ValueError(f"unsafe branch name: {name!r}")
    return name


def pr_title(workflow_id: str) -> str:
    """The fixed pull-request title shape."""
    return f"AgentGuard remediation {workflow_id}"


# The fixed pull-request body. Every field a reviewer needs to judge the
# proposal is a labelled line, so proposals are comparable at a glance and a
# reviewer never has to open another tool to see what changed and why. The
# footer is constant: this is always a draft, AgentGuard cannot merge, and
# the data is synthetic.
PR_BODY_TEMPLATE = """\
## AgentGuard remediation proposal

- **Workflow ID:** {workflow_id}
- **Template:** {template_id}
- **Target agent:** {agent_name}
- **Finding addressed:** {finding}
- **Predicted risk score after change:** {predicted_score}
- **Source environment SHA-256:** {source_sha256}
- **Proposal SHA-256:** {proposal_sha256}

This pull request was generated by AgentGuard v4 from an allowlisted
remediation template. It is a **draft**: a human must review the diff and
merge it. AgentGuard has no merge capability.

Synthetic training data only. Never merge into a production system.
"""

# The labelled lines above, by their format key. render_pr_body() requires
# every one — a missing field raises KeyError rather than producing a body
# with a hole in it.
PR_BODY_FIELDS = (
    "workflow_id",
    "template_id",
    "agent_name",
    "finding",
    "predicted_score",
    "source_sha256",
    "proposal_sha256",
)


def render_pr_body(**fields: str) -> str:
    """Fill PR_BODY_TEMPLATE. Every key in PR_BODY_FIELDS must be supplied."""
    missing = [key for key in PR_BODY_FIELDS if key not in fields]
    if missing:
        raise KeyError(f"missing PR body field(s): {', '.join(missing)}")
    return PR_BODY_TEMPLATE.format(**fields)


def write_pr_body(target_dir, **fields: str) -> Path:
    """Render the PR body and write it to ``target_dir/.agentguard/pr_body.md``.

    ``target_dir`` is the checked-out demo-repo working tree - the same
    directory the live ``git`` / ``gh`` commands run in, so
    ``gh pr create --body-file .agentguard/pr_body.md`` (relative to that
    cwd) finds the file. There is no default: the caller must name the
    directory, so this can never write into the AgentGuard source repo by
    accident.

    Creates the ``.agentguard/`` directory if it does not exist, overwrites
    any stale body, and returns the ``Path`` written. A missing review
    field raises ``KeyError`` (from ``render_pr_body``) *before* any
    directory or file is created.
    """
    body = render_pr_body(**fields)  # raises KeyError here, before any write
    path = Path(target_dir) / PR_BODY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path
