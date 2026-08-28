# AGP-002 - Least Privilege for Agent Tools

An agent should only be given the specific tools it needs for its
approved task — nothing broader. Wildcard access or admin-level tools are
not allowed unless there's a documented, approved reason.

## Required controls

- List the exact tools an agent may use; avoid open-ended or wildcard
  permissions.
- Keep tools that only read data separate from tools that can change or
  delete data.
- Re-review an agent's tool list before launch and any time its tools
  change.
