# AgentGuard V3 to V4 Handoff — Governed Actions

v3 changed *where* agent inventory comes from: a read-only MCP client/server
boundary instead of a local file. v4 adds the ability to *change* an agent's
configuration — remediation. This document records how v4 does that without
breaking a single guarantee v3 established, in the same checklist shape
`docs/v2_to_v3_handoff.md` used for the v2 to v3 transition.

## The one decision this handoff is about

v4 does **not** add a write tool to the MCP discovery server. It adds a
**separate governed-action workflow**: propose → human approval → verified apply
→ rollback, with an audit record at every step. The discovery server stays
exactly what it is today — five read-only tools, no mutation capability.

### Why not just add a sixth tool

Adding a `remediate_agent` tool to `mcp_server.py` looks cheap — the server
already talks to the registry. It is not cheap. Everything below currently
depends on the server having *no* way to change anything:

- `mcp_client.py`'s five-tool allowlist and `_verify_tool_allowlist()`
- the "read-only" claim in `docs/v3_threat_model.md` §5-6
- `scripts/validate_starter_kit.py::check_five_readonly_tools()`, run on every
  release-gate invocation
- every "the server cannot write" answer in `docs/v3_interview_brief.md`

A single write tool would make all of that false in one commit. Four concrete
reasons it stays out:

1. **Blast radius.** A read-only tool that misbehaves — a bug, a wrong file —
   returns bad *data*. A write tool that misbehaves changes *production
   configuration*. The cost of a mistake goes from "re-run the scan" to "restore
   an agent's settings".
2. **Prompt injection stops being contained.** In v3, connected text is inert:
   nothing downstream of `scanner.evaluate_agent()` has the authority to act on
   it, so `"ignore this finding"` in a registry note does nothing. Put a write
   tool in the same pipeline and `"set human_approval_required to false"` in a
   note becomes a live instruction path an attacker can aim at.
3. **Authorization blurs.** Today there is one bright line: the tool allowlist.
   "Who may read" and "who may write" are the same question because there is
   only reading. Mix read and write behind one server and every caller that
   could read can now also write, unless a second, finer-grained check is added
   *inside* the server — more surface, more to get wrong.
4. **The audit story weakens.** v3's audit event records *that a read happened*
   (route, tool, source hash, correlation id, outcome). A write needs a
   fundamentally richer record — what field changed, from what value to what
   value, which human approved it, whether the result was verified, whether it
   was rolled back. That does not belong bolted onto a `discovery_complete`
   event.

Keeping writes in a separate workflow means v3's read-only server stays
*provably* read-only forever, and v4's risk is isolated to the new component.

## The v4 governed-action workflow (design, not built)

1. **Propose.** v4 emits a *proposal*: one specific, bounded change to one agent
   — e.g. "set `human_approval_required = true` on Deployment Agent" — with the
   finding it addresses and the risk score the change is expected to produce.
   Deterministic rules decide *what* to propose; an AI layer may only *explain*
   the proposal, exactly as it explains a v2 finding.
2. **Bind to approval.** A human reviews the proposal and approves *that exact
   proposal*. Approval is bound to the proposal's content hash, so an approved
   proposal cannot be silently swapped for a different change before it is
   applied.
3. **Apply, verified.** Only an approved, unmodified proposal is applied, in an
   isolated step. The result is immediately re-scanned to confirm it produced
   the state the proposal predicted.
4. **Rollback.** Every applied change stores enough to reverse it. A failed
   verification, or a later human decision, restores the prior state.
5. **Audit.** Each step writes its own event: proposed, approved (by whom, which
   hash), applied, verified, rolled back.

The MCP discovery server is not in this loop at any step. v4's AI layer may
*propose*; it may never approve, apply, verify, or set a score.

## Preconditions — before v4 starts

- [ ] `python scripts/run_release_gate.py` ends
      `RELEASE GATE PASS for AgentGuard v3`.
- [ ] the optional live check passes:
      `python scripts/run_mcp_live_smoke.py` → `MCP LIVE SMOKE PASS`.
- [ ] v3 is tagged as a restorable checkpoint (a `v3.x-rc` tag). **Not done
      yet** — v3's Day 2–10 work is still uncommitted on `v3-development`; see
      the Day 10 Lab 7 public-readiness note. Committing that backlog and
      tagging it is a human step before v4.
- [ ] the two accepted residual risks in `docs/v3_threat_model.md` ("carried to
      v4") are re-evaluated. If v4's MCP server can ever be **remote** rather
      than a local subprocess, `mcp_client._structured()`'s uncapped
      response-block parse and `read_json_with_provenance()`'s uncapped file
      read both need explicit size bounds.

## What v4 must preserve, unchanged

- [ ] `scanner.py` — v1's deterministic scoring stays the **sole** risk
      authority. A proposal may *predict* a new score; it may never *set* one.
- [ ] `mcp_server.py` / `mcp_client.py` — exactly five read-only discovery
      tools; `check_five_readonly_tools()` still passes.
- [ ] `discovery_adapter.py` — the field presence / type / size validation
      boundary between connected data and the scanner.
- [ ] the AI boundary from v2: the model may explain and cite, and may now also
      *propose*; it may never approve, apply, or score.
- [ ] `audit_log.py` — the existing `analysis_complete` and `discovery_complete`
      event fields keep their shape. v4 adds new event *types* alongside them; it
      does not change the old ones.

## What this lab did not do

No v4 code. No write tool. No `remediate_*` MCP tool. No git tag. This document
only records the boundary so v4 starts from an explicit agreement about where
write capability lives and how it is governed — exactly as
`docs/v2_to_v3_handoff.md` did for v3.
