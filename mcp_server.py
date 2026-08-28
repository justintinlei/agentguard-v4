"""Read-only MCP 2.x server for AgentGuard v3 discovery.

This lab only creates the server instance itself - no tools are
registered yet. Day 5 Labs 2-5 each add one of the five discovery tools;
Lab 6 configures logging. STDIO reserves stdout for protocol messages
(Day 2 Lab 7), so nothing in this file should ever print to stdout.
"""

from __future__ import annotations

import logging

from mcp.server import MCPServer

from discovery_core import get_agent, get_ownership, health, list_agents, list_tools

# STDIO reserves stdout for protocol messages (Day 2 Lab 7). A handler
# created with no explicit stream defaults to stderr, so this call is
# already safe without needing to name a stream at all.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = MCPServer(
    "agentguard-discovery",
    instructions=(
        "Read-only access to a synthetic AI-agent registry. "
        "The server exposes exactly five allowlisted discovery tools."
    ),
)


@mcp.tool()
def health_check() -> dict:
    """Return server health and confirm that the server is read-only."""
    return health()


@mcp.tool()
def list_agent_inventory() -> dict:
    """List synthetic agents from the allowlisted connected registry."""
    return list_agents()


@mcp.tool()
def get_agent_by_name(agent_name: str) -> dict:
    """Return one named synthetic agent after validating the name."""
    return get_agent(agent_name)


@mcp.tool()
def list_tool_catalog() -> dict:
    """List the synthetic tools known to the connected registry."""
    return list_tools()


@mcp.tool()
def list_agent_ownership() -> dict:
    """List ownership records from the connected registry."""
    return get_ownership()


if __name__ == "__main__":
    mcp.run(transport="stdio")
