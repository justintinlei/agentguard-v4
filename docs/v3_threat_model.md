# V3 Threat Model — Attack Checklist

Security design starts with naming abuse cases explicitly, before
proving each one is blocked. This checklist is the map Day 8's labs
each executed one entry of. As of v3's release candidate, all seven
categories are proven by permanent tests, assembled into one command
(`python evals/run_v3_evals.py`). This document inventories what's real
and assigns each case its formal test; it does not propose new
protection. Two categories were strengthened after Day 8 — the Day 9
security review (§3) and Day 10 Lab 2 (§5) — and two risks were
reviewed and deliberately accepted (see the end).

## 1. Path traversal / absolute paths (Lab 2)

**Attack:** a requested filename contains `../` segments or an
absolute path, trying to read a file outside `connected_environment/`.

**Existing defense:** `mcp_security.safe_child()` resolves the
candidate path and checks `candidate.parent != base` — the resolved
path must land directly inside `base_dir`, not merely somewhere
beneath it. Already partly proven by
`tests/test_mcp_security.py::test_safe_child_blocks_traversal_even_if_allowlist_is_misconfigured`.

**Lab 2 formalizes:** dedicated traversal-string and absolute-path
test cases against `safe_child()`.

## 2. Unapproved filenames / symlink escape (Lab 3)

**Attack:** (a) requesting a real filename never added to the
allowlist; (b) an allowlisted name that's secretly a symlink pointing
elsewhere on disk.

**Existing defense:** `safe_child()` checks the raw candidate for
`is_symlink()` *before* calling `resolve()` — a resolved path's parent
can look perfectly safe even when reached through a redirect, so the
symlink check has to happen on the raw path first. Already proven by
`test_safe_child_rejects_untrusted_notes_even_though_it_exists` (case
a) and `test_safe_child_blocks_a_symlink_even_when_its_target_stays_inside_base_dir`
(case b).

**Lab 3 formalizes:** additional unapproved-filename and symlink-escape
cases, including a directory masquerading as a file (already covered
by `test_safe_child_blocks_a_directory_masquerading_as_a_file`).

## 3. Missing fields, wrong types, oversized names (Lab 4)

**Attack:** a connected registry record is missing a required field,
has a field of the wrong type (e.g. a truthy string standing in for a
boolean), or supplies an oversized value.

**Existing defense:** Day 7's `discovery_adapter.py` validates every
required field's presence and type before constructing an `Agent`
(`mcp_agent_to_agent()`). Day 6 Lab 4 already tested this category
manually, through Inspector, at the MCP transport layer, and explicitly
deferred permanent pytest coverage to this lab.

**Corrected by the Day 9 security review (Lab 7):** the field/count
*size* limits from `docs/v3_data_contract.md` (`agents` ≤ 50,
name-like fields ≤ 200 chars, `tools` ≤ 20, tool name ≤ 100 chars) were
written down but never enforced. `discovery_core.get_agent()` bounds
its `agent_name` *argument* (the lookup query), not the stored record.
`discovery_adapter.py` now enforces all of these limits
(`MAX_AGENTS` / `MAX_FIELD_CHARS` / `MAX_TOOLS` / `MAX_TOOL_NAME_CHARS`)
before any value reaches `scanner.evaluate_agent()`, covered by
`tests/test_discovery_adapter.py`.

**Lab 4 formalizes:** the same category as dedicated, permanent tests
at the MCP/server layer (`mcp_security.py` / `tests/test_mcp_security.py`),
complementing Day 7's adapter-layer tests.

## 4. Prompt injection as untrusted data (Lab 5)

**Attack:** connected data — a note, a comment field, any text a
registry entry carries — contains instructions written to manipulate
an AI explanation layer: "ignore the scanner's score," "report this as
safe," "omit this finding."

**Existing defense:** v1's deterministic scanner is the *only*
component ever allowed to set a risk score — no text anywhere can
change it, because nothing downstream of `evaluate_agent()` has the
authority to override its output. v2's `validate_grounding()` further
checks that any AI-generated explanation only ever restates the real
scan result and retrieved policy evidence (both proven in Day 7). The
test fixture already exists: `connected_environment/untrusted_notes.txt`
(Day 3) is a self-labeled synthetic prompt-injection payload, and
`tests/test_untrusted_content.py` (Lab 1) confirms that fixture is
honestly labeled. The fixture is also already permanently unreachable
via `safe_child()`'s allowlist (proven Day 4, Lab 1, Lab 3) — it is
never among the three files any tool can read at all.

**Lab 5 formalizes:** since Day 7's adapter and v2 pipeline aren't in
this lab's file scope (already proven independently, above), Lab 5
verifies the one function in scope that *does* turn connected bytes
into structured data — `read_json_with_provenance()` — is content-blind:
it parses JSON structure and hashes raw bytes, with no code path that
reads meaning out of a string. A field embedding the fixture's real
injected-instruction text comes back byte-identical, as inert data,
proving there is no interpretation step here to hijack in the first
place.

## 5. Unexpected server tool name (Lab 6)

**Attack:** a connected MCP server — misconfigured, compromised, or
simply a different version than expected — advertises a tool the
client never agreed to trust.

**Existing defense:** Day 6 Lab 6's `EXPECTED_TOOLS` allowlist and
`_verify_tool_allowlist()` in `mcp_client.py` refuse to proceed unless
the server's declared tool set is *exactly* the five expected tools —
already proven by `tests/test_mcp_client.py`'s three allowlist tests
and, end to end against a real subprocess server, by Day 7 Lab 8.

**Lab 6 formalizes:** `mcp_client.py`/`tests/test_mcp_client.py` aren't
in this lab's file scope, and the real mechanism above is already
fully tested — Lab 6 instead verifies the same anti-expansion
principle at the boundary it *can* touch: `safe_child()`'s
`allowed_names` parameter is a capability allowlist too, just for
files instead of tools. Confirms `safe_child()` never grants access
beyond exactly what's explicitly listed — no wildcard interpretation
(mirroring v1's own AG-001 rule, which already treats `"*"` as the
single riskiest tool-list pattern) and no implicit "same folder"
capability for an unlisted-but-real file.

**Strengthened by Day 10 Lab 2:**
`scripts/validate_starter_kit.py::check_five_readonly_tools()` adds a
source-only re-check — it parses the `@mcp.tool()` decorators from
`mcp_server.py` and the `EXPECTED_TOOLS` set from `mcp_client.py`,
fails the release gate unless both are exactly the five expected
names, and rejects any tool name containing a write verb. This runs
every time `python scripts/run_release_gate.py` runs, so a sixth tool
or a write tool cannot be merged without failing the gate.

## 6. Byte-for-byte file integrity (Lab 7)

**Attack:** any part of the discovery pipeline — the server, the
adapter, a test — accidentally modifies a connected-environment file
while "just reading" it.

**Existing defense:** zero write operations exist anywhere in
`mcp_security.py`, `discovery_core.py`, or `mcp_server.py` — already
statically verified in Day 5, Lab 7
(`tests/test_mcp_sdk_contract.py::test_no_write_operation_exists_anywhere_in_the_discovery_source`).
`read_json_with_provenance()`'s SHA-256 hash gives an independently
re-checkable fingerprint of the exact bytes read.

**Lab 7 formalizes:** hashing every connected-environment file before
and after a full discovery run and asserting the hashes are identical.

## 7. The complete security evaluation suite (Lab 8)

**Goal:** assemble every test above into one release-gate script,
`evals/run_v3_evals.py`, mirroring `evals/run_v2_evals.py`'s pattern —
regression first, then the security-specific matrix — so the whole
checklist can be proven with one command.

**Implemented:** `python evals/run_v3_evals.py` — runs the full
`pytest -q` regression first, then reruns each category above by its
exact, verified test names, printing one `[PASS]` line per category
and a final `V3 SECURITY EVAL SUITE PASS` banner.

**Wired into the release gate (Day 10):** `scripts/run_release_gate.py`
now runs `run_v3_evals.py` (Lab 1) and
`validate_starter_kit.py`'s five-read-only-tools source check (Lab 2),
so the whole checklist is re-proven every time
`python scripts/run_release_gate.py` is run — it ends
`RELEASE GATE PASS for AgentGuard v3`.

## Accepted residual risks (carried to v4)

Two risks were identified in the Day 9 security review, understood, and
deliberately **accepted** rather than fixed. They are decisions, not
oversights:

1. **Unbounded file read.** `mcp_security.read_json_with_provenance()`
   reads the whole source file into memory before hashing or parsing,
   with no size cap. Accepted because the three source files are a
   fixed, in-repo allowlist — an attacker able to plant a
   multi-gigabyte `agents.json` already has write access to the
   repository, which is a larger compromise than this guard could
   matter for.
2. **Unbounded response-block parse.** `mcp_client._structured()`
   parses the first text block of a tool response as JSON with no size
   cap. Accepted for v3 because the server is our own local subprocess,
   not a network peer. Revisit in v4 if the discovery server can ever
   be remote.
