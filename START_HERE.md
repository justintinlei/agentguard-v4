# START HERE — AgentGuard v3

This folder continues from the verified, frozen AgentGuard v2 baseline. V3
**replaces** v2's local-file inventory source with a read-only MCP (Model
Context Protocol) client/server boundary — complete as of the Day 10 release
candidate. v1's deterministic scanner stays the sole authority for risk; only
where the inventory comes from changed. See `docs/roadmap.md` for how this fits
with v1/v2/v4, and `docs/v3_architecture.md` for the data flow and a box-by-box
reproduce guide.

1. Work only inside `~/Developer/AgentGuard/01-Working/agentguard-v3`.
2. Activate the environment: `source .venv/bin/activate`.
3. The Day 1 through Day 10 labs are all complete. Each lab's step-by-step
   details live in `docs/lab_execution_index.md`; the matching Claude Code
   prompt is in `prompts/course_labs/`.
4. Stay in mock mode (no paid API calls) unless a lab explicitly says to run a
   live Claude call, and only ever store an API key in `.env` (never in code or
   chat).
5. Run `pytest -q` after any code change to confirm v1's and v2's behavior are
   still intact — v3 is not allowed to break either.
6. Re-verify the whole build with one command:
   `python scripts/run_release_gate.py` — it ends
   `RELEASE GATE PASS for AgentGuard v3`.
7. The invariant to protect: the discovery server stays **read-only** and
   exposes **exactly five tools** (`health_check`, `list_agent_inventory`,
   `get_agent_by_name`, `list_tool_catalog`, `list_agent_ownership`), and only
   v1's scanner ever sets a risk score.
