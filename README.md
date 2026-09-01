# AgentGuard v4 — Governed Remediation MVP

AgentGuard discovers synthetic AI-agent inventory, scores it with v1's
deterministic security rules, explains findings with a grounded AI layer, and —
new in v4 — proposes a **bounded, human-approved, verified, auditable
remediation** and delivers it only as a **draft pull request** on a dedicated
synthetic repository. It never gives an AI model arbitrary write access.

This is a synthetic training project. No real systems, accounts, credentials, or
data are involved at any point.

## The problem v4 solves

Visibility and explanation do not fix risk. An enterprise needs a way to propose
a *narrow* change to a risky agent, have a *named person approve the exact
reviewed content*, *verify* the change is correct before it is delivered, and
keep a full *audit and rollback* path — without trusting a probabilistic model to
decide risk or to touch production.

## The one invariant

Deterministic rules decide **what** to propose. Software verifies whether an
applied change is correct. A human approves **intent**. The AI layer may explain
a finding and propose a remediation — it may **never** approve, apply, verify, or
score. **v1's `scanner.py` remains the sole authority for the risk number**, from
v1 through v4 unchanged: a proposal *predicts* a score, it never *sets* one.

## End-to-end flow

```
Synthetic connected registry (connected_environment/, 3 JSON files)
  -> read-only MCP boundary        [v3, UNCHANGED — 5 read-only tools, SHA-256 provenance]
  -> v1 deterministic scanner      [v1, UNCHANGED — the sole risk authority]
  -> grounded AI explanation       [v2, UNCHANGED — explains, cites; never scores]
  -> remediation proposal          one of 3 allowlisted templates; predicts a score
  -> canonical hash                SHA-256 of the exact source AND the exact proposal
  -> human approval                APPROVE / REJECT, bound to both hashes
  -> isolated verification         apply to a throwaway copy, re-scan; HIGH count must not rise
  -> GitHub plan                   dry-run by default; opt-in live = ONE draft PR, never a merge
  -> SQLite audit + rollback       every ending recorded; pre-merge rollback = close PR + delete branch
```

The workflow is an explicit state machine
(`DISCOVERED → SCANNED → PROPOSED → APPROVED → VERIFIED → DRAFT_PR_CREATED →
ROLLED_BACK`, with `REJECTED` / `FAILED` as fail-closed terminals). Every step
not on the map is refused. Full map and enforcement:
[`docs/v4_state_machine.md`](docs/v4_state_machine.md). State-by-state
*data / authority / gate* table and the six trust boundaries:
[`docs/v4_architecture.md`](docs/v4_architecture.md). Abuse cases and the test
that blocks each: [`docs/v4_threat_model.md`](docs/v4_threat_model.md).

## The six trust boundaries

Authority to act increases at six points; each is gated by one named,
deterministic check:

1. **Data boundary** (inherited from v3) — connected inventory becomes
   scanner-readable only after `discovery_adapter.py` validates fields, types,
   and size limits.
2. **Score boundary** — only `scanner.py` ever sets a risk score; a proposal
   carries a *predicted* score and no AI output may change the real one.
3. **Approval boundary** (`PROPOSED → APPROVED`) — nothing proceeds without an
   `ApprovalRecord` bound to the exact proposal hash **and** source hash.
4. **Verification boundary** (`APPROVED → VERIFIED`) — nothing proceeds without
   an isolated apply + re-scan in which every check passes; software, not the
   human, confirms correctness.
5. **GitHub boundary** (`VERIFIED → DRAFT_PR_CREATED`) — only an approved *and*
   verified proposal reaches the repo, only within the repo/branch/path
   allowlist, dry-run by default, draft-only. There is no merge command anywhere
   in the code.
6. **Rollback boundary** — automatic reversal is allowed only *before* merge
   (close PR, delete branch). After a merge the system refuses and requires a
   reviewed `git revert`.

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/verify_setup.py          # runtime + current MCP 2.x imports
python scripts/run_release_gate.py       # the full gate — see below
streamlit run app_v4.py                  # the product
```

Everything runs in free, deterministic **mock mode** by default — no network
call, no cost, no API key. Live Claude mode (v2's analyst layer) is optional,
billed per token, and only ever reads a key from a local, git-ignored `.env`.

Container (only after local acceptance):

```bash
docker compose up        # app at http://localhost:8501, non-root, mock mode
```

GitHub live execution is **optional and opt-in**. It targets one private
synthetic demo repository, creates only a **draft** pull request, and is a
separate deliberate step — the app itself can never run it. Setup and the exact
commands: [`docs/v4_github_demo_setup.md`](docs/v4_github_demo_setup.md).

## Release gate & test report

One command re-proves every layer and prints a single pass line:

```bash
python scripts/run_release_gate.py
```

It runs, fail-fast, in order:

| Step | Command | Result |
|---|---|---|
| Course scaffolding + "exactly 5 read-only MCP tools" source check | `scripts/validate_starter_kit.py` | `STARTER KIT VALIDATION PASS: 80 labs` |
| Every v1 + v2 + v3 + v4 unit test | `python -m pytest -q` | **866 passed** |
| v2 evaluation matrix (forced mock mode) | `evals/run_v2_evals.py` | `V2 EVALUATION PASS: 3 of 3 cases passed` |
| v3 security evaluation suite | `evals/run_v3_evals.py` | `V3 SECURITY EVAL SUITE PASS` (6 threat-model categories) |
| v4 failure-injection evaluation | `evals/run_v4_evals.py` | `V4 FAILURE-INJECTION EVAL PASS: 10 of 10 checks held (fails closed)` |
| Secret scan (`.py` / `.md` / `.yml` / Dockerfile …) | `scripts/check_no_secrets.py` | `SECRET CHECK PASS` |

The run ends `RELEASE GATE PASS for AgentGuard v4`. `python -m compileall -q .`
is clean. CI (`.github/workflows/tests.yml`) runs the same unit tests plus the
v2/v3/v4 evals and the secret scan on every push, on Python 3.14.

The v4 eval is the security proof: each of its 10 checks *injects* a bad input —
a skipped workflow state, a rollback of an already-merged PR, a risk-raising
remediation, a drifted approval, a broken `gh` command, an unapproved
repository — and passes only if v4 **refuses** it. Two positive controls confirm
a valid remediation still verifies and still reaches a five-command plan, so
"fails closed" is not "broken closed".

Reproduce every claim yourself: [`evidence/README.md`](evidence/README.md).

## Inherited v2 / v3 baseline (verified, frozen)

v4 builds on the completed v2 and v3 projects without changing their behavior.

- **v1** — five deterministic rules (`AG-001`–`AG-005`) produce a score and a
  rule ID from a local JSON inventory. Unchanged.
- **v2** — a grounded Claude explanation layer: it retrieves real policy text,
  asks the model (or a free deterministic mock) for a structured explanation
  with citations, and validates every citation and the reported score before
  anything is shown. Explains and cites; never sets the score. Shipped tagged
  `v2.0.0-rc1`. See [`docs/v2_architecture.md`](docs/v2_architecture.md) and
  [`docs/v2_threat_model.md`](docs/v2_threat_model.md).
- **v3** — a read-only MCP (Model Context Protocol) 2.x server/client pair
  (`mcp_server.py` / `mcp_client.py`) that discovers the inventory over STDIO
  under a fixed allowlist, exposing **exactly five** tools (`health_check`,
  `list_agent_inventory`, `get_agent_by_name`, `list_tool_catalog`,
  `list_agent_ownership`) — no create, update, or delete tool. The client
  refuses any server whose tool set is not exactly those five. Ended
  `RELEASE GATE PASS for AgentGuard v3`. See
  [`docs/v3_architecture.md`](docs/v3_architecture.md) and
  [`docs/v3_threat_model.md`](docs/v3_threat_model.md).

**v4 adds no sixth, write-capable MCP tool.** The remediation workflow is a
separate governed component so v3's server stays provably read-only forever. The
reasoning: [`docs/v3_to_v4_handoff.md`](docs/v3_to_v4_handoff.md).

## Learn more

- [`START_HERE.md`](START_HERE.md) — course navigation and how to re-verify the build
- [`docs/lab_execution_index.md`](docs/lab_execution_index.md) — the authoritative map of all 80 labs
- [`docs/v4_architecture.md`](docs/v4_architecture.md) — state-by-state authority table and the six trust boundaries
- [`docs/v4_state_machine.md`](docs/v4_state_machine.md) — the transition map, its enforcement, and the audit log
- [`docs/v4_threat_model.md`](docs/v4_threat_model.md) — the abuse categories, the control for each, and the test that proves it
- [`docs/v4_github_demo_setup.md`](docs/v4_github_demo_setup.md) — the private synthetic demo repo, the allowlist, and the optional draft-PR run
- [`docs/final_mvp_interview_brief.md`](docs/final_mvp_interview_brief.md) — eleven likely interview questions answered from the real code
- [`docs/post_mvp_backlog.md`](docs/post_mvp_backlog.md) — what a next version would build, and how this prototype maps to résumé / portfolio / interviews
- [`docs/v3_to_v4_handoff.md`](docs/v3_to_v4_handoff.md) — why v4 governs writes through proposals + approval instead of a write tool
- [`evidence/README.md`](evidence/README.md) — reproduce and save proof of every claim yourself
- [`docs/roadmap.md`](docs/roadmap.md) — the full v1–v4 plan
- `CLAUDE.md` — the standing safety boundaries for working in this repo

## Safety boundaries

Everything runs locally on synthetic data; no real credentials or accounts are
involved. The MCP discovery server is read-only and exposes exactly five tools.
Only v1's deterministic rules ever set a risk score — the AI layer explains and
cites, never decides. GitHub work is dry-run by default, draft-only, on a
dedicated synthetic repo, and there is no merge command anywhere in the code.
Full list: `CLAUDE.md`.
