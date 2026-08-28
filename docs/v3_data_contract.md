# V3 Connected Data Contract

This documents what an enterprise agent registry must provide to
AgentGuard v3 — a **data contract**, decided before any MCP code reads
from it. Only `docs/v3_data_contract.md` and the `connected_environment/`
fixture files are created in this lab; the full synthetic dataset, tool
classifications, ownership records, and the deliberately malicious note
are each a later lab's job (noted below).

## The problem this contract solves

v1 and v2 both read agent data from one trusted local JSON file that
ships with the repo — no contract was needed, because the code and the
data live in the same place. A real enterprise registry is different:
it's typically **several separate systems**, maintained by different
teams, none of which AgentGuard controls or can implicitly trust. Before
writing any code that talks to those systems, this lab defines exactly
what each one must supply — the same discipline `docs/v3_architecture.md`
(Day 1 Lab 7) already applied to *where* untrusted data becomes trusted;
this lab answers *what shape* that data takes.

## The four sources

1. **`connected_environment/agents.json`** — the core agent inventory.
   Must supply exactly v1's six required fields per agent (from
   `scanner.py`): `agent_name`, `owner`, `identity`, `tools`,
   `sensitive_data_access`, `human_approval_required`. Wrapped in an
   **envelope** — `{environment_name, source_system, agents: [...]}` —
   rather than a bare array, so the source system is recorded, not just
   the data. *This lab creates one placeholder agent only; the full
   synthetic dataset is Day 3 Lab 2's job.*
2. **`connected_environment/tool_catalog.json`** — metadata about the
   tools referenced in `agents.json`: what each tool does and what
   access level it represents, beyond just its name. *This lab includes
   one matching entry only; real access classifications are Day 3 Lab
   3's job.*
3. **`connected_environment/ownership.json`** — a **separate** source of
   owner records, distinct from the `owner` field already in
   `agents.json`. Real enterprise registries routinely have ownership
   recorded in more than one system; a later lab (Day 7's adapter)
   reconciles the two. *This lab includes one matching entry only; real
   ownership records are Day 3 Lab 4's job.*
4. **`connected_environment/untrusted_notes.txt`** — free-text content
   from the connected system, included specifically to prove AgentGuard
   treats connected *data* as data, never as instructions, even over an
   otherwise-trusted transport. *This lab contains a benign placeholder
   only; the actual deliberately crafted test payload is Day 3 Lab 5's
   job — writing it now would leave that lab nothing to teach.*

## Required fields and maximum sizes

A **schema** isn't just "what fields exist" — it also bounds *how big*
each piece of data is allowed to be. Without a documented limit, a
connected source (or an attacker controlling one) could send an
extremely long string or a huge array, which is a real **attack
surface**: unbounded input can exhaust memory, blow up logs, or slow
parsing to a crawl. Writing these limits down now, before any adapter
exists, means that code has concrete numbers to enforce from day one.

**`connected_environment/agents.json`**

| Field | Type | Max size |
|---|---|---|
| `environment_name`, `source_system` | string | ≤ 200 characters |
| `agents` | array | ≤ 50 entries |
| `agent_name`, `identity` | string, required | ≤ 200 characters |
| `owner` | string, required (may be empty) | ≤ 200 characters |
| `tools` | array | ≤ 20 entries |
| each tool name | string | ≤ 100 characters |
| `sensitive_data_access`, `human_approval_required` | boolean | — |

**`connected_environment/tool_catalog.json`**

| Field | Type | Max size |
|---|---|---|
| `tools` | array | ≤ 100 entries |
| `name`, `system` | string, required | ≤ 100 characters |
| `access` | string, required | one of `read`, `external_write`, `destructive`, `production_write` |

**`connected_environment/ownership.json`**

| Field | Type | Max size |
|---|---|---|
| `owners` | array | ≤ 50 entries |
| `agent_name`, `owner` | string, required (`owner` may be empty) | ≤ 200 characters |

**`connected_environment/untrusted_notes.txt`**

| Constraint | Limit |
|---|---|
| Total file size | ≤ 10 KB |

This file is free text, not structured JSON — a size cap is the only
practical guard available for it, which matters precisely *because* it's
meant to be read as inert data and never parsed as instructions or
structure of any kind.

## New terms

- **Data contract** — an explicit, written agreement on exactly what
  fields, types, and shape one system provides to another, so the
  receiving side knows what to expect without guessing.
- **Envelope** — a wrapper object around the actual data that carries
  metadata about where it came from (`source_system`), as opposed to a
  bare array with no such context.
- **Source system** — the specific origin system a piece of connected
  data claims to come from, recorded so provenance can be traced later.
- **Untrusted note** — free-text content included specifically to test
  that connected data is never treated as an instruction, regardless of
  transport trust.
- **Schema** — the full contract for a piece of data: not just field
  names and types, but also size and count limits.
- **Attack surface** — the total set of ways a system could be
  manipulated through the input it accepts; narrowing what's allowed
  (bounded sizes, fixed field sets) shrinks it.
- **Bounded input** — data with an explicit, enforced maximum size or
  count, as opposed to accepting an unlimited amount.

## What this lab deliberately does not do yet

- Does not design the full synthetic agent dataset (Day 3 Lab 2).
- Does not classify tool access levels (Day 3 Lab 3).
- Does not populate real ownership records (Day 3 Lab 4).
- Does not write the actual malicious note content (Day 3 Lab 5).
- Does not enforce the field/size limits documented above in any code —
  they're written down, not yet checked by anything. No MCP server or
  adapter reads any of these files yet — they are inert fixtures until a
  later lab builds the server (Day 5) and the adapter that maps them
  back to `scanner.py`'s schema (Day 7).

  *Update — Day 9 security review (Lab 7):* Day 7's adapter enforced
  field *presence and type* but not these *size* limits. They are now
  enforced in `discovery_adapter.py` as `MAX_AGENTS` /
  `MAX_FIELD_CHARS` / `MAX_TOOLS` / `MAX_TOOL_NAME_CHARS`, with matching
  tests in `tests/test_discovery_adapter.py`.

## The one invariant this contract must never break

No matter what shape these three registry sources take, an adapter will
later convert them into the exact `scanner.py` `Agent` schema before
scoring — v1's deterministic scanner remains the sole authority for risk,
regardless of which system the inventory came from.
