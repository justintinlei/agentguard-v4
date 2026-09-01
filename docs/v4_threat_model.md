# V4 Threat Model — Governed Remediation

v4 is the first version that can **change** an agent's configuration (on
synthetic data, via a draft pull request). Security design starts by naming the
abuse cases that new capability opens, then pointing at the deterministic control
that blocks each and the permanent test that proves it. This document inventories
what is real; it does not propose new protection.

Every control below is also exercised end to end by `evals/run_v4_evals.py`,
which *injects* a bad input and passes only if v4 refuses it — 10 injections plus
2 positive controls, ending `V4 FAILURE-INJECTION EVAL PASS: 10 of 10 checks held
(fails closed)`. That eval runs on every `python scripts/run_release_gate.py`.

The v3 threat model ([`docs/v3_threat_model.md`](v3_threat_model.md)) still holds
unchanged — the discovery boundary is untouched. This document covers only the
new action layer.

## 1. Arbitrary model-generated patch

**Attack:** the AI layer emits a free-form code or config diff — "here is the
fix" — and the system applies it. An unconstrained model becomes a write
primitive.

**Control:** there is no code path that applies model output. A remediation is
one of exactly three allowlisted templates (`remediation_templates.py`:
`REQUIRE_HUMAN_APPROVAL`, `ASSIGN_OWNER`, `REMOVE_BROAD_ADMIN_TOOL`), each a
deterministic function producing a bounded `field_changes` dict.
`require_allowlisted(template_id)` rejects anything else before an agent is
touched. The AI layer may *explain* a finding and *suggest* which template
applies; it never produces the change.

**Proven by:** `tests/test_remediation_templates.py` (an unknown template is
blocked; each template changes only its documented field);
`tests/test_app_v4.py::test_an_unallowlisted_template_is_refused_before_touching_an_agent`;
`evals/run_v4_evals.py` "a risk-raising remediation is blocked before planning".

## 2. Stale or replayed approval

**Attack:** a human approves proposal A against source S; then the proposal or
the source changes and the old approval is reused to push through a change
nobody signed off.

**Control:** `approval.decide()` records an `ApprovalRecord` bound to **both**
`proposal_sha256` and `source_sha256` (canonical-JSON SHA-256, `proposal_hash.py`).
`approval.validate_approval(record, proposal_sha256, source_sha256)` raises unless
the decision is `APPROVE` **and** both hashes still match, in that order
("not approved" / "proposal changed" / "source changed").
`approval.approval_is_current()` is the non-raising wrapper the workflow checks
before `APPROVED → VERIFIED`.

**Proven by:** `tests/test_approval.py` (changed proposal rejected; changed
source rejected; exact-match passes);
`tests/test_failure_paths.py`; `evals/run_v4_evals.py` "a drifted approval is no
longer current".

## 3. Direct production write

**Attack:** the workflow writes the change straight into the real inventory, or
into a real repository, skipping review.

**Control:** the only inventory write is to an **isolated temp copy**
(`verifier.py`: `isolated_candidate_file` + `apply_proposal_to_environment`, which
deep-copies). The source file is never opened for writing. GitHub delivery is a
`GitHubPlan` — data, not an action — and `execute_plan()` is **dry-run by
default**; `live=True` is keyword-only and targets only the allowlisted synthetic
demo repo. The app (`app_v4.py`) has no live-execution control at all.

**Proven by:** `tests/test_verifier.py` (source unchanged after verification);
`tests/test_app_v4.py::test_approve_and_verify_does_not_mutate_the_environment`;
`tests/test_github_plan.py` (dry-run is the default; a dry run never shells out);
`evals/run_v4_evals.py` "a dry run never shells out".

## 4. Repository / branch / file-path injection

**Attack:** a crafted repository name, branch, or file path carries shell
metacharacters or points at the wrong target (`main`, the AgentGuard source repo,
`.github/workflows/…`).

**Control:** `github_plan.py` runs two gates on every value — a **shape** regex
(`SAFE_REPO`, `SAFE_BRANCH`: one `/`, no spaces, `;`, `&&`, `$(…)`, backticks,
newlines) and **exact membership** (`ALLOWLISTED_REPOSITORIES`,
`ALLOWLISTED_FILE_PATHS`, the `agentguard/` branch prefix). Commands are built as
**token lists**, never shell strings — `subprocess.run(list(command))` with no
`shell=True`, so there is no shell to inject into. `GitHubPlan.__post_init__`
re-validates every field, so an invalid plan cannot be constructed.

**Proven by:** `tests/test_github_plan.py` (a matrix of malformed repos, branches,
and paths all raise; no unvalidated string can appear as a command token);
`tests/test_failure_paths.py`; `evals/run_v4_evals.py` "an unapproved repository
is refused".

## 5. Bypassed or skipped verification

**Attack:** jump from `PROPOSED` or `APPROVED` straight to `DRAFT_PR_CREATED`,
delivering a change that was never verified — or that raised the HIGH-risk count.

**Control:** `workflow.transition()` is a pure guard over `ALLOWED_TRANSITIONS`;
every `(from, to)` pair not on the map raises `ValueError`. The only route to
`VERIFIED` is `APPROVED → VERIFIED`, gated by `verifier.verify()` — 10 check rows
including "HIGH-risk count did not increase", "exactly one target changed", "only
allowlisted keys changed". `verifier.require_verified(result)` raises unless
`result.passed`, blocking GitHub planning.

**Proven by:** `tests/test_workflow.py` (all ~70 illegal arrows raise; no
shortcut to `VERIFIED`); `tests/test_verifier.py`;
`tests/test_failure_paths.py::…cannot_skip_from_proposed_to_verified`;
`evals/run_v4_evals.py` "state-skipping is refused" and "a risk-raising
remediation is blocked".

## 6. Unreviewed merge / auto-merge

**Attack:** the workflow merges its own PR, or opens it ready-to-merge, so a
machine-proposed change lands in `main` with no human review.

**Control:** `create_plan()` builds exactly five commands ending in
`gh pr create --draft` — a **draft** PR cannot merge until a human clicks "Ready
for review". There is **no** `git merge`, `gh pr merge`, `--auto`, `--force`,
`git checkout main`, or `git reset` token anywhere in any plan, over a matrix of
workflow ids.

**Proven by:** `tests/test_github_plan.py` (`FORBIDDEN_TOKENS` / `FORBIDDEN_COMMANDS`
disjoint from every plan; exactly one `gh` command and it is a draft `pr create`);
`tests/test_app_v4.py::test_render_gates_the_plan_on_verified_and_has_no_live_execution`;
`evals/run_v4_evals.py` "no plan has merge / --force / a non-agentguard push".

## 7. Post-merge automatic rollback

**Attack:** after a PR is merged, the system "rolls back" by rewriting shared
history (force-push, reset, an unreviewed revert).

**Control:** `rollback.rollback_plan()` takes a required keyword-only `merged`
flag. `merged=True` raises `ValueError("Automatic rollback is refused after
merge. Use a reviewed revert workflow.")` and returns no command. A non-bool
`merged` also raises (so `"no"` / `0` / `None` cannot be read as "not merged").
Pre-merge rollback is only two reversible commands: `gh pr close` +
`git push origin --delete <agentguard/ branch>` — never `--force`, never a
history rewrite.

**Proven by:** `tests/test_rollback.py` (merged refused; the two-command plan has
no forbidden token; the branch delete targets an `agentguard/` branch only);
`evals/run_v4_evals.py` "rollback after merge is refused".

## 8. Audit-trail tampering or silence

**Attack:** a failed, rejected, or rolled-back run leaves no record, so the log
implies success — or a row is edited after the fact.

**Control:** the SQLite `workflow_events` table is **append-only by convention** —
`audit_db.py` has no `UPDATE` or `DELETE` code path, uses `?` placeholders, and
orders by `id` (not `created_at`, which can tie). `workflow.record_terminal_state()`
is the one helper for an ending: it takes the `transition()` step **and** writes
the matching event (`workflow_rejected` / `workflow_failed` /
`workflow_rolled_back`) with a required non-empty `reason`. `transition()` alone
never writes, so a state can never be logged that the guard would have rejected.

**Proven by:** `tests/test_audit_db.py` (events ordered; missing db / unknown id
returns `[]`); `tests/test_workflow.py` (every recorded run is a legal, ordered
walk); `tests/test_failure_paths.py` (a failed run is recorded as `FAILED`);
`evals/run_v4_evals.py` "a failed run is recorded as a terminal state".

## 9. Credential / secret leakage

**Attack:** a GitHub token, API key, or SSH material lands in the repo, a
container image, or a log.

**Control:** no token is ever held by AgentGuard — `gh` keeps it in the OS
keyring; `app_v4.github_auth_status()` shells `gh auth status` and strips any
`Token:` line before returning. `scripts/check_no_secrets.py` scans every tracked
`.py` / `.md` / `.yml` / `.yaml` / `.txt` / `.json` / `.gitignore` plus
`Dockerfile` / `.dockerignore` for `sk-ant-…` / `github_pat_…` / `gh[oprsu]_…`
shapes on every release-gate run. The `Dockerfile` runs as non-root `appuser`
with no `ANTHROPIC_API_KEY`; `.dockerignore` and `.gitignore` exclude `.env*`,
`*.db`, and `.agentguard/`.

**Proven by:** `scripts/check_no_secrets.py` (`SECRET CHECK PASS` in the gate);
`tests/test_check_no_secrets.py`;
`tests/test_app_v4.py::test_auth_status_strips_any_token_line`;
`tests/test_ci_workflow.py`.

## Accepted residual risks

Understood and deliberately **accepted** for the MVP — decisions, not oversights:

1. **The app's event timeline is in-memory.** `app_v4.approve_and_verify()`
   returns an ordered list of steps for display; it does **not** write to the
   SQLite audit DB. The durable audit trail (`audit_db.py`,
   `workflow.record_terminal_state`) is fully built and tested, but a
   `v4_service` orchestrator that wires it into the UI path is deferred to
   post-MVP. The tests and evals exercise the durable path directly.
2. **Single-reviewer approval, no RBAC.** `decide()` records one reviewer name
   as free text. There is no identity check, no separation of duties, no
   "two-person rule". Acceptable for a synthetic demo; real use needs approval
   RBAC.
3. **Unbounded response-block parse (carried from v3).** `mcp_client._structured()`
   parses a tool response's first text block as JSON with no size cap —
   accepted because the server is a local subprocess, not a network peer.
   Revisit if the discovery server can ever be remote.
4. **Local-only trust in `gh` / `git`.** Live execution trusts that the local
   `gh` is authenticated to the right account and the demo repo is the intended
   one. The allowlist bounds the *target*; it does not verify the *operator*.
