# AgentGuard — Evidence

This folder is the reproducible proof for every claim AgentGuard makes. Each
section is a command you can re-run (or a file to open) plus the exact result to
expect — not a claim to take on faith.

**Reviewing v4?** Skip to the two final v4 sections near the end — the
three-layer capture checklist (protocol · product · verification) and the
rehearsable five-minute demo. Everything above them is a dated archive of the
v1 → v4 build, in the order it was captured.

---

# AgentGuard v1 — Required Evidence

Per `CLAUDE.md`, this project needs to demonstrate four things before v1 is
considered done:

1. **Four automated tests pass.**
2. **The BEFORE scan shows two HIGH-risk agents.**
3. **The AFTER scan shows zero HIGH-risk agents.**
4. **The AFTER scan shows three NO RISK FOUND agents.**

## How to check each item yourself

**Tests (item 1):**

```bash
source .venv/bin/activate
pytest -q
```

You should see `4 passed`. The last test in `tests/test_scanner.py`
(`test_before_environment_has_two_high_and_after_has_zero_high_three_clear`)
directly checks items 2, 3, and 4 by loading both sample JSON files and
counting risk levels.

**Visual confirmation in the app (once approved to run):**

```bash
streamlit run app.py
```

- Open the **Before guardrails** tab, click **Scan this environment**, and
  confirm the HIGH count shown is **2**.
- Open the **After guardrails** tab, click **Scan this environment**, and
  confirm the HIGH count is **0** and the NO RISK FOUND count is **3**.
- Open the **Before vs. after** tab to see all three agents' risk levels
  side by side.

## Saving evidence

If you want a permanent record, take a screenshot of each tab after
scanning and save it in this `evidence/` folder (e.g.
`evidence/before_scan.png`, `evidence/after_scan.png`), or paste the exact
`pytest -q` output into a text file here.

---

# AgentGuard v2 — Day 1 Evidence

Day 1 has no application to screenshot yet — it's setup, orientation, and
one design document. Its evidence package is four small, reproducible
proof points: a command you can re-run plus the file it touches, not a
claim you have to take on faith.

1. **A separate branch with a baseline commit (Lab 4).**
   ```bash
   git log --oneline --all --decorate
   ```
   Expect two lines: `main` still at `f31889b Start V2 from verified
   AgentGuard V1 baseline`, and `v2-development` one commit ahead at
   `0f2f8af Complete Day 1 setup: v2 orientation docs and learning log
   baseline`. Save as `evidence/day01-branch-and-commit.png` (or paste the
   text output).

2. **The v1 regression suite passing, unmodified (Lab 5).**
   ```bash
   python -m pytest -q tests/test_scanner.py
   ```
   Expect `4 passed`. Save as `evidence/day01-regression-tests.png` (or
   paste the text output) — this is the "before" baseline every later
   day's test run gets compared against.

3. **The v2 architecture diagram (Lab 6).**
   The file itself: `docs/v2_architecture.md`. No command to run — save a
   screenshot of the diagram, or just keep the file as the evidence.

4. **The Day 1 learning log (Labs 1–7).**
   The file itself: `notes/learning_log.md`. Its "Day 1 Summary" entry
   indexes what was learned in each lab — this is the readable record a
   beginner or an interviewer can point to without re-reading every entry.

---

# AgentGuard v3 — Day 1 Evidence

Day 1 has no application to screenshot yet — it's setup, orientation, and
one design document, exactly like v2's Day 1 was. Its evidence package is
four small, reproducible proof points: a command you can re-run plus the
file it touches, not a claim you have to take on faith.

1. **A separate branch with a baseline commit (Lab 4).**
   ```bash
   git log --oneline --all --decorate
   ```
   Expect two lines: `main` still at `84f249e Start V3 from verified
   AgentGuard V2 baseline`, and `v3-development` one commit ahead at
   `3667335 Complete Day 1 setup: v3 orientation docs and learning log
   baseline`. Save as `evidence/day01-branch-and-commit.png` (or paste the
   text output).

2. **The full v1+v2 regression gate passing, unmodified (Lab 5).**
   ```bash
   python scripts/run_release_gate.py
   ```
   Expect `RELEASE GATE PASS` — 52 tests passed, 3 of 3 v2 evaluation
   cases passed, and the secret scan clean. Save as
   `evidence/day01-regression-gate.png` (or paste the text output) — this
   is the known-good baseline every later day's work gets compared
   against.

3. **The v3 trust boundary and data flow diagram (Lab 7).**
   The file itself: `docs/v3_architecture.md`. No command to run — save a
   screenshot of the diagram and trust-boundary table, or just keep the
   file as the evidence.

4. **The Day 1 learning log (Labs 1–8).**
   The file itself: `notes/learning_log.md`. Its "Day 1 Summary — Labs 1
   through 8" entry indexes what was learned in each lab — the readable
   record a beginner or an interviewer can point to without re-reading
   every entry.

---

# AgentGuard v3 — Day 3 Evidence

No MCP server exists yet (that's Day 5), so the `connected_environment/`
files as they stand right now — validated, within their documented size
limits — *are* the "before discovery" evidence: the registry's exact
starting condition, prior to any read-only tool ever touching it.

1. **The connected data contract (Labs 1, 7).**
   The file itself: `docs/v3_data_contract.md` — defines what fields and
   maximum sizes an enterprise registry must provide, decided before any
   code reads from one.

2. **The before-discovery snapshot: valid and within contract (Labs
   2–6).**
   ```bash
   find connected_environment -type f -exec wc -c {} +
   python -m json.tool connected_environment/agents.json > /dev/null
   python -m json.tool connected_environment/tool_catalog.json > /dev/null
   python -m json.tool connected_environment/ownership.json > /dev/null
   ```
   Expect all three JSON files to validate with no output (success), and
   every file size well under its documented limit in
   `docs/v3_data_contract.md`: `ownership.json` 247 bytes, `tool_catalog.json`
   651 bytes, `agents.json` 951 bytes, `untrusted_notes.txt` 1,326 bytes
   (limit 10 KB). Save as `evidence/day03-before-discovery.png` (or
   paste the text output) — this is the exact state Day 5+'s server will
   later read from.

3. **The intentionally malicious untrusted note (Lab 5).**
   The file itself: `connected_environment/untrusted_notes.txt` — proof a
   self-labeled, synthetic prompt-injection test fixture already exists
   in the before-state, ready for Day 8's security-testing labs.

---

# AgentGuard v3 — Day 6 Evidence

Day 6 is the first day since Day 3 with genuine interactive, live
artifacts — an Inspector session and a real independent client — worth
screenshotting rather than only proving through `pytest`. Full detail
for the manual steps lives in `docs/v3_inspector_walkthrough.md`; this
is the reproducible index an interviewer (or future-you) can follow
command by command.

1. **The Inspector session (Labs 1–4).** Interactive and manual — no
   single command reproduces a screenshot, but every step is exact in
   `docs/v3_inspector_walkthrough.md`. With the venv active, run:
   ```bash
   npx @modelcontextprotocol/inspector python mcp_server.py
   ```
   Open the printed local URL, click **Connect**, and capture:
   - The **Tools** panel listing exactly five entries: `health_check`,
     `list_agent_inventory`, `get_agent_by_name`, `list_tool_catalog`,
     `list_agent_ownership`. Save as
     `evidence/day06-inspector-tool-list.png`.
   - The `health_check` response (`status: "ok"`, `mode: "read-only"`,
     `tool_count: 5`). Save as
     `evidence/day06-inspector-health-check.png`.
   - Each of the four remaining tools' responses, compared against the
     known-good values in the walkthrough doc (3 agents, "Research
     Agent" owned by "Product Research", 8 tools, 3 ownership
     records). Save as `evidence/day06-inspector-list-agent-inventory.png`,
     `-get-agent-by-name.png`, `-list-tool-catalog.png`,
     `-list-agent-ownership.png`.
   - The five invalid-input error responses on `get_agent_by_name`
     (empty name, unknown name, oversized name, wrong type, missing
     field) — confirm none contains a file path or "Traceback". Save
     as `evidence/day06-inspector-invalid-inputs.png`.

2. **The live client, end to end (Lab 5).**
   ```bash
   python scripts/run_mcp_live_smoke.py
   ```
   Expect:
   ```
   MCP LIVE SMOKE PASS
   Health: ok read-only
   Discovered agents: 3
   ```
   Save as `evidence/day06-mcp-live-smoke.png` (or paste the text
   output) — proof the independent client (not Inspector) can start
   the server, initialize a session, list tools, and call one, for
   real, outside any devtool.

3. **The tool allowlist and error-handling tests (Labs 6–7).**
   ```bash
   python -m pytest -q tests/test_mcp_client.py -v
   ```
   Expect `8 passed`: the allowlist accepting the real five tools and
   rejecting a missing or an unexpected extra one; a malformed or
   empty tool response rejected as `MCPMalformedResponseError`; an
   unreachable server and a hung server both rejected as
   `MCPUnavailableError`; and the plain happy path succeeding against
   the real, unmodified server. Save as
   `evidence/day06-client-tests.png` (or paste the text output).

4. **The full regression gate, unmodified (all of Day 6).**
   ```bash
   python -m pytest -q
   ```
   Expect `111 passed` — the 103 tests standing at the end of Day 5,
   plus 8 new ones for the client, none removed or weakened. Save as
   `evidence/day06-regression-tests.png` (or paste the text output) —
   this is the baseline every later day's work gets compared against.

---

# AgentGuard v3 — Day 10: the "exactly five read-only tools" claim

v3's central security promise is one sentence: the MCP server exposes
exactly five tools and every one is read-only. It is proven four
independent ways — grep, gate, Inspector, and the running SDK — so no
single artifact has to be trusted alone, and a change that adds a sixth
tool or a write tool fails at least one of them immediately.

1. **Source inspection — no server, no execution.**
   ```bash
   grep -n "@mcp.tool()" mcp_server.py
   grep -n -A 7 "EXPECTED_TOOLS" mcp_client.py
   ```
   Expect five `@mcp.tool()` lines in the server, and the client's
   `EXPECTED_TOOLS` set holding the same five names: `health_check`,
   `list_agent_inventory`, `get_agent_by_name`, `list_tool_catalog`,
   `list_agent_ownership`. Every name is a read verb (`health`, `list`,
   `get`) — no create, update, delete, or write. Save as
   `evidence/day10-five-tools-source.png` (or paste the text).

2. **The release gate enforces it.**
   ```bash
   python scripts/validate_starter_kit.py
   ```
   Expect a line `MCP TOOL SET VERIFIED: 5 read-only tools (mcp_server.py
   + mcp_client.py)`. `check_five_readonly_tools()` re-does the source
   inspection above on every release-gate run and fails the whole gate
   if the server or client tool set ever changes, or if a tool name
   contains a write verb. Save as
   `evidence/day10-five-tools-source-check.png` (or paste the text).

3. **Inspector evidence — the protocol-level view a client sees.**
   Follow `docs/v3_inspector_walkthrough.md` (Day 6, Lab 1):
   ```bash
   npx @modelcontextprotocol/inspector python mcp_server.py
   ```
   Open the **Tools** panel — it lists exactly those five names and
   nothing else. Save as `evidence/day10-inspector-five-tools.png`.

4. **The running SDK agrees.**
   ```bash
   python -m pytest -q tests/test_mcp_sdk_contract.py
   ```
   `test_mcp_server_exposes_all_five_discovery_tools` calls the server's
   own `list_tools()` and asserts the exact list; the `health_check`
   response reports `tool_count: 5` and `mode: "read-only"`. Save as
   `evidence/day10-sdk-contract-tests.png` (or paste the text).

Day 10 Lab 4 assembles the broader final screenshot set (protocol,
product, and verification layers); this section is scoped to the single
tool-set claim.

---

# AgentGuard v3 — Day 10: Final evidence capture (protocol · product · verification)

"It works" is three separate claims — the protocol boundary is real, the
product behaves, and the automated checks pass — and they can fail
independently. This is the complete set to capture for a demo or an
interview, one screenshot (or pasted text) per item, grouped by layer.
Every screenshot must show only synthetic data and must not show a `.env`
file, an API key, or a token.

## Layer 1 — Protocol (MCP Inspector)

The wire-level view: exactly what a client sees over STDIO. Exact expected
values for every call are in `docs/v3_inspector_walkthrough.md`.

1. **Inspector is available.**
   ```bash
   npx @modelcontextprotocol/inspector --help
   ```
   Prints usage (`--web`, `--cli`, `--tui`, `-h`), no error. Save as
   `evidence/day10-inspector-help.png` (or paste the text).

2. **The five-tool list.**
   ```bash
   npx @modelcontextprotocol/inspector python mcp_server.py
   ```
   Open the printed local URL, click **Connect**, open the **Tools**
   panel — exactly five names: `health_check`, `list_agent_inventory`,
   `get_agent_by_name`, `list_tool_catalog`, `list_agent_ownership`. Save
   as `evidence/day10-inspector-tools.png`.

3. **Each tool's response.** Call and capture:
   - `health_check` → `status: "ok"`, `mode: "read-only"`, `tool_count: 5`
     → `evidence/day10-inspector-health-check.png`.
   - `list_agent_inventory` → `count: 3`; `source_name: "agents.json"`;
     `source_sha256` is 64 hex characters (note this value for the
     cross-layer check below) → `evidence/day10-inspector-list-agent-inventory.png`.
   - `get_agent_by_name` with `{"agent_name": "Research Agent"}` →
     `agent.owner: "Product Research"` →
     `evidence/day10-inspector-get-agent-by-name.png`.

4. **Failures stay safe.** On `get_agent_by_name`, try `{"agent_name": ""}`
   and `{"agent_name": 123}` — both return a clean `Error executing tool
   get_agent_by_name` with no file path and no `Traceback`. Save as
   `evidence/day10-inspector-invalid.png`.

## Layer 2 — Product (`streamlit run app_v3.py`)

What an operator actually sees.

```bash
streamlit run app_v3.py
```

1. **The boundary and the journey.** Capture the ⚠️ safety-boundary panel
   and the six-row "discovery journey" table (the Trust column marks where
   untrusted data enters, where it is validated, and where risk is
   decided) → `evidence/day10-app-journey.png`.

2. **A discovery, direct path.** Pick **Direct core (debug)**, click
   **Discover and scan**. Capture the Provenance table (source file, the
   full 64-char SHA-256, the correlation ID), the green "hash and
   correlation ID … match the raw inventory" line, the *Agents scanned 3 /
   HIGH risk 2* metrics, the risk table, one expanded per-agent finding
   (e.g. Customer Support Agent), and the "a `discovery_complete` audit
   event was appended" caption → `evidence/day10-app-direct.png`.

3. **Same result over the real protocol.** Switch to **MCP client/server**,
   click **Discover and scan** again. The risk table and the SHA-256 are
   identical to step 2 — the transport changed, the result did not. Save
   as `evidence/day10-app-mcp.png`.

4. **A safe error.** In another terminal, temporarily move the source file
   aside, then click **Discover and scan**:
   ```bash
   mv connected_environment/agents.json connected_environment/agents.json.bak
   # ... click Discover and scan, capture the screen ...
   mv connected_environment/agents.json.bak connected_environment/agents.json
   ```
   The page shows one plain sentence plus `Error category: ValueError` —
   no traceback, no file path. Save as `evidence/day10-app-safe-error.png`.

## Layer 3 — Verification (tests, evals, gate)

The automated proof. One screenshot or pasted text each.

```bash
python -m pytest -q                    # every unit test  -> "220 passed" (or current)
python scripts/run_mcp_live_smoke.py   # real client <-> real server:
                                       #   MCP LIVE SMOKE PASS / Health: ok read-only / Discovered agents: 3
python evals/run_v3_evals.py           # six [PASS] lines + "V3 SECURITY EVAL SUITE PASS"
python scripts/run_release_gate.py     # everything, one line: "RELEASE GATE PASS for AgentGuard v3"
```

Save as `evidence/day10-verify-pytest.png`, `-smoke.png`, `-v3-evals.png`,
`-release-gate.png`.

## The cross-layer check

The same fact, seen three ways — this is what shows the layers describe one
system, not three:

```bash
shasum -a 256 connected_environment/agents.json
```

The 64-character digest printed here must equal the `source_sha256` in the
Inspector `list_agent_inventory` response (Layer 1, step 3) **and** the
SHA-256 in the app's Provenance table (Layer 2, step 2).

---

# AgentGuard v3 — Day 10: The five-minute demo

A rehearsable walkthrough that *proves* the trust model — connected
discovery, provenance, deterministic policy scanning, and the security
controls — not just shows a working app. Practise it against a timer; it
should finish under 5:00.

## Before you start

- `source .venv/bin/activate` in a terminal at the repo root.
- `streamlit run app_v3.py` already open in a browser tab.
- A second terminal ready, in the repo root.
- `connected_environment/agents.json` present (not renamed from a prior run).
- **Nothing sensitive on the shared screen** — no `.env` file open, no
  terminal showing an API key or token.

## The script — six beats

| Time | Do | Say (the point) |
|---|---|---|
| 0:00–0:30 | The app is already on screen. | "v1 scored agents from a local JSON file. A real agent registry is a separate system you don't control and can't implicitly trust. v3 connects to it over a **read-only MCP boundary** — and v1's deterministic scanner still makes every risk decision, completely unchanged." |
| 0:30–1:30 | Scroll to the **discovery journey** table. Pick **Direct core (debug)**, click **Discover and scan**. Then switch the radio to **MCP client/server** and click **Discover and scan** again. | "The journey table marks where untrusted data enters and where it's validated. The debug path runs the discovery logic in this process — no protocol, my control group. The MCP path starts `mcp_server.py` as a subprocess, verifies the server exposes exactly the five expected read-only tools, and calls one. **Same risk table both times** — the transport changed, the result didn't." |
| 1:30–2:30 | Point at the **Provenance** panel. In the second terminal: `shasum -a 256 connected_environment/agents.json`. | "Source file, the full 64-character SHA-256 of the exact bytes, and a correlation ID. The digest in the terminal matches the panel — anyone can re-verify precisely which bytes were scanned. The correlation ID ties this one scan together across the server, the adapter, the scanner, and the audit log." |
| 2:30–3:30 | The risk table: **2 HIGH, 1 NO RISK FOUND**. Expand **Customer Support Agent**. | "These are v1's five deterministic rules, AG-001 through AG-005 — the same code and the same scores as v1 and v2. The MCP layer changed *where* the inventory came from, never *how* it's judged. **No AI produced this number.**" |
| 3:30–4:30 | Terminal: `mv connected_environment/agents.json connected_environment/agents.json.bak`, click **Discover and scan**, watch the error, then `mv connected_environment/agents.json.bak connected_environment/agents.json`. Then: `python scripts/validate_starter_kit.py`. | "When it fails, the page shows one plain sentence and an error category — no traceback, no file path. Three controls you don't see because they just work: the fixed three-file allowlist, the pre-resolve symlink check, and the adapter's size limits. And the release gate re-checks from source, every run — `MCP TOOL SET VERIFIED: 5 read-only tools`." |
| 4:30–5:00 | Terminal: `python scripts/run_release_gate.py`. | "One command proves the whole thing — v1, v2, and v3 unit tests, both evaluation suites, the secret scan. It ends `RELEASE GATE PASS for AgentGuard v3`. Read-only discovery, deterministic authority, full provenance." |

## If something breaks

Don't debug live. Use a fallback, in this order — any one still makes the point:

1. `npx @modelcontextprotocol/inspector python mcp_server.py` → the **Tools**
   panel showing exactly five names.
2. `python scripts/run_mcp_live_smoke.py` → `MCP LIVE SMOKE PASS` — the real
   client and server round trip.
3. Paste `python -m pytest -q` output — every test passing.

## What NOT to claim

- This is **synthetic data in a local demo**, not a production deployment.
- It is **not** complete asset discovery or full enterprise coverage.
- The discovery server has **no write access** and never will — there is no
  autonomous remediation in v3.
- v4's remediation is a **separate, governed workflow with human approval and
  rollback** — not a write tool added to the discovery server.
- Any live external integration must be verified on your own machine with
  dedicated test accounts.

---

# AgentGuard v4 — Day 1 Evidence

Day 1 has no application to screenshot yet — it's setup, orientation, and one
design document, exactly like v2's and v3's Day 1. Its evidence package is four
small, reproducible proof points: a command you can re-run plus the file it
touches, not a claim you have to take on faith.

1. **A separate branch with a baseline commit (Lab 4).**
   ```bash
   git log --oneline --all --decorate
   ```
   Expect: `main` still at `f813e24 Add V4 course prompts and lab index`, and
   `v4-development` one commit ahead at `517db77 Complete Day 1 setup: V4
   orientation and prompt adjustments`. Save as
   `evidence/day01-branch-and-commit.png` (or paste the text output). The Day 1
   Lab 5–8 updates (the release-gate rename, `docs/v4_architecture.md`, and the
   later learning-log entries) sit on top of that commit as working-tree
   changes, not yet committed.

2. **The full v1–v3 release gate passing (Lab 5).**
   ```bash
   python scripts/run_release_gate.py
   ```
   Expect the run to end `RELEASE GATE PASS for AgentGuard v4` — every unit test
   passing (874 at completion), the v2 evaluation matrix passed, the v3
   six-category security suite passed, the secret scan clean, and the
   source-only "exactly five read-only tools" check verified. Save as
   `evidence/day01-release-gate.png` (or paste the text output). At the start of
   v4 this was the inherited v1–v3 baseline; the only change from v3's gate then
   was the version string it prints.

3. **The v4 state machine and trust-boundary design (Lab 7).**
   The file itself: `docs/v4_architecture.md`. No command to run — save a
   screenshot of the state diagram and the per-state
   *data / authority / gate* table, or just keep the file as the evidence. It
   records, before any action-layer code exists, what the system may do at each
   workflow state and which check must pass to move forward.

4. **The Day 1 learning log (Labs 1–8).**
   The file itself: `notes/learning_log.md`. Its "Day 1 Summary — Labs 1 through
   8" entry indexes what was learned in each lab — the readable record a
   beginner or an interviewer can point to without re-reading every entry.

---

# AgentGuard v4 — The no-production pledge

v4 is the first version that can *change* an agent's configuration. This is the
written commitment about what that capability will and will not touch. Every
item is enforced by code built later in the course, not left to good intentions;
this section is the checklist an auditor or interviewer can hold the project to.

- **Synthetic data only.** Every agent, tool, and ownership record is fabricated
  for the demo. No real cloud account, identity provider, or agent registry is
  ever contacted.
- **A dedicated demo repository, never production.** GitHub work targets one
  private repository created only for this training (Day 2). It is never the
  AgentGuard source repository and never a production system. The repository,
  the branch-name prefix, and the single target file path are all on a fixed
  allowlist; anything else is refused.
- **Draft pull requests only.** There is no merge command anywhere in the code.
  A remediation reaches GitHub only as a draft PR that a human must review and
  merge by hand.
- **Dry-run by default.** The GitHub step prints the exact commands it would run
  and changes nothing. Live execution is a separate, explicit opt-in.
- **Isolated verification.** A proposal is applied only to a throwaway temporary
  copy of the environment for re-scanning. The source data is never modified in
  place.
- **The discovery boundary stays read-only.** The MCP server keeps exactly five
  read-only tools; v4 adds no write tool to it. The remediation workflow is a
  separate component — see `docs/v3_to_v4_handoff.md`.
- **No autonomous remediation.** A human approval, cryptographically bound to
  the exact proposal and the exact source it was built from, gates every applied
  change. The AI layer may explain a finding and propose a remediation; it may
  never approve, apply, verify, or score.
- **Deterministic authority is unchanged.** v1's `scanner.py` remains the sole
  authority for the risk score, from v1 through v4. A proposal *predicts* a
  score; it never sets one.
- **Live steps are the user's to run.** Any real external action (installing
  `gh`, authenticating, creating the demo repo, opening a real draft PR) is
  performed by the user on their own machine with a dedicated test account, and
  only when a lab explicitly calls for it.

---

# AgentGuard v4 — Day 10: Final evidence capture (protocol · product · verification)

"It works" is three separate claims — the protocol boundary is real, the product
behaves, and the automated checks pass — and they can fail independently. This is
the complete set to capture for a demo, a recording, or an interview: one
screenshot (or pasted text) per item, grouped by layer. It mirrors v3's Day 10
capture, extended for the governed-remediation workflow.

## Before you capture anything — the credential-safety checklist

The learning goal for this lab is *showing the system without exposing
credentials*. A demo that touches GitHub is exactly where a secret leaks onto a
shared screen or into a recording. **Nothing in this list may appear in any
screenshot, paste, or video frame:**

- a `.env` file, open in an editor or shown by `cat` / `ls -la` — it holds the
  optional `ANTHROPIC_API_KEY`;
- any `ANTHROPIC_API_KEY=...` line, in a terminal, an env dump (`env`,
  `printenv`), or a shell prompt;
- any string shaped like `sk-ant-...`, `github_pat_...`, or `gho_` / `ghp_` /
  `ghs_` / `ghr_` / `ghu_` followed by a long token body;
- the `Token:` line from `gh auth status` (the app's `gh auth` panel already
  strips it — capture the panel, not the raw command);
- the contents of `~/.config/gh/` or `~/.ssh/`;
- a browser password manager, an autofill dropdown, or a "save password" prompt;
- shell history (`history`, a scrollback buffer) containing any of the above.

Before recording: open a fresh terminal, close editor tabs and browser tabs that
could hold a secret, and confirm every data value on screen is synthetic (the
three demo agents, the `justintinlei/agentguard-remediation-demo` repo). If in
doubt, don't show it.

## Layer 1 — Protocol (MCP Inspector)

The wire-level view — unchanged from v3, because v4 adds no tool. Exact expected
values for every call are in `docs/v3_inspector_walkthrough.md`.

```bash
npx @modelcontextprotocol/inspector python mcp_server.py
```

Open the printed local URL, click **Connect**, open the **Tools** panel:

1. **Exactly five read-only tools** — `health_check`, `list_agent_inventory`,
   `get_agent_by_name`, `list_tool_catalog`, `list_agent_ownership`, and nothing
   else. Save as `evidence/day10-v4-inspector-tools.png`.
2. **`health_check`** → `status: "ok"`, `mode: "read-only"`, `tool_count: 5`.
   Save as `evidence/day10-v4-inspector-health.png`.
3. **`list_agent_inventory`** → `count: 3`; `source_name: "agents.json"`;
   `source_sha256` is 64 hex characters — note it for the cross-layer check.
   Save as `evidence/day10-v4-inspector-inventory.png`.

## Layer 2 — Product (`streamlit run app_v4.py`)

What an operator actually sees. The whole governed remediation journey in one
page.

```bash
streamlit run app_v4.py
```

1. **The boundary and the journey map.** Capture the "Safety boundary" bullet
   list and the six-stage "v4 remediation journey" map (Discovery → Proposal →
   Approval → Verification → Plan → Audit), each stage tied to a real
   `workflow.STATES` token. Save as `evidence/day10-v4-app-journey.png`.

2. **Build a proposal.** Agent = **Customer Support Agent**, template =
   **REQUIRE_HUMAN_APPROVAL**, click **Build proposal**. Capture the proposal
   JSON (`field_changes: {"human_approval_required": true}`), the **Proposal
   SHA-256**, and the **Source SHA-256**. Save as
   `evidence/day10-v4-app-proposal.png`.

3. **Approve and verify.** Reviewer name, a decision reason, decision =
   **APPROVE**, click **Approve & verify**. Capture:
   - the **Content hashes** block — the exact proposal and source SHA-256 the
     approval is bound to;
   - the **Approval record** (`decision: APPROVE`, the reviewer, both hashes)
     and the "still current: True" caption;
   - the **Verification** summary — `Verification PASSED (10/10 checks)` and the
     `HIGH-risk agents: before 2 -> after 1` caption;
   - the **Event timeline** — `PROPOSED` → `APPROVED` → `VERIFIED`.
   Save as `evidence/day10-v4-app-approve-verify.png`.

4. **The GitHub dry-run plan.** For the VERIFIED run, capture the five commands
   (`git checkout -b agentguard/<id>` → `git add …` → `git commit -m …` →
   `git push -u origin agentguard/<id>` → `gh pr create --draft …`), the
   `DRY_RUN` status on every row, and the `GITHUB_SAFETY_WARNINGS` bullets. Save
   as `evidence/day10-v4-app-dry-run-plan.png`.

5. **The `gh auth` panel — authenticated, no token.** Capture the "GitHub CLI
   authentication" panel. It shows `gh` is authenticated **and shows no
   credential** — the panel runs `gh auth status` and strips the `Token:` line
   before display (`app_v4._strip_token_lines`). This is the "show it without
   exposing it" point, on screen. Save as `evidence/day10-v4-app-gh-auth.png`.

## Layer 3 — Verification (tests, evals, gate)

The automated proof. One screenshot or pasted text each.

```bash
python -m pytest -q                    # every unit test  -> "874 passed" (or current)
python evals/run_v2_evals.py           # "V2 EVALUATION PASS: 3 of 3 cases passed"
python evals/run_v3_evals.py           # six [PASS] lines + "V3 SECURITY EVAL SUITE PASS"
python evals/run_v4_evals.py           # ten PASS lines + "10 of 10 checks held (fails closed)"
python scripts/run_release_gate.py     # everything, one line: "RELEASE GATE PASS for AgentGuard v4"
python -m compileall -q .              # no output, exit 0
```

Save as `evidence/day10-v4-verify-pytest.png`, `-v2-evals.png`, `-v3-evals.png`,
`-v4-evals.png`, `-release-gate.png`.

## The cross-layer check

The same fact, seen three ways — this is what shows the layers describe one
system, not three:

```bash
shasum -a 256 connected_environment/agents.json
```

The 64-character digest printed here must equal the `source_sha256` in the
Inspector `list_agent_inventory` response (Layer 1, step 3) **and** the Source
SHA-256 shown in the app after building a proposal (Layer 2, step 2).

---

# AgentGuard v4 — Day 10: The five-minute demo (video plan)

A rehearsable walkthrough that *proves* the governed-remediation trust model —
deterministic finding, bounded proposal, exact-hash approval, isolated
verification, draft-only delivery — not just shows a working app. Practise it
against a timer; it should finish under 5:00.

## Before you start

- Run the **credential-safety checklist** above. In particular: no `.env` open,
  no terminal showing an API key or a `gh` token, no browser password UI.
- `source .venv/bin/activate` in a terminal at the repo root.
- `streamlit run app_v4.py` already open in a browser tab.
- A second, clean terminal ready in the repo root.
- `connected_environment/agents.json` present (not renamed from a prior run).

## The script — six beats

| Time | Do | Say (the point) |
|---|---|---|
| 0:00–0:40 | The app is on screen. Scroll the "Safety boundary" list and the six-stage journey map. | "v1 through v3 only ever *read and scored* agent risk. v4 can *change* an agent's config — on synthetic data, through a draft pull request. The rule: deterministic code decides *what* to fix, software verifies it, a human approves *intent*, and the AI layer only ever explains or proposes. v1's scanner is still the only thing that sets a risk score." |
| 0:40–1:40 | Agent = **Customer Support Agent**, template = **REQUIRE_HUMAN_APPROVAL**. Click **Build proposal**. Point at the proposal JSON and the two SHA-256 lines. | "The scanner flagged this agent HIGH — it can delete customer records and read sensitive data with no human gate. The fix is one of exactly three allowlisted templates — never a free-form AI patch. The proposal is one bounded field change, and we hash *both* the exact source inventory and the exact proposal." |
| 1:40–2:50 | Reviewer name, a reason, decision **APPROVE**, click **Approve & verify**. Point at the Content hashes, the Approval record, the Verification checklist, the timeline. | "A named person approves — and the approval is cryptographically bound to those two hashes, so if the proposal or the source changes, this approval is stale and the workflow fails closed. Then *software*, not the human, verifies: it applies the change to a throwaway copy and re-scans. Ten of ten checks pass, and the HIGH-risk count drops from two to one." |
| 2:50–3:40 | Scroll to the GitHub dry-run plan. Read the five commands and the warnings. | "This is the delivery step, and by default it *runs nothing* — it shows the exact five commands. Four `git` steps that stay on an `agentguard/` branch, then `gh pr create --draft`. There is no merge command anywhere in the codebase. A live run is a separate, deliberate opt-in the page itself can never trigger." |
| 3:40–4:20 | Point at the "GitHub CLI authentication" panel. In the second terminal: `shasum -a 256 connected_environment/agents.json`. | "The app confirms GitHub access works and shows no token — it reads `gh auth status` and strips the credential line. And this digest in the terminal matches the Source SHA-256 on the page: anyone can re-verify exactly which bytes were scanned and approved." |
| 4:20–5:00 | Second terminal: `python scripts/run_release_gate.py`. | "One command re-proves every layer — v1–v4 unit tests, the v2, v3, and v4 evaluation suites, the secret scan. The v4 eval injects ten bad inputs — a skipped state, a post-merge rollback, an unapproved repo — and passes only because v4 *refuses* each. It ends `RELEASE GATE PASS for AgentGuard v4`." |

## If something breaks

Don't debug live. Use a fallback, in this order — any one still makes the point:

1. `python evals/run_v4_evals.py` → the ten `PASS` lines and
   `10 of 10 checks held (fails closed)`.
2. `python -m pytest -q` → every test passing.
3. The dry-run plan JSON from a prior run — the five commands, every one
   `DRY_RUN`.

## What NOT to claim

- This is **synthetic data in a local demo**, not a production deployment.
- It is **not** complete enterprise agent discovery or full coverage.
- The AI layer **never** approves, applies, verifies, or scores — it explains
  and proposes only. `scanner.py` is the sole risk-score authority.
- The GitHub step is **dry-run by default and draft-only**; the one live draft
  PR is a separate, explicitly approved manual step, and **there is no merge
  command in the code**.
- There is **no autonomous remediation** — every applied change is gated by a
  human approval bound to the exact reviewed content.
- Any live external action must be run on your own machine with a dedicated
  test account.
