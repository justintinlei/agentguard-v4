# AgentGuard V2 to V3 Handoff Checklist

v3 changes *where* agent inventory comes from. It never changes *who
decides the risk score* — that authority stays with v1's deterministic
scanner regardless of version. This checklist exists so that invariant
survives the transition on purpose, not by accident.

## Before starting v3

- [ ] v2's release gate passes: `python scripts/run_release_gate.py` ends
      in `RELEASE GATE PASS`
- [ ] v2 is tagged as a restorable checkpoint (already true: `v2.0.0-rc1`)
- [ ] No open, unresolved security findings from v2's review (already
      true: the one finding from Day 9 · Lab 6 was fixed and committed in
      isolation)

## What v3 must preserve, unchanged

- [ ] `scanner.py` — v1's deterministic scoring stays the **sole** risk
      authority; nothing in v3 may set or override a score
- [ ] `policy_library.py` — policy chunk loading, splitting, and hashing
- [ ] `retrieval.py` — the retrieval/scoring logic that selects evidence
- [ ] `grounding.py` — the grounding validator: score preservation and
      citation authenticity checks, both unchanged
- [ ] `mock_analyst.py` — the free, deterministic analyst stays available
      and stays the default
- [ ] `claude_analyst.py` — the live Claude adapter and its cost controls
      (token cap, low effort, timeout)
- [ ] `audit_log.py` — the audit event fields and format
- [ ] `evals/v2_cases.json` — the existing evaluation cases keep passing

## What v3 changes

- [ ] Replace direct local JSON file reads (`sample_environment_*.json`)
      with agent/tool discovery via an MCP server/client
- [ ] Discovery is **read-only** — v3 may discover agent and tool
      metadata, never mutate it
- [ ] Discovery is bounded by an **allowlist** — only pre-approved
      agents/tools are discoverable, the same fixed-corpus philosophy
      already used for policy retrieval in v2
- [ ] Every discovery call is captured in an **audit log**
- [ ] The one invariant that does not change: v3 changes the *source* of
      inventory, never the risk authority

## What this lab did not do

No MCP code was written — no `mcp_server.py`, no `mcp_client.py`. Building
the read-only MCP boundary is v3's actual job, not this checklist's; this
document only records the boundary so that work starts from an explicit
agreement instead of an assumption.
