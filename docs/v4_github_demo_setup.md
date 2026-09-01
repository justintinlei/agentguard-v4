# AgentGuard v4 — GitHub Demo Setup

**Status: design + setup, in progress across Day 2.** This document is the plan
and the safety contract for the GitHub side of v4's remediation demo. The code
that *enforces* the allowlist and the dry-run / draft-only rules
(`github_plan.py` and its tests) is built on Day 7; until then this is the agreed
design. All setup steps that touch a live GitHub account (installing `gh`,
authenticating, creating the repo, opening a PR) are run by the user on their own
machine with a dedicated test account, one per lab.

## The five terms, in plain English

- **Repository ("repo")** — a project's full file tree plus its entire version
  history, hosted on GitHub. Cloning a repo copies both.
- **Branch** — an independent line of commits inside one repo. Commits on one
  branch don't affect any other until they are deliberately merged. v4 puts each
  remediation on its own short-lived branch.
- **Commit** — one permanent, message-labelled snapshot of the staged changes.
  A commit records *what* changed and *why*, and can always be checked out
  again.
- **Push** — uploading local commits to the GitHub-hosted copy (the *remote*,
  usually named `origin`) so other people and CI can see them. **A push by
  itself changes nothing that anyone depends on** — it just makes the commits
  visible.
- **Pull request (PR)** — a request to merge one branch into another, presented
  as a reviewable diff with discussion, required reviewers, and automated status
  checks. A **draft PR** is explicitly marked not-ready and cannot be merged
  until it is taken out of draft.

## How source-control review separates a proposal from an applied change

A pull request is the change **offered**. A **merge** is the change **applied**.
Everything between the two is review surface:

- the **diff** shows every line that would change, so the proposal is fully
  inspectable before anything happens;
- **status checks / CI** must pass, so a proposal that breaks tests can't be
  applied;
- **required reviewers** must approve;
- and until someone clicks merge, the whole proposal can be discarded by simply
  closing the PR — nothing was applied.

v4's remediation workflow reuses this model exactly. The `VERIFIED →
DRAFT_PR_CREATED` transition in `docs/v4_architecture.md` produces a *proposal*
on GitHub — a draft PR on a branch. The only thing that ever *applies* it is a
**human clicking merge**. There is no merge command anywhere in v4's code, and
the PR is created as a draft so it cannot merge itself even by accident.

## The v4 demo setup (what Day 2 builds)

| Step | Lab | What it does | Safety point |
|---|---|---|---|
| Install `gh` | Day 2 Lab 2 | `brew install gh`; `gh --version` | The GitHub CLI is the only tool that talks to GitHub — a narrow, auditable surface |
| &nbsp; | &nbsp; | **Done:** `gh version 2.98.0 (2026-08-20)`, installed at `/opt/homebrew/bin/gh`. Version checked only; `gh auth status` reports "not logged into any GitHub hosts" — authentication is Lab 3. | &nbsp; |
| Authenticate | Day 2 Lab 3 | `gh auth login` through the **browser (OAuth)** | The token is stored by `gh` **outside this repo** — never pasted into a file, never committed |
| &nbsp; | &nbsp; | **Done:** logged in to `github.com` as `justintinlei`, HTTPS, token scopes `gist, read:org, repo, workflow`. The token is held in the **macOS keyring** (not even a file), reported by `gh auth status` as `gho_************`. No token value is recorded here or anywhere in the repo. | &nbsp; |
| Create the demo repo | Day 2 Lab 4 | A **new private repository** containing only synthetic files | Never the AgentGuard source repo, never a production repo |
| &nbsp; | &nbsp; | **Done:** `justintinlei/agentguard-remediation-demo` — private, default branch `main`, one README commit, no other content yet. `https://github.com/justintinlei/agentguard-remediation-demo`. Synthetic agent data is added in Lab 5. | &nbsp; |
| Clone it | Day 2 Lab 5 | Clone to a **sibling directory** (e.g. `~/Developer/AgentGuard/01-Working/agentguard-remediation-demo`), **never inside this repo** | Keeps the two git histories completely separate; nothing to add to this repo's `.gitignore` |
| &nbsp; | &nbsp; | **Done:** cloned to `~/Developer/AgentGuard/01-Working/agentguard-remediation-demo` (sibling). Added `connected_environment/agents.json` — the synthetic 3-agent registry copied verbatim from this repo (empty owner, no human approval, broad admin tools = the fixable before-state). Pushed to the demo repo's `main` (`e147248`). Still private. | &nbsp; |
| PR template + branch rule | Day 2 Lab 6 | Standard PR metadata and a fixed branch-name prefix | Every proposed change looks the same to a reviewer |
| &nbsp; | &nbsp; | **Done:** in `github_plan.py`. Branch names must match `^agentguard/[a-z0-9-]{1,60}$` (`github_plan.branch_name`) — so the workflow can never push to `main`. The PR body shape is `github_plan.PR_BODY_TEMPLATE` (labelled fields + a fixed draft / no-merge / synthetic footer), rendered by `github_plan.render_pr_body`; it is written to `.agentguard/pr_body.md` at PR-creation time (Day 7). A repo-level `.github/pull_request_template.md` in the demo repo is optional and can be added when the first real PR is made (Day 10). | &nbsp; |
| Practice a draft PR | Day 2 Lab 7 | Open one draft PR by hand, then close it | Learn the human workflow before AgentGuard automates it |
| &nbsp; | &nbsp; | **Done:** branch `agentguard/manual-practice` → one-line edit to `connected_environment/agents.json` (Customer Support Agent `human_approval_required` → `true`) → commit → push → `gh pr create --draft` opened **PR #1** (`isDraft: true`, base `main`). Then `gh pr close 1 --delete-branch` — `state: CLOSED`, `mergedAt: null` (never merged), branch deleted (local + remote). Demo repo `main` unchanged at `e147248`. | &nbsp; |
| Record the allowlist | Day 2 Lab 8 | Write down the exact `owner/repo`, branch prefix, and target file path as plain configuration | No secret is recorded — `scripts/check_no_secrets.py` must still pass |

## The allowlist (recorded — Day 2 Lab 8)

v4's GitHub step is permitted to touch **exactly**:

| Value | Setting | Recorded |
|---|---|---|
| repository | `justintinlei/agentguard-remediation-demo` | Day 2 Lab 4 |
| branch-name prefix | `agentguard/` — every branch must match `^agentguard/[a-z0-9-]{1,60}$` | Day 2 Lab 6 |
| target file path | `connected_environment/agents.json` | Day 2 Lab 5 |

Anything outside this list is refused by `github_plan.py`.

### How it is enforced (Day 7 Lab 1)

`github_plan.py` exposes three validators, each returning the value on
success and raising `ValueError` otherwise:

- `require_allowlisted_repository(repo)` — the OWNER/REPO **shape**
  (`SAFE_REPO`: one `/`, no spaces or shell metacharacters), then exact
  membership of `ALLOWLISTED_REPOSITORIES`.
- `require_allowlisted_branch(branch)` — must match `SAFE_BRANCH`
  (`^agentguard/[a-z0-9-]{1,60}$`), so a push can never target `main`.
- `require_allowlisted_file_path(path)` — exact membership of
  `ALLOWLISTED_FILE_PATHS`. Exact match is stricter than a shape check:
  `..`, a leading `/`, and `.github/…` are simply not the one allowed
  string.

The **shape** checks stop command injection (a metacharacter never reaches
a `git`/`gh` argument); the **value** checks stop wrong-target changes
(the change can only land in the one synthetic repo, on an `agentguard/`
branch, in the one synthetic file). The plan generator built across the
rest of Day 7 calls these validators before it builds any command.

### Blocking unapproved inputs (Day 7 Lab 7)

`create_plan(repository, workflow_id, file_path)` validates **every input
at its own entry**, before it builds a single command token:
`require_allowlisted_repository`, `require_allowlisted_file_path`, and
`branch_name()` (which validates the branch and, transitively, the
workflow id — it must lowercase to `[a-z0-9-]{1,60}`). `GitHubPlan`'s
`__post_init__` re-checks all three, so the type cannot hold an
unapproved value either.

What is refused (each raises `ValueError`, nothing is built):

| Category | Examples blocked |
|---|---|
| wrong repository | any `OWNER/REPO` but `justintinlei/agentguard-remediation-demo` — including the AgentGuard **source** repo and a `…-demos` typo |
| unsafe repo shape | `owner/repo; rm -rf ~`, `owner/$(id)`, `owner/repo && x`, a newline, backticks, no `/`, `a/b/c` |
| wrong / unsafe branch | `main`, `master`, `feature/x`, `agentguard/UPPER`, `agentguard/wf/nested`, an over-length id |
| wrong / unsafe file path | `README.md`, `.github/workflows/deploy.yml`, `/etc/passwd`, `../../secrets`, a `…/../../x` suffix, a case or trailing-space variant |

Because of this, every token in every generated command is either a fixed
literal (`git`, `gh`, `--draft`, …) or one of the validated values (the
repo, the file, the branch, the title) or `.agentguard/pr_body.md`.

### Guarantees under test (Day 7 Lab 8)

`tests/test_github_plan.py` proves, over a matrix of plans (not one
example):

- **Every pull request is `--draft`.** The one `gh` command in every plan
  is `gh pr create … --draft`.
- **There is no merge or "ready" command.** No plan contains `gh pr
  merge`, `gh pr ready`, `--auto`, `git merge`, or `git rebase` — the
  forbidden-token set is entirely absent from every command.
- **No command can touch `main`.** No plan contains `git checkout main` /
  `master`, `git push origin main`, `--force` / `-f`, or `git reset`. The
  single `git push` targets the `agentguard/` feature branch; the single
  `git checkout` is `checkout -b <that branch>`.
- **The plan shape is fixed.** `create_plan` always returns exactly five
  commands in the same order (`checkout`, `add`, `commit`, `push`, `pr
  create`) — no parameter can insert a sixth (merge) step.
- **Dry-run unless you name it.** `execute_plan(plan)` returns `DRY_RUN`
  rows and never calls `subprocess`; only `execute_plan(plan, live=True)`
  runs, and `live` is keyword-only.

### Configuration vs. secrets

Those three values are **configuration**: they say *where* a change may go. None
of them prove *who* you are, so reading them grants no access — they are checked
into version control, in this file, on purpose.

The GitHub **token** is a **secret**: it authenticates you. It is held in the
macOS keyring by `gh` (Lab 3), never written to a file, an environment variable,
or this repo. `scripts/check_no_secrets.py` scans every tracked text file for
`sk-ant-…`, `github_pat_…`, and `gh{o,p,s,r,u}_…` token shapes on every
release-gate run, so a committed credential fails the gate immediately.

### The plan object (Day 7 Lab 2)

A remediation's GitHub step is expressed as a `GitHubPlan` (`github_plan.py`) —
**data, not an action**:

| Field | Meaning |
|---|---|
| `repository` | `OWNER/REPO`, on the allowlist |
| `branch` | an `agentguard/…` branch, never `main` |
| `file_path` | the one allowlisted file |
| `title` | the commit / pull-request title |
| `commands` | the exact `git` / `gh` calls as **token-lists** — e.g. `("git", "add", "connected_environment/agents.json")` — never shell strings |

`GitHubPlan` is frozen and validates every field on construction (an invalid
plan cannot exist). It is produced and reviewed — the dry-run executor prints
every command — before anything runs. `create_plan()` (Lab 3–4) builds the
commands; `execute_plan()` (Lab 5–6) runs them, dry-run by default.

### The plan commands (Day 7 Labs 3–4)

`create_plan(repository, workflow_id)` fills `commands` with four `git`
steps and one `gh` step:

```
git checkout -b agentguard/<workflow_id>
git add connected_environment/agents.json
git commit -m "AgentGuard remediation <workflow_id>"
git push -u origin agentguard/<workflow_id>
gh pr create --draft --repo <repository> --title "AgentGuard remediation <workflow_id>" --body-file .agentguard/pr_body.md
```

How a remediation stays isolated from `main`:

- **A new branch, off HEAD.** The change lives on `agentguard/<id>` and
  nowhere else. The branch name is produced and validated by
  `branch_name()`, so it can never be `main`.
- **Only the one file is staged.** `git add` names the exact allowlisted
  file — never `git add .` or `git add -A`, which would sweep in anything
  else in the working tree.
- **The push targets that branch only.** `git push -u origin
  agentguard/<id>` — there is no `git push origin main`.
- **The PR opens in review state.** `gh pr create --draft` marks the PR a
  **draft**: the merge button is disabled until a human clicks "Ready for
  review". The machine-created PR is a *proposal*, not an applied change.
- **No apply step, no auto-merge.** The plan contains no `git merge`, no
  `git checkout main`, no `--force`, no `git reset`, and no `gh` `--auto`
  flag. `main` moves only when a human takes the PR out of draft and
  merges it.

The PR description is the output of `render_pr_body()` (labelled review
fields + the fixed draft / no-merge / synthetic footer). Just before live
execution, `github_plan.write_pr_body(<demo-repo working tree>, **fields)`
renders it and writes it to `.agentguard/pr_body.md` in that working tree.
That path is git-ignored in this repo and never `git add`-ed in the demo
repo, so the generated body lands in neither history.

### Executing the plan (Day 7 Labs 5–6)

`execute_plan(plan)` runs a plan — and **by default it does nothing**.
With no flag it returns one row per command:

```
{"command": ["git", "checkout", "-b", "agentguard/<id>"], "status": "DRY_RUN"}
{"command": ["git", "add", "connected_environment/agents.json"], "status": "DRY_RUN"}
...
{"command": ["gh", "pr", "create", "--draft", ...], "status": "DRY_RUN"}
```

No branch is created, nothing is pushed, no pull request is opened, no
file is written, and there is no network call — a person reads exactly
what *would* happen and decides.

**`execute_plan(plan, live=True)`** is the deliberate opt-in that actually
carries out the commands. It is the **only** function with the authority
to act — `create_plan()` merely describes. Properties:

- `live` is **keyword-only**: `execute_plan(plan, True)` is a `TypeError`.
  You have to type `live=True`.
- Each command runs via `subprocess` as a **token list with no shell**
  (`shell=True` is never used), so nothing is re-parsed for
  metacharacters.
- `check=True`: a non-zero exit raises `CalledProcessError` and **stops
  the run** — it never continues past a failed step.
- Each row comes back as `{"command": [...], "status": "EXECUTED",
  "stdout": "..."}` with captured output.

A real live run first calls `github_plan.write_pr_body(<demo-repo working
tree>, **fields)` to render the `render_pr_body()` output to
`.agentguard/pr_body.md` (Day 10 Lab 3), then runs the five commands with
cwd set to that same working tree.

## Standing rules for the GitHub surface

- **Synthetic data only.** The demo repo contains fabricated agent
  configuration, nothing real.
- **Dry-run by default.** The plan prints the exact `gh` / `git` commands it
  would run and changes nothing. Live execution is a separate, explicit opt-in.
- **Draft-only pull requests.** No merge command exists in the code.
- **Never a production repository**, and never the AgentGuard source repo.
- **Rollback before merge only** — close the draft PR and delete its branch.
  After a merge, v4 refuses automatic rollback and requires a reviewed revert.

This restates the Day 1 no-production pledge (`evidence/README.md`) for the
GitHub side specifically. The reasoning for keeping remediation in a separate
governed workflow — rather than a write tool on the MCP server — is in
`docs/v3_to_v4_handoff.md`.
