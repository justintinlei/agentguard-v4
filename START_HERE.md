# START HERE — AgentGuard v4

AgentGuard v4 — **Governed Remediation MVP** — continues from the frozen v2 and
v3 baselines and adds a bounded, human-approved, verified, auditable remediation
workflow that delivers change only as a **draft pull request** on a dedicated
synthetic repository. It adds no write tool to v3's read-only discovery server.

See [`README.md`](README.md) for the full picture,
[`docs/v4_architecture.md`](docs/v4_architecture.md) for the state-by-state
authority table, [`docs/v4_threat_model.md`](docs/v4_threat_model.md) for the
abuse categories and their controls, and
[`docs/final_mvp_interview_brief.md`](docs/final_mvp_interview_brief.md) for the
design rationale.

## Verify the build (one command)

```bash
source .venv/bin/activate
python scripts/run_release_gate.py
```

It ends `RELEASE GATE PASS for AgentGuard v4` after running the repository
scaffolding check, every v1–v4 unit test, the v2/v3/v4 evaluation suites, and
the secret scan.

## See it run

```bash
streamlit run app_v4.py
```

Everything runs in free, deterministic mock mode by default — no network call,
no cost, no API key. The rehearsable five-minute walkthrough is in
[`evidence/README.md`](evidence/README.md).

## The invariant it protects

- The MCP discovery server stays **read-only** and exposes **exactly five
  tools** (`health_check`, `list_agent_inventory`, `get_agent_by_name`,
  `list_tool_catalog`, `list_agent_ownership`).
- Remediation is **exactly three allowlisted templates** — never a free-form AI
  patch.
- Only v1's `scanner.py` ever sets a risk score — a proposal *predicts* one.
- GitHub work is dry-run by default, draft-only, on the one allowlisted synthetic
  demo repository, with **no merge command anywhere in the code**.

## How it was built

AgentGuard v4 was implemented in roughly 80 small, individually tested,
sequenced steps. The full index is
[`docs/lab_execution_index.md`](docs/lab_execution_index.md); the build log is
`notes/learning_log.md`.
