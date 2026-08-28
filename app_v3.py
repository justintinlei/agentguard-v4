"""AgentGuard v3 - MCP Connected Discovery. Streamlit page (Day 9, Labs 1-8).

Lab 1 drew this page as a map of the discovery journey with the "Discover"
control disabled. Lab 2 wired the control, with two routes to the same
synthetic inventory:

  - "Direct core (debug)" calls discovery_core.list_agents() in this same
    Python process - no server, no STDIO pipe, no subprocess.
  - "MCP client/server" calls mcp_client.call_tool_sync(...), which starts
    mcp_server.py as a child process and speaks real MCP 2.x over STDIO.

Both return the identical dict, so they are directly comparable. That is
the point of the debug path: if "Direct core" scans correctly but "MCP
client/server" fails, the fault is in the transport layer (server
startup, the STDIO pipe, JSON serialization, the tool-allowlist check),
not in the discovery logic, the adapter, or v1's scanner. The debug path
is a known-good control group to bisect a connected-integration failure
against.

Lab 3 turned the discovery's provenance - the SHA-256 hash of the exact
source bytes and the correlation id - into visible, re-checkable evidence
on the page, and expanded the risk results so every deterministic finding
is readable in full.

Lab 4 makes failures safe to display: safe_error_message() picks a
fixed, hand-written sentence by exception *type*. The exception's own
text - which can carry a local file path, a data payload, or a secret -
is never shown on the page; the full exception goes only to the
process's stderr log.

Lab 5 writes one audit line per "Discover and scan" click via
record_discovery_event() -> audit_log.log_discovery_event(): route, tool
name, source file + SHA-256, correlation id, and outcome (success with
counts, or error with the exception's class name only). It records that
a read happened, not what was read.

Lab 6 added `python evals/run_v3_evals.py` to CI; Lab 7's security
review found and closed a size-limit gap in discovery_adapter.py; Lab 8
resolved the remaining doc drift and added an end-to-end page-flow test.
As of the end of Day 9 the v3 discovery UI is feature-complete - journey
map, two discovery paths, provenance + findings display, safe error
handling, and the audit trail - and stable: nothing is deferred within
Day 9.

Boundary unchanged: exactly five read-only MCP tools; the client refuses
any server whose tool set differs from EXPECTED_TOOLS; synthetic data
only; v1's scanner.py stays the sole risk authority and this page only
displays its ScanResults; no AI call anywhere on this page.
"""

from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

# The append-only audit trail v2 already writes to. log_discovery_event()
# (Day 9 Lab 5) adds one line per discovery, next to v2's analysis events.
from audit_log import log_discovery_event

# The MCP-to-AgentGuard adapter (Day 7) - unchanged. It already validates
# every discovered agent and runs v1's real evaluate_agent() on each.
from discovery_adapter import scan_mcp_inventory

# Import the *real* allowlists so the map cannot drift from the system it
# describes. Importing mcp_client does not start a server - that only
# happens when call_tool_sync() actually runs.
from discovery_core import ALLOWED_FILES, list_agents
from mcp_client import (
    EXPECTED_TOOLS,
    MCPMalformedResponseError,
    MCPUnavailableError,
    call_tool_sync,
)


logger = logging.getLogger(__name__)

PAGE_TITLE = "AgentGuard v3 - MCP Connected Discovery"

# One shared audit trail for the whole product - the same file v2's
# analysis events go to (see evals/run_v2_evals.py). It is *.jsonl, which
# .gitignore already excludes, so running the app never dirties git.
AUDIT_LOG_PATH = Path(__file__).resolve().parent / "audit_events.jsonl"

# The two discovery routes. Kept in one tuple so the radio labels and the
# dispatch in discover_inventory() can never fall out of step.
DISCOVERY_PATHS = ("Direct core (debug)", "MCP client/server")

# Same wording v1's app.py uses. Re-declared here rather than imported,
# because importing app.py would run v1's whole Streamlit page.
NOT_FULLY_SECURE_NOTE = (
    'Note: "NO RISK FOUND" only means none of AgentGuard\'s five rules were '
    "triggered. It does not mean the agent is fully secure - it just passed "
    "the checks this tool knows how to run."
)

# The boundary, stated once, in plain words. The automated test checks
# these sentences are still on the page after any future edit.
BOUNDARY_NOTES = (
    "The connected environment is synthetic - every agent, tool, and owner "
    "is made up for training.",
    "Every MCP tool is read-only. There is no create, update, or delete "
    "tool, and there never will be in v3.",
    "File access is limited to a fixed allowlist of three JSON files. Any "
    "other filename is refused even if the file exists.",
    "v1's deterministic scanner.py is the sole authority for risk. v3 only "
    "changes where the inventory comes from, never how it is scored.",
    "AI (v2's grounded analyst) may explain a score and cite policy. It can "
    "never change a score.",
)

# The discovery journey, as ordered steps. Each step names who acts, what
# happens, and how that step relates to the trust boundary. This is plain
# data so the test suite can read it without running Streamlit.
DISCOVERY_JOURNEY = (
    {
        "step": 1,
        "actor": "User (this page)",
        "action": "Choose a discovery path and click 'Discover and scan'. "
                  "Nothing runs until the user acts.",
        "trust": "Start - user-initiated",
    },
    {
        "step": 2,
        "actor": "mcp_client.py",
        "action": "Start the server, initialise the session, verify the "
                  "server exposes exactly the five expected read-only tools, "
                  "then call one tool. (Skipped by the debug path.)",
        "trust": "Client refuses an unexpected server",
    },
    {
        "step": 3,
        "actor": "mcp_server.py -> discovery_core.py -> mcp_security.py",
        "action": "safe_child() resolves one allowlisted file; "
                  "read_json_with_provenance() reads it, hashes the bytes "
                  "(SHA-256), and tags the call with a correlation id.",
        "trust": "UNTRUSTED external data enters here",
    },
    {
        "step": 4,
        "actor": "discovery_adapter.py",
        "action": "Check every required agent field is present, correctly "
                  "typed, and within the documented size limits (Day 9 "
                  "review). Malformed or oversized data is rejected loudly, "
                  "naming the bad agent - it never reaches the scanner.",
        "trust": "Validation boundary",
    },
    {
        "step": 5,
        "actor": "scanner.py (v1, unchanged)",
        "action": "Run evaluate_agent() on each agent - the same five "
                  "deterministic rules v1 and v2 already use. No AI, same "
                  "input always gives the same score.",
        "trust": "Deterministic authority - source of truth",
    },
    {
        "step": 6,
        "actor": "This page",
        "action": "Show the discovered inventory, its provenance (source "
                  "name, SHA-256, correlation id), and the risk table.",
        "trust": "Output - provenance stays attached",
    },
)


def discover_inventory(path_label: str) -> dict:
    """Fetch the raw discovered inventory dict for the chosen path.

    'Direct core (debug)' runs the pure discovery function in this
    process. 'MCP client/server' goes through the real client, which
    starts mcp_server.py and calls exactly one read-only tool,
    'list_agent_inventory'. Both return the same dict shape, so a
    difference in the *result* points at the transport, not the logic -
    that is what makes this page useful for isolating a connected-
    integration failure.
    """
    if path_label == "Direct core (debug)":
        return list_agents()
    if path_label == "MCP client/server":
        return call_tool_sync("list_agent_inventory")
    raise ValueError(f"Unknown discovery path: {path_label!r}")


def safe_error_message(exc: Exception) -> str:
    """Map a discovery failure to a fixed, user-facing sentence.

    The category is chosen by the exception *type* only. str(exc) is
    never used: it can contain a local file path (which leaks the
    machine's username), a raw data payload, deep library internals, or
    - in a real deployment - a token that happened to be in a stack
    frame. The caller shows this string; the real exception is written
    to the process's stderr log instead, where only a developer sees it.

    MCPUnavailableError and MCPMalformedResponseError both subclass
    RuntimeError, so they are checked before the generic RuntimeError
    branch. An unrecognised type gets the most generic (least
    revealing) message - a fail-safe default.
    """
    if isinstance(exc, MCPUnavailableError):
        return (
            "Could not reach the MCP discovery server. It may have failed to "
            "start, crashed, or not responded in time. Check that "
            "`python mcp_server.py` runs cleanly, then try again."
        )
    if isinstance(exc, MCPMalformedResponseError):
        return (
            "The MCP server replied with data this client could not parse. "
            "The server may be running an incompatible version."
        )
    if isinstance(exc, ValueError):
        return (
            "The discovered inventory could not be read, or it failed "
            "validation before scanning (a required agent field was missing "
            "or had the wrong type). Nothing was scored."
        )
    if isinstance(exc, RuntimeError):
        return (
            "The MCP server behaved unexpectedly - for example it exposed a "
            "tool this client does not trust. The discovery was refused."
        )
    return "An unexpected error stopped the discovery. Please try again."


def record_discovery_event(
    route: str,
    tool_name: str,
    inventory: dict | None,
    *,
    report: dict | None = None,
    exc: Exception | None = None,
) -> None:
    """Write one best-effort audit line for a discovery attempt.

    Reads the provenance straight off the inventory dict the discovery
    returned; on an early failure `inventory` is None, so those fields are
    recorded as empty. When `exc` is given the outcome is "error" and only
    the exception's class name is stored - never its text. A broken audit
    log must not break discovery, so any write failure is logged to
    stderr and swallowed.
    """
    provenance = inventory or {}
    fields = {
        "route": route,
        "tool_name": tool_name,
        "source_name": provenance.get("source_name", ""),
        "source_sha256": provenance.get("source_sha256", ""),
        "correlation_id": provenance.get("correlation_id", ""),
    }
    if exc is not None:
        fields["outcome"] = "error"
        fields["error_category"] = type(exc).__name__
    else:
        rows = scan_rows(report) if report else []
        fields["outcome"] = "success"
        fields["agent_count"] = len(rows)
        fields["high_risk_count"] = sum(1 for row in rows if row["Risk level"] == "HIGH")

    try:
        log_discovery_event(AUDIT_LOG_PATH, **fields)
    except Exception:
        logger.exception("Could not write the discovery audit event")


def scan_rows(report: dict) -> list[dict]:
    """Flatten scan_mcp_inventory()'s ScanResult list into table rows.

    report['results'] is a list of v1 scanner.ScanResult objects - this
    only reads their fields for display, it never recomputes a score.
    """
    return [
        {
            "Agent": result.agent.agent_name,
            "Risk level": result.risk_level,
            "Score": result.score,
            "Findings": len(result.findings),
        }
        for result in report["results"]
    ]


def provenance_rows(report: dict) -> list[dict]:
    """Turn report['provenance'] into labelled table rows.

    scan_mcp_inventory() guarantees all three fields exist (the adapter's
    extract_provenance() raises if any is missing), so this can read them
    directly. The SHA-256 value is shown in full, not shortened - the
    point is that a reader can re-hash the source file and compare every
    character.
    """
    provenance = report["provenance"]
    return [
        {"Field": "Source file", "Value": provenance["source_name"]},
        {"Field": "SHA-256 of source bytes", "Value": provenance["source_sha256"]},
        {"Field": "Correlation ID", "Value": provenance["correlation_id"]},
    ]


def provenance_matches_inventory(report: dict, inventory: dict) -> bool:
    """True iff the hash and correlation id on the risk report are the
    same ones carried by the raw discovered inventory.

    The adapter copies these fields straight from the inventory, so a
    mismatch would mean the report and the inventory on screen came from
    two different discoveries - visible proof, either way, that the two
    panels belong together.
    """
    provenance = report["provenance"]
    return (
        provenance["source_sha256"] == inventory.get("source_sha256")
        and provenance["correlation_id"] == inventory.get("correlation_id")
    )


def finding_rows(report: dict) -> list[dict]:
    """Flatten every finding from every agent into one list of rows,
    each tagged with the agent it belongs to."""
    rows = []
    for result in report["results"]:
        for finding in result.findings:
            rows.append(
                {
                    "Agent": result.agent.agent_name,
                    "Rule": finding.rule_id,
                    "Severity": finding.severity,
                    "Points": finding.points,
                    "Title": finding.title,
                }
            )
    return rows


def render() -> None:
    """Draw the whole page. Called from the __main__ guard below."""
    st.set_page_config(page_title=PAGE_TITLE, page_icon="🔌", layout="wide")
    st.title("🔌 " + PAGE_TITLE)
    st.write(
        "v3 discovers a synthetic agent registry through a read-only MCP "
        "boundary, keeps the source's fingerprint (provenance), and scans "
        "the result with v1's unchanged deterministic scanner. The debug "
        "path runs the same discovery logic in-process, with no protocol, "
        "so a connected failure can be isolated to the transport."
    )

    st.warning(
        "Safety boundary - read this before running any discovery:",
        icon="⚠️",
    )
    for note in BOUNDARY_NOTES:
        st.markdown(f"- {note}")

    st.header("The discovery journey")
    st.write(
        "Read top to bottom. The 'Trust' column marks where untrusted data "
        "enters, where it is validated, and where risk is actually decided."
    )
    st.table(
        [
            {
                "Step": item["step"],
                "Who acts": item["actor"],
                "What happens": item["action"],
                "Trust": item["trust"],
            }
            for item in DISCOVERY_JOURNEY
        ]
    )

    st.header("Fixed allowlists this journey depends on")
    col_files, col_tools = st.columns(2)
    with col_files:
        st.subheader("Allowed files (step 3)")
        st.table([{"Filename": name} for name in sorted(ALLOWED_FILES)])
    with col_tools:
        st.subheader("Expected MCP tools (step 2)")
        st.table([{"Tool": name} for name in sorted(EXPECTED_TOOLS)])

    st.header("Start a discovery")
    path_label = st.radio("Discovery path", DISCOVERY_PATHS, horizontal=True)
    st.caption(
        "Direct core runs discovery_core.list_agents() in this process. "
        "MCP client/server starts mcp_server.py and calls one read-only "
        "tool. Same result either way - a mismatch points at the transport."
    )

    if st.button("Discover and scan", type="primary"):
        tool_name = (
            "list_agent_inventory"
            if path_label == "MCP client/server"
            else "(direct core - no tool call)"
        )
        inventory = None
        try:
            inventory = discover_inventory(path_label)
            report = scan_mcp_inventory(inventory)
            st.session_state["v3_path"] = path_label
            st.session_state["v3_inventory"] = inventory
            st.session_state["v3_report"] = report
            record_discovery_event(path_label, tool_name, inventory, report=report)
        except Exception as exc:
            # Full detail (with traceback) to stderr only - never the page.
            logger.exception("Discovery failed")
            record_discovery_event(path_label, tool_name, inventory, exc=exc)
            st.error(safe_error_message(exc))
            st.caption(f"Error category: {type(exc).__name__}")

    if "v3_report" in st.session_state:
        inventory = st.session_state["v3_inventory"]
        report = st.session_state["v3_report"]
        rows = scan_rows(report)
        high_count = sum(1 for row in rows if row["Risk level"] == "HIGH")

        st.subheader("Provenance - where this inventory came from")
        st.write(f"Path used: **{st.session_state['v3_path']}**")
        st.table(provenance_rows(report))
        st.caption(
            "Re-check the hash yourself: "
            "`shasum -a 256 connected_environment/agents.json` must print the "
            "same 64 characters. A different value means the source file "
            "changed since this discovery."
        )
        if provenance_matches_inventory(report, inventory):
            st.success(
                "The hash and correlation ID on the risk report match the raw "
                "inventory - both panels are from this one discovery."
            )
        else:
            st.warning(
                "The risk report's provenance does not match the raw "
                "inventory shown below - they may be from different discoveries."
            )

        st.subheader("Risk findings (deterministic - v1 scanner)")
        col_agents, col_high = st.columns(2)
        col_agents.metric("Agents scanned", len(rows))
        col_high.metric("HIGH risk", high_count)
        st.table(rows)

        for result in report["results"]:
            header = (
                f"{result.agent.agent_name} - {result.risk_level} "
                f"({result.score} pts)"
            )
            with st.expander(header):
                if not result.findings:
                    st.write("No findings - none of the five rules triggered.")
                for finding in result.findings:
                    st.markdown(
                        f"**{finding.rule_id} - {finding.title}**  ·  "
                        f"{finding.severity}  ·  {finding.points} pts"
                    )
                    st.write(finding.explanation)
                    st.write(f"**Recommendation:** {finding.recommendation}")
        st.caption(NOT_FULLY_SECURE_NOTE)

        st.subheader("Raw discovered inventory (debug view)")
        st.json(inventory)

        st.caption(
            "A `discovery_complete` audit event (route, tool, source hash, "
            "correlation ID, outcome) was appended to `audit_events.jsonl`."
        )


# `streamlit run app_v3.py` executes this file as __main__, so the page
# draws. A plain `import app_v3` (the tests) skips render() and just reads
# the module-level data and helpers - no Streamlit warnings, no side effects.
if __name__ == "__main__":
    render()
