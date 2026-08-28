# AgentGuard v3 — MCP Connected Discovery

AgentGuard keeps v1's deterministic security scan as the single, unchanged
source of truth for risk. v3 changes only **where the agent inventory comes
from**: instead of the UI reading a local JSON file, a read-only MCP (Model
Context Protocol) 2.x server/client pair discovers the inventory under a fixed
allowlist, with a SHA-256 provenance hash and an audit trail on every request.
This is a synthetic training demo — no real systems, accounts, or data are
involved.

## What v3 adds over v2

- A **read-only MCP server** (`mcp_server.py`) exposing **exactly five**
  discovery tools over STDIO: `health_check`, `list_agent_inventory`,
  `get_agent_by_name`, `list_tool_catalog`, `list_agent_ownership`. There is no
  create, update, or delete tool.
- An **independent MCP client** (`mcp_client.py`) that refuses any server whose
  advertised tool set is not exactly those five.
- A **strict validation adapter** (`discovery_adapter.py`): every discovered
  record is checked for field presence, correct type, and documented size limits
  before it can reach v1's scanner.
- **Provenance** on every discovery — the SHA-256 of the exact source bytes plus
  a correlation ID — shown in the UI and written to the audit log.
- **`app_v3.py`** — a Streamlit page with two discovery paths (a direct in-process
  "debug" path and the full MCP client/server path), safe traceback-free error
  messages, and the provenance + risk display.

v1's `scanner.py` and v2's grounded analyst (`v2_service.py`) are **unchanged**.
Only the inventory source and the UI around it are new.

## End-to-end flow

```
Synthetic connected registry (3 JSON files, connected_environment/)
  -> read-only MCP server        (STDIO, 5 tools, fixed file allowlist, SHA-256 provenance)
  -> independent MCP client      (refuses any tool set that isn't exactly the 5)
  -> validation adapter          (fields, types, size limits; provenance preserved)
  -> v1 deterministic scanner    [UNCHANGED — the sole risk authority]
  -> v2 policy retrieval + grounded explanation   [UNCHANGED]
  -> Streamlit UI + audit log    (now also records the source hash + correlation ID)
```

Full picture and the trust-boundary table: [`docs/v3_architecture.md`](docs/v3_architecture.md).
Abuse cases and how each is blocked: [`docs/v3_threat_model.md`](docs/v3_threat_model.md).

## Reproduce the integration

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/verify_setup.py          # runtime + current MCP 2.x imports
python scripts/run_release_gate.py       # the full gate — see below
python scripts/run_mcp_live_smoke.py     # real client <-> real server, once, end to end
streamlit run app_v3.py                  # the product
```

Everything runs in free, deterministic **mock mode** by default — no network
call, no cost, no API key. Live Claude mode (v2's analyst layer) is optional,
billed per token, and only ever reads a key from a local, git-ignored `.env`.

Optional protocol-level view:

```bash
npx @modelcontextprotocol/inspector python mcp_server.py
```

Open the **Tools** panel — it lists exactly those five names. Step-by-step in
[`docs/v3_inspector_walkthrough.md`](docs/v3_inspector_walkthrough.md).

## Reviewed release result

- 80 labs (Day 1–10), each with a matching Claude Code prompt file in
  `prompts/course_labs/`.
- 214 pytest test functions, all passing (`python -m pytest -q`).
- v2 evaluation: 3 of 3 cases pass.
- v3 security evaluation: 6 of 6 threat-model categories pass —
  `python evals/run_v3_evals.py` ends in `V3 SECURITY EVAL SUITE PASS`.
- Starter-kit validation (including the source-only "exactly five read-only
  tools" check) and the secret scan both pass.
- `python scripts/run_release_gate.py` ends in
  `RELEASE GATE PASS for AgentGuard v3`.

## Inherited V2 baseline (verified, frozen)

v3 builds on the completed v2 project without changing it. v1's five
deterministic rules (`AG-001`–`AG-005`) produce a score and a rule ID; v2 adds a
plain-English explanation tied to real, hashed policy text, with every citation
checked before it is shown and any model attempt to change the score rejected.
That pipeline — retrieval, model, grounding validator, UI — can only read,
explain, check, or display; only v1's scanner ever sets the score. Full v2
diagram and abuse cases: [`docs/v2_architecture.md`](docs/v2_architecture.md) and
[`docs/v2_threat_model.md`](docs/v2_threat_model.md). v2 shipped tagged
`v2.0.0-rc1`.

## Learn more

- [`START_HERE.md`](START_HERE.md) — course navigation and how to re-verify the build
- [`docs/lab_execution_index.md`](docs/lab_execution_index.md) — the authoritative map of every lab
- [`docs/v3_architecture.md`](docs/v3_architecture.md) — trust boundaries, data flow, and a box-by-box reproduce guide
- [`docs/v3_threat_model.md`](docs/v3_threat_model.md) — the seven abuse categories and their tests, plus accepted residual risks
- [`docs/v3_data_contract.md`](docs/v3_data_contract.md) — the exact shape and size limits a connected registry must supply
- [`docs/v3_mcp_setup.md`](docs/v3_mcp_setup.md) — Python + Node environment for MCP
- [`docs/v3_inspector_walkthrough.md`](docs/v3_inspector_walkthrough.md) — driving the MCP Inspector
- [`docs/v3_interview_brief.md`](docs/v3_interview_brief.md) — eight likely interview questions answered from the real code
- [`docs/v3_to_v4_handoff.md`](docs/v3_to_v4_handoff.md) — why v4 governs writes through proposals + approval instead of a write tool
- [`evidence/README.md`](evidence/README.md) — how to verify and save proof of each claim above yourself
- [`docs/roadmap.md`](docs/roadmap.md) — the full v1–v4 plan

## Safety boundaries

See `CLAUDE.md` for the full list. In short: everything here runs locally, no
real credentials or accounts are involved, the MCP discovery server is read-only
and exposes exactly five tools, and only v1's deterministic rules ever set a risk
score — the AI layer explains and cites, never decides.
