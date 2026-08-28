# AgentGuard v3 Architecture — Trust Boundaries and Data Flow

This documents the v3 data flow **as built**. The design was decided across
Day 1's labs and implemented Day 4 onward; every box in the diagram below is
now a real file with tests. This is the map another engineer follows to
reproduce or extend the MCP integration, and the record of where the trust
boundary was drawn — on paper first, then in code.

## The core question this design answers

v1 and v2 both read the agent inventory from a local JSON file that ships
with the repo — implicitly trusted, because it's part of the codebase. v3
changes that: the inventory comes from a **connected** source (a separate
MCP server reading its own registry files) that isn't part of the codebase
and can't be implicitly trusted just because it responds. So the question
this design answers is: **exactly where does that untrusted data enter the
system, and exactly where does it become safe to treat like v1/v2's
original local data?**

## New terms

- **Untrusted input/data** — data whose correctness or safety can't be
  assumed just because it arrived; it must be checked before use.
- **Trust boundary** — the specific point in a system where data crosses
  from a zone that isn't fully controlled or verified into a zone that
  is. Everything before the line is treated as untrusted no matter how
  it's labeled; everything after it is trusted only because something
  specific checked it first.
- **Allowlist** — an explicit, fixed list of exactly what's permitted
  (here: three registry filenames, five tool names). Anything not on the
  list is refused outright, rather than trying to enumerate everything
  bad.
- **Validation adapter** — the code whose only job is checking untrusted
  data against exact rules (required fields, correct types, size limits)
  before it's allowed to become something the rest of the app trusts.
- **Provenance** — a record of where a piece of data came from, plus
  proof it hasn't been altered (a SHA-256 hash of the source file).
- **Correlation ID** — a unique identifier attached to one discovery
  request/response pair, so it can be traced through logs later.

## Flow diagram

```
        Connected Registry Files (synthetic JSON, on disk)
        agents.json / tool_catalog.json / ownership.json
        ══════════════════ UNTRUSTED ═══════════════════
                              │
                              ▼
                   MCP Server (read-only)
        (five allowlisted tools, STDIO transport, reads
         only the fixed three-file allowlist, returns
         each response with a SHA-256 provenance hash)
                              │
        ══════════ TRUST BOUNDARY: protocol ═══════════
                              │
                              ▼
                MCP Client (independent process)
        (checks the server's exposed tool list against
         an expected allowlist before calling anything —
         an unexpected tool name is refused, not trusted)
                              │
                              ▼
                  Validation Adapter (strict)
        (checks every required field, type, and size;
         preserves the source hash + correlation ID;
         rejects anything malformed BEFORE it becomes
         an "agent" the rest of the app can see)
                              │
        ══════════ TRUST BOUNDARY: data ═══════════════
                              │
                              ▼
          v1 Deterministic Scanner — UNCHANGED
        (same five rules, same scoring logic; doesn't
         know or care whether data came from a local
         file or a validated MCP response)
                              │
                              ▼
     v2 Policy Retrieval + AI Explanation — UNCHANGED
                              │
                              ▼
                       Streamlit UI
                              │
                              ▼
              Audit Log (now also records the
              source hash + correlation ID per
              discovery, alongside v2's existing fields)
```

## Where untrusted data enters, and where it becomes trusted

| Stage | Trust level | What happens |
|---|---|---|
| Connected registry files | **Untrusted** | Synthetic files outside the codebase — nothing here guarantees they're well-formed or unmodified. |
| MCP Server | Untrusted boundary is crossed here, but containment starts | Can only read the three fixed, allowlisted filenames — nothing else on disk is reachable through it. |
| MCP Client | Still untrusted-adjacent | Refuses to call any tool not on the expected allowlist, even if the server offers one. |
| Validation Adapter | **This is the real trust boundary** | Every field is checked for presence, type, and size; anything malformed is rejected here and never reaches the scanner. |
| v1 Scanner onward | **Trusted** | Identical to v1/v2's original behavior — validated data is indistinguishable from the old local-file data by this point. |

## Reproduce this integration

Every box in the diagram is a real file, and every file has a test that proves
its behaviour. To rebuild or extend the integration, read the files in flow
order:

| Diagram box | File(s) | Proven by |
|---|---|---|
| Connected registry files | `connected_environment/agents.json`, `tool_catalog.json`, `ownership.json` | shape + size limits: `docs/v3_data_contract.md` |
| MCP server (read-only, 5 tools, STDIO) | `mcp_server.py` → `discovery_core.py` → `mcp_security.py` | `tests/test_mcp_sdk_contract.py`, `test_discovery_core.py`, `test_mcp_security.py` |
| MCP client (tool-allowlist check) | `mcp_client.py` | `tests/test_mcp_client.py` |
| Validation adapter (fields, types, sizes; provenance preserved) | `discovery_adapter.py` | `tests/test_discovery_adapter.py` |
| v1 deterministic scanner (UNCHANGED) | `scanner.py` | `tests/test_scanner.py` |
| v2 retrieval + grounded explanation (UNCHANGED) | `v2_service.py`, `retrieval.py`, `grounding.py` | `tests/test_v2_service.py`, `test_retrieval.py`, `test_grounding.py` |
| Streamlit UI + audit log | `app_v3.py`, `audit_log.py` | `tests/test_app_v3.py`, `test_audit_log.py` |

Run it end to end:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/verify_setup.py            # runtime + MCP 2.x imports
python -m pytest -q                       # every box's tests
python scripts/run_mcp_live_smoke.py      # real client <-> real server over STDIO
python scripts/run_release_gate.py        # the whole gate; ends RELEASE GATE PASS for AgentGuard v3
streamlit run app_v3.py                   # the product, both discovery paths
```

The source-only "exactly five read-only tools" check
(`scripts/validate_starter_kit.py::check_five_readonly_tools`) runs inside the
release gate and re-verifies the tool set from `mcp_server.py` + `mcp_client.py`
on every run.

## The one invariant this design must never break

No matter where the inventory comes from, **only v1's deterministic
scanner ever sets the risk score.** The MCP server, the client, and the
validation adapter can only supply or reject data — none of them can score
anything, explain anything, or influence v2's AI explanation layer. That
guarantee, unchanged since Day 1 of v1, is the one thing every later v3
lab is built to protect.
