"""Pure read-only discovery functions used by MCP tools and automated tests.

Every function here is a plain Python function: no MCP imports, no
transport code, no decorators. That is deliberate - this business logic
must be fully testable with ordinary pytest, without a running MCP
server, without STDIO, and without the Inspector. A later lab (Day 5)
wraps each of these functions in a thin @mcp.tool() decorator inside
mcp_server.py; nothing about that wrapping is allowed to change what
these functions actually do.

All five discovery functions are implemented: health, list_agents,
get_agent, list_tools, get_ownership. Every one is strictly read-only -
none of them writes, creates, or deletes anything. That is not an
oversight: v3 only ever needs to read the connected inventory and hand
it to v1's unchanged scanner. Writing to or remediating the environment
is v4's job, not v3's.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from mcp_security import read_json_with_provenance, safe_child


BASE_DIR = Path(__file__).parent / "connected_environment"

# The fixed allowlist: exactly the three JSON registry sources defined
# in Day 3's data contract. untrusted_notes.txt is deliberately excluded
# - it exists in the same folder, but it was never meant to be served by
# a discovery tool, so it is not authorized here regardless of presence.
ALLOWED_FILES = {"agents.json", "tool_catalog.json", "ownership.json"}


def new_correlation_id() -> str:
    """Generate a fresh, unique ID to tag one logical discovery request.

    Traceability, not security: every discovery function below attaches
    an ID like this to its response, and an internal call - get_agent
    calling list_agents, for example - reuses the same ID rather than
    minting a new one. That lets one request be followed across the
    server, the future adapter, the scanner, and any logs each layer
    writes (Day 9), instead of guessing which log lines belong together
    based on timing alone.
    """
    return str(uuid.uuid4())


def health() -> dict:
    """Report server health and confirm read-only mode.

    The only discovery function that needs no file access and no
    security helper - it can be imported and tested without
    connected_environment/ existing, without mcp_security.py's real
    logic, and without the mcp package installed at all.
    """
    return {
        "correlation_id": new_correlation_id(),
        "status": "ok",
        "mode": "read-only",
        "tool_count": 5,
    }


def list_agents() -> dict:
    """List every synthetic agent from the connected registry.

    Composes every earlier building block in sequence: safe_child (Day 4
    Labs 2-4) validates and resolves the path, read_json_with_provenance
    (Lab 5) reads it and fingerprints the bytes, new_correlation_id
    (Lab 6) tags this specific call for tracing.
    """
    record = read_json_with_provenance(safe_child(BASE_DIR, "agents.json", ALLOWED_FILES))
    agents = record["payload"].get("agents", [])
    return {
        "correlation_id": new_correlation_id(),
        "source_name": record["source_name"],
        "source_sha256": record["source_sha256"],
        "environment_name": record["payload"].get("environment_name", ""),
        "agents": agents,
        "count": len(agents),
    }


def get_agent(agent_name: str) -> dict:
    """Return one named agent from the connected registry.

    Reuses list_agents()'s own correlation_id rather than minting a new
    one - this call and the list_agents() call it makes internally are
    the same logical request, so they should trace as one, not two.
    """
    if not agent_name or len(agent_name) > 200:
        raise ValueError("agent_name must be 1-200 characters")
    inventory = list_agents()
    matches = [agent for agent in inventory["agents"] if agent.get("agent_name") == agent_name]
    if not matches:
        raise KeyError(f"Unknown agent: {agent_name}")
    return {
        "correlation_id": inventory["correlation_id"],
        "source_name": inventory["source_name"],
        "source_sha256": inventory["source_sha256"],
        "agent": matches[0],
    }


def list_tools() -> dict:
    """List the synthetic tool catalog from the connected registry."""
    record = read_json_with_provenance(safe_child(BASE_DIR, "tool_catalog.json", ALLOWED_FILES))
    return {
        "correlation_id": new_correlation_id(),
        "source_name": record["source_name"],
        "source_sha256": record["source_sha256"],
        "tools": record["payload"].get("tools", []),
    }


def get_ownership() -> dict:
    """List ownership records from the connected registry."""
    record = read_json_with_provenance(safe_child(BASE_DIR, "ownership.json", ALLOWED_FILES))
    return {
        "correlation_id": new_correlation_id(),
        "source_name": record["source_name"],
        "source_sha256": record["source_sha256"],
        "owners": record["payload"].get("owners", []),
    }
