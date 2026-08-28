# AgentGuard roadmap

## v1 — Local Policy Scanner (done)
Local JSON inventory, five deterministic rules (AG-001–AG-005), a Streamlit
UI, and four pytest tests. This is the verified baseline this v2 folder was
copied from — its scoring logic does not change in v2.

## v2 — Grounded AI Analyst (done)
Adds a Claude API explanation layer on top of the v1 scanner: it retrieves
relevant policy passages (RAG), asks Claude — or a free deterministic mock
analyst — for a structured explanation with citations, and validates every
citation before it reaches the screen. The model explains findings; it
never sets or changes the risk score, since that authority stays with v1's
deterministic rules.

**v2's finish line:** a local app where a synthetic agent shows (1) v1's
unchanged deterministic score and (2) a validated, cited AI explanation,
running in a free "mock" mode by default with an optional paid "live" mode.
Reached and verified — this is the frozen baseline the v3 folder was copied
from.

## v3 — Connected Agent Discovery (this project, Day 1–10)
A read-only MCP server/client that discovers real agent and tool metadata
under an allowlist and audit log, instead of reading a local JSON file. A
local file stands in for inventory but not for how a real enterprise
integration works — there's no network boundary, no allow/deny list, no
auditable request. MCP gives that a controlled protocol boundary instead of
direct file access.

**v3's finish line (reached — Day 10 release candidate):** the same app,
still scored only by v1's unchanged deterministic rules, but now fed by a
read-only MCP server/client pair that discovers agent and tool metadata
under an allowlist, with every request logged. `python
scripts/run_release_gate.py` ends `RELEASE GATE PASS for AgentGuard v3`.

## v4 — Governed Remediation MVP (future)
Minimal remediation proposals that require human approval, get verified,
and can be rolled back, with full audit evidence.
