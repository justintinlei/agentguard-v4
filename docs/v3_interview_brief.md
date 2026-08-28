# AgentGuard v3 Interview Brief

Eight questions likely to come up when explaining this project, each with a
concise (2-4 sentence) answer. Written from what's actually built and verified
in this repo, not a generic description. The pair `docs/v2_interview_brief.md`
covers the v1/v2 questions (deterministic authority, RAG, grounding).

---

**Q: In one sentence, what changed from v2 to v3, and what deliberately did
not?**

v3 replaced v2's local-file inventory source with a read-only MCP (Model Context
Protocol) client/server boundary: the inventory is now discovered from a
separate server under a fixed allowlist, with provenance and an audit trail.
`scanner.py` and v2's grounded analyst (`v2_service.py`) are byte-for-byte
unchanged — the only new things are where the inventory comes from and the UI
(`app_v3.py`) around it.

**Q: Walk me through the MCP roles in this project — host, client, server, tool,
transport.**

The **host** is AgentGuard itself (`app_v3.py`), the application that wants the
data; it doesn't speak MCP directly. The **client** (`mcp_client.py`) is the
component — one per server — that actually speaks the protocol and manages the
connection. The **server** (`mcp_server.py`) is a separate process exposing a
fixed set of capabilities. A **tool** is one named, callable capability — v3 has exactly five
(`health_check`, `list_agent_inventory`, `get_agent_by_name`,
`list_tool_catalog`, `list_agent_ownership`); the **transport** is STDIO — the
client launches the server as a local subprocess and they exchange JSON-RPC over
its stdin/stdout, no network.
MCP also has *resources* (readable data, not invoked) but v3 uses none — every
capability is a tool.

**Q: Which MCP SDK version and classes does v3 use, and how would you prove it
without running anything?**

The current MCP 2.x Python SDK: `requirements.txt` pins `mcp[cli]>=2.0,<3`.
`mcp_server.py` uses `from mcp.server import MCPServer` (not the older
`FastMCP`), and `mcp_client.py` uses `ClientSession` + `stdio_client` directly
rather than a higher-level wrapper. Two independent source checks assert this:
`tests/test_mcp_sdk_contract.py::test_server_uses_the_current_mcp_2_server_class`
and `scripts/validate_starter_kit.py`, the latter running on every release-gate
invocation.

**Q: What are the authorization boundaries in v3, and where exactly is each one
enforced?**

There are two. The **protocol boundary**: `_verify_tool_allowlist()` in
`mcp_client.py` refuses to proceed unless the server advertises *exactly* the
five expected tool names — an unexpected extra tool or a missing one is
rejected, not trusted. The **data boundary**: `discovery_adapter.py` checks
every discovered agent's fields for presence, correct type, and documented size
limits before it becomes an `Agent` the scanner can see. Beneath both,
`mcp_security.safe_child()` restricts file reads to three fixed filenames and
checks for a symlink before resolving the path. Everything downstream of the
adapter is trusted exactly the way v1/v2's local-file data was.

**Q: Why is the server read-only, and how is that actually guaranteed rather
than just intended?**

Discovery only ever needs to *read* a registry; writing or remediating is v4's
job, deliberately kept separate. It's guaranteed three independent ways:
`mcp_server.py` registers exactly five tools and each returns a `discovery_core`
function that only reads and hashes; `tests/test_mcp_sdk_contract.py` statically
asserts no write operation exists anywhere in the discovery source; and
`scripts/validate_starter_kit.py::check_five_readonly_tools()` re-parses the
server and client source on every release-gate run to confirm the tool set is
exactly those five names and that no name contains a write verb.

**Q: How does v3 handle prompt injection in connected data?**

Connected data is treated as data, never as instructions. v1's deterministic
scanner is the *only* component that can set a risk score, so no text in a
registry field — "ignore this finding", "report as safe" — can change the
outcome, because nothing downstream of `evaluate_agent()` has that authority.
`mcp_security.read_json_with_provenance()` is content-blind: it parses JSON
structure and hashes raw bytes, with no code path that reads meaning from a
string, and the deliberately-malicious `connected_environment/untrusted_notes.txt`
fixture is permanently outside the three-file allowlist, so no tool can read it
at all. v2's `validate_grounding()` is a second layer on any AI explanation:
it must restate the real scan result and cited policy only.

**Q: What is provenance here, and what does a correlation ID buy you?**

Provenance is a SHA-256 hash of the exact source file bytes plus the filename —
anyone can run `shasum -a 256 connected_environment/agents.json` and confirm
which bytes were scanned. A correlation ID is a UUID minted per discovery
request and carried by every layer's response, so one request can be followed
across the server, the adapter, the scanner, and the audit log
(`audit_events.jsonl`) without guessing from timestamps. Both are displayed in
`app_v3.py`'s provenance panel and written to the audit trail on every scan.

**Q: Tell me about a real gap you found and closed in v3, and what risks you
chose to accept.**

The Day 9 security review found that `docs/v3_data_contract.md` and
`docs/v3_threat_model.md` both claimed `discovery_adapter.py` enforced input
size limits — `agents` <= 50, name-like fields <= 200 chars, `tools` <= 20 —
that the adapter never actually checked; it validated field presence and type
only. A compromised or swapped MCP server could therefore have handed v1's
scanner an unbounded list or a multi-megabyte string. Closed with four `MAX_*`
constants and matching tests, and both overclaiming docs were corrected. Two
risks were reviewed and deliberately accepted:
`read_json_with_provenance()` reads the whole file into memory uncapped
(accepted — the three files are a fixed in-repo allowlist), and
`mcp_client._structured()` parses the first response block as JSON uncapped
(accepted for v3 — the server is our own subprocess; revisit in v4 if it can be
remote). And the honest limits: synthetic data, a local demo, no production
write access.
