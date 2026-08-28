# AgentGuard v3 - Instructions for Claude Code

## Product purpose
AgentGuard is a beginner-friendly application that applies deterministic security rules to sample AI agents' identities, tools, data access, ownership, and human-approval settings. V1 read agent inventory from a local JSON file and scored it with five deterministic rules. V2 (complete and frozen) added a controlled AI explanation layer on top of v1's scanner — the model may explain and cite policy, never change a score. V3 is planned to replace the local-file inventory source with a read-only MCP (Model Context Protocol) client/server boundary: v1's deterministic scanner remains the sole authority for risk, only where the inventory comes from changes.

## Safety boundaries
- Work only inside this project folder.
- Do not access real cloud accounts, browsers, passwords, SSH keys, or personal files.
- Do not request or create API keys.
- Do not implement MCP server or client code, or any other v3 functionality, until a lab explicitly authorizes and scopes it.
- Do not delete files without explicit approval.
- Do not install packages unless the user approves.
- Keep code simple and explain changes in plain English.
- Run `pytest -q` after code changes and report the exact result.
- Run `python -m compileall .` after code changes and report the exact result.

## v1 commands
Activate the environment:
`source .venv/bin/activate`

Run tests:
`pytest -q`

Run the app:
`streamlit run app.py`

## Product naming
- Product family: AgentGuard.
- Current release: AgentGuard v3 - MCP Connected Discovery (in progress).
- Do not rename it back to AgentGuard Mini.

## Required v1 evidence
- Four automated tests must pass.
- The BEFORE scan must show two HIGH-risk agents.
- The AFTER scan must show zero HIGH-risk agents and three NO RISK FOUND agents.
