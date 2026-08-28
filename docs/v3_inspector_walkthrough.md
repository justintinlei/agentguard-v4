# V3 MCP Inspector Walkthrough

MCP Inspector is the official interactive devtool for testing an MCP
server by hand, before any automated client exists. It starts your
server as a subprocess, performs the MCP handshake, and gives you a
browser page to explore what the server can do. It runs via `npx`
(downloaded and run once, not installed) so it never appears in
`requirements.txt` — it is a devtool, not a project dependency.

This file grows one section per Day 6 lab. This section covers only
Lab 1: launching Inspector and seeing the tool list. Later sections
will cover calling `health_check` (Lab 2), calling every discovery tool
(Lab 3), trying invalid inputs (Lab 4), and saving final evidence
(Lab 8).

## Day 6, Lab 1 — Launch Inspector against the local server

**Prerequisite check** (already confirmed working in Day 2):

```bash
cd ~/Developer/AgentGuard/01-Working/agentguard-v3
source .venv/bin/activate
npx @modelcontextprotocol/inspector --help
```

This should print Inspector's usage text (`--web`, `--cli`, `--tui`,
`-h`) with no error. `--web` is the default mode.

**Launch Inspector against `mcp_server.py`:**

```bash
npx @modelcontextprotocol/inspector python mcp_server.py
```

- Inspector starts `mcp_server.py` as a child process talking over
  STDIO — the same transport a real client uses — and prints a local
  URL (with a one-time session token) to open in a browser.
- Open that URL, click **Connect**.
- Open the **Tools** panel. You should see exactly five tools, no more,
  no less:
  - `health_check`
  - `list_agent_inventory`
  - `get_agent_by_name`
  - `list_tool_catalog`
  - `list_agent_ownership`
- Do not call any tool yet — clicking into each tool's schema to
  confirm it matches its function signature is enough for this lab.
  Calling them is Labs 2–4.

## Security boundary

Inspector is only another MCP client. It reaches the server through
the exact same STDIO transport and the exact same five-tool allowlist
any client would see — it cannot bypass `mcp_security.py`'s path-safety
or file-allowlist checks (Day 4), because those checks live inside the
tool functions themselves, not in the transport. Inspector runs
entirely on localhost, performs no writes, and is not part of
AgentGuard's runtime — it is a manual session the student drives by
hand, closed when the terminal is closed.

## Day 6, Lab 2 — Call `health_check` in Inspector

With Inspector connected (Lab 1) and the Tools panel open:

- Select **`health_check`**.
- It takes no arguments — click **Call Tool** directly.
- Read the response. It should be exactly:
  ```json
  {
    "correlation_id": "<a fresh UUID, different every call>",
    "status": "ok",
    "mode": "read-only",
    "tool_count": 5
  }
  ```

**What this proves.** `health_check` takes no input and touches no
file — it is the simplest possible tool. A working response here means
the full round trip already succeeded: the client-server `initialize`
handshake completed, the `tools/call` message reached the server,
`discovery_core.health()` ran, and its JSON came back unchanged. If the
transport were broken, this is the point where it would fail — no
tool, however simple, can respond otherwise.

**What this does *not* prove yet.** `mode: "read-only"` here is a fixed
value the server declares about itself (`discovery_core.py:50-63`), not
something Inspector verified against real behavior — no
connected-environment file was read, so none of Day 4's allowlist or
path-safety code ran. Confirming those checks fire on real file reads
starts in Lab 3, when every discovery tool is called in turn.

## Day 6, Lab 3 — Call every discovery tool in Inspector

`health_check` (Lab 2) touched no file. These four calls do — each one
runs the real Day 4 chain (`safe_child()`'s allowlist and path-safety
checks, then `read_json_with_provenance()`'s read-and-hash) against a
real connected-environment file, live, for the first time outside
`pytest`. Call each one and compare against these known-good values,
read directly from the files themselves:

**`list_agent_inventory`** — no arguments.
- `count: 3`; `agents` contains exactly "Customer Support Agent",
  "Research Agent", "Deployment Agent".
- `source_name: "agents.json"`; `source_sha256` is a 64-character hex
  string.

**`get_agent_by_name`** — argument `{"agent_name": "Research Agent"}`.
- `agent.owner: "Product Research"`, matching that agent's full record.
- Try an unknown name too, e.g. `"Nonexistent Agent"` — expect an
  error, not a crash (full error-shape testing is Lab 4; here just
  notice it fails cleanly).

**`list_tool_catalog`** — no arguments.
- `tools` has exactly 8 entries; `source_name: "tool_catalog.json"`.

**`list_agent_ownership`** — no arguments.
- `owners` has exactly 3 entries; `source_name: "ownership.json"`.

**Provenance, independently.** `source_sha256` is not a label to trust
blindly — it's a SHA-256 fingerprint of the exact file bytes read. You
can verify it yourself, outside Inspector entirely:
```bash
shasum -a 256 connected_environment/agents.json
```
The hex digest printed should match the `source_sha256` Inspector
showed you for `list_agent_inventory`.

**Separately auditable, not merged.** Call `list_tool_catalog` and
`list_agent_ownership` back to back. Both describe agent-adjacent
metadata, but their `source_name`, `source_sha256`, and
`correlation_id` are all different — proof the two registries stay
independently traceable rather than being silently combined into one
untraceable blob.

## Day 6, Lab 4 — Try invalid tool inputs in Inspector

Labs 2–3 proved the happy path. This lab deliberately breaks things and
checks the failure itself stays safe. Try each of these five inputs on
`get_agent_by_name` and read the exact error text Inspector shows.
Verified directly (a real separate client process, over the same
STDIO transport Inspector uses — not just assumed):

| Input | Rejected by | Client sees |
|---|---|---|
| `{"agent_name": ""}` | `discovery_core.get_agent()`'s own check | `Error executing tool get_agent_by_name` |
| `{"agent_name": "Nonexistent Agent"}` | same | `Error executing tool get_agent_by_name` |
| `{"agent_name": "x"` × 300 chars `}` | same | `Error executing tool get_agent_by_name` |
| `{"agent_name": 123}` | the SDK's schema check (wrong type) | `Error executing tool get_agent_by_name: 1 validation error for get_agent_by_nameArguments\nagent_name\n  Input should be a valid string [type=string_type, input_value=123, input_type=int]\n    For further information visit https://errors.pydantic.dev/2.13/v/string_type` |
| `{}` (missing field) | the SDK's schema check | same shape, `Field required [type=missing, ...]` |

**Two different rejection layers.** The first three all pass schema
validation (a string is a string) and reach `discovery_core.get_agent()`
itself, whose own domain rules — 1–200 characters, must be a real agent
— reject them. The last two never reach your code at all: the MCP
SDK's own pydantic-based schema check rejects them first, because
`get_agent_by_name`'s declared input type is a string.

**Why the domain-error text looks *more* generic than the code that
raised it.** `discovery_core.get_agent()` already writes safe,
human-readable messages — `"agent_name must be 1-200 characters"`,
`"Unknown agent: Nonexistent Agent"`. But the SDK wraps any exception a
tool function raises in `UnexpectedToolError` before it ever reaches
the client, and the *wrapper's* message — `"Error executing tool
get_agent_by_name"` — is what actually gets sent, not the original
text. The original message only exists as the exception's `__cause__`,
visible to Python code (like `pytest`) holding the exception object
directly, never to a remote client. That's belt-and-suspenders safety:
even an already-safe message doesn't reach the wire unmodified.

**Where the full detail actually goes.** Run the server directly (not
just through Inspector) and you'll see the complete Python traceback —
file paths, line numbers, the works — printed to the server's own
**stderr**. That's for the developer's own debugging (Day 2's
STDIO/logging rule: stdout is reserved for protocol messages, stderr
for logs) and never crosses into what `content` sends to the client.
The schema-validation messages are more detailed than the domain ones
(they name the pydantic library and link its docs) but still contain
no file paths, no stack trace, and no server internals beyond "this
project uses pydantic for input validation" — safe, if less polished.

**What this doesn't formalize yet.** Turning these five cases into
permanent pytest assertions belongs to **Day 8, Lab 4** ("Test Missing
Fields Wrong Types And Oversized Names"). This lab is the manual,
click-through version.

## Labs 5–8: from Inspector to an independent client

Labs 1–4 above used Inspector as the client. Starting with Lab 5,
AgentGuard gets its own Python client, `mcp_client.py`, so the project
no longer depends on Inspector to talk to its own server. `mcp_client.py`
performs the same four steps by hand that Inspector performed for you -
start the server, initialize a session, list tools, call one - and
`scripts/run_mcp_live_smoke.py` proves it with two real tool calls end
to end. Run it with:

```bash
python scripts/run_mcp_live_smoke.py
```

Inspector remains useful for ad hoc, interactive exploration; the
client is what any real integration (or Day 9's Streamlit app) will
actually use.

## Lab 8: where the evidence lives

This file documents *how* to reproduce every Day 6 step by hand. The
reproducible, screenshot-by-screenshot index of *what to save* -
Inspector's tool list and responses, the live client's smoke output,
and the full test suite - is `evidence/README.md`'s "Day 6 Evidence"
section, added in Lab 8.
