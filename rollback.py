"""Plan the rollback of a draft pull request - and refuse it after merge.

Day 8 Lab 2 slice: ``rollback_plan()`` returns the two commands that undo
a draft pull request AgentGuard opened - close the PR, delete its branch.
Both are reversible (a closed PR can be reopened; a deleted remote branch
can be re-pushed from a local copy), which is exactly why undoing an
*unmerged* change is safe to automate.

Day 8 Lab 3 slice: the caller must state whether the PR was ``merged``.
If it was, the change is already in shared history and the only correct
undo is a **new reviewed ``git revert`` pull request** - never an
automated history rewrite. So ``rollback_plan(..., merged=True)`` raises
``ValueError`` and produces no command at all.

Like ``github_plan.create_plan()``, this returns **data for review** and
runs nothing: no ``subprocess``, no network, no ``git`` / ``gh`` call.
Inputs are validated with the same Day 7 allowlist validators
``create_plan()`` uses, so no unapproved string can reach a ``git`` /
``gh`` argument.
"""

from __future__ import annotations

from github_plan import require_allowlisted_branch, require_allowlisted_repository

# The fixed comment left on the pull request when AgentGuard closes it, so
# a reviewer scanning the repo can see why the PR was closed.
ROLLBACK_COMMENT = "Closed by AgentGuard rollback."


def rollback_plan(
    repository: str, pr_number: int, branch: str, *, merged: bool
) -> list[list[str]]:
    """Return the two commands that roll back one *unmerged* draft PR.

    1. ``gh pr close <n> --repo <repo> --comment "..."`` - close the pull
       request without merging it. The commits and branch still exist and
       the PR can be reopened.
    2. ``git push origin --delete <branch>`` - delete the feature branch
       on the remote. Not ``--force``, not a history rewrite; if the
       branch still exists locally it can be re-pushed.

    Every command is a **token list**, never a shell string - there is no
    shell to inject metacharacters into. ``str(pr_number)`` because
    command arguments are strings.

    ``merged`` is **keyword-only and required**: the caller must state
    whether the PR was merged - there is no fail-open default. It is
    checked first, before any input validation or token building:
      - not a ``bool`` -> ``ValueError`` (so ``merged="no"`` / ``0`` /
        ``None`` cannot be silently treated as "not merged");
      - ``True`` -> ``ValueError`` "Automatic rollback is refused after
        merge. Use a reviewed revert workflow." A merged change lives in
        shared history; undoing it means a new reviewed ``git revert``
        PR, which AgentGuard does not automate. No command is returned.

    Then, for an unmerged PR, the inputs are checked before any token is
    built:
      - ``repository`` must be on the Day 7 allowlist (the one synthetic
        demo repo), OWNER/REPO shaped;
      - ``branch`` must match ``^agentguard/[a-z0-9-]{1,60}$`` - so the
        delete can only ever target an AgentGuard feature branch, never
        ``main``;
      - ``pr_number`` must be a positive integer (``bool`` is rejected
        even though it is an ``int`` subclass).
    Any miss raises ``ValueError`` and no command is returned.
    """
    if not isinstance(merged, bool):
        raise ValueError(f"merged must be a bool: {merged!r}")
    if merged:
        raise ValueError(
            "Automatic rollback is refused after merge. "
            "Use a reviewed revert workflow."
        )

    require_allowlisted_repository(repository)
    require_allowlisted_branch(branch)
    if isinstance(pr_number, bool) or not isinstance(pr_number, int) or pr_number < 1:
        raise ValueError(f"pr_number must be a positive integer: {pr_number!r}")

    return [
        ["gh", "pr", "close", str(pr_number), "--repo", repository, "--comment", ROLLBACK_COMMENT],
        ["git", "push", "origin", "--delete", branch],
    ]
