# START HERE — AgentGuard v4

AgentGuard v4 — **Governed Remediation MVP** — is the finished portfolio
project. It continues from the verified, frozen v2 and v3 baselines and adds a
bounded, human-approved, verified, auditable remediation workflow that delivers
change only as a **draft pull request** on a dedicated synthetic repository. It
adds no write tool to v3's read-only discovery server.

See [`README.md`](README.md) for the full picture,
[`docs/v4_architecture.md`](docs/v4_architecture.md) for the state-by-state
authority table, and [`docs/roadmap.md`](docs/roadmap.md) for how v1–v4 fit
together.

1. Work only inside `~/Developer/AgentGuard/01-Working/agentguard-v4`.
2. Activate the environment: `source .venv/bin/activate`.
3. The Day 1 through Day 10 labs (80 in total) are complete. Each lab's
   step-by-step details live in [`docs/lab_execution_index.md`](docs/lab_execution_index.md);
   the matching Claude Code prompt is in `prompts/course_labs/`.
4. Stay in mock mode (no paid API calls) unless a lab explicitly says to run a
   live Claude call, and only ever store an API key in `.env` (never in code or
   chat).
5. Keep GitHub execution in **dry-run** until the optional draft-PR lab
   (Day 10 Lab 3) — and separately approve that one live action.
6. Run `pytest -q` after any code change to confirm v1, v2, and v3 behavior are
   still intact — v4 is not allowed to break any of them.
7. Re-verify the whole build with one command:
   `python scripts/run_release_gate.py` — it ends
   `RELEASE GATE PASS for AgentGuard v4`.
8. The invariant to protect:
   - the MCP discovery server stays **read-only** and exposes **exactly five
     tools** (`health_check`, `list_agent_inventory`, `get_agent_by_name`,
     `list_tool_catalog`, `list_agent_ownership`);
   - remediation is **exactly three allowlisted templates** — never a free-form
     AI patch;
   - only v1's `scanner.py` ever sets a risk score — a proposal *predicts* one;
   - GitHub work is dry-run by default, draft-only, on the one allowlisted demo
     repo, with **no merge command anywhere in the code**.
