"""Independent MCP 2.x client for AgentGuard v3.

Day 6, Lab 5 built the four steps any MCP client performs: start the
server, initialize a session, list its tools, and call one. Lab 6 added
the missing check: refuse to proceed unless the server's declared tool
set is exactly what this client expects - no more, no fewer. Lab 7
(this one) turns two remaining failure classes into controlled,
named errors instead of raw library internals: the server being
unreachable (missing, crashed, or hung) and a tool response that isn't
parseable JSON. Every tool this client can reach is already read-only
(mcp_server.py, Day 5) - this file adds no new capability, only a way
to reach it, refuse an untrusted server, and fail predictably.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

BASE_DIR = Path(__file__).parent

# A server that never responds is just as unavailable as one that never
# starts - without this, a hung server would make the client wait forever.
CONNECT_TIMEOUT_SECONDS = 15.0

EXPECTED_TOOLS = {
    "health_check",
    "list_agent_inventory",
    "get_agent_by_name",
    "list_tool_catalog",
    "list_agent_ownership",
}


class MCPUnavailableError(RuntimeError):
    """The server process could not be started, reached, or responded in time."""


class MCPMalformedResponseError(RuntimeError):
    """A tool's response could not be parsed as the JSON this client expects."""


def _verify_tool_allowlist(available: set[str]) -> None:
    """Refuse to proceed unless the server's tool set is exactly what
    this client expects. An unexpected extra tool is a capability the
    client never agreed to trust; a missing expected tool is a broken
    or downgraded server - both are refused, not silently allowed.
    """
    if available != EXPECTED_TOOLS:
        raise RuntimeError(
            "MCP server tool set differs from the client's allowlist: "
            f"expected={sorted(EXPECTED_TOOLS)} actual={sorted(available)}"
        )


def _structured(result: Any) -> dict:
    """Parse a tool result's JSON text into a plain dict.

    Every discovery tool in mcp_server.py returns a Python dict, which
    the SDK serializes as exactly one text content block - so parsing
    that one block's text as JSON always recovers the original dict,
    as long as the response is well-formed.
    """
    for block in result.content:
        text = getattr(block, "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError as exc:
                raise MCPMalformedResponseError(f"Tool response was not valid JSON: {exc}") from exc
    raise MCPMalformedResponseError(f"MCP tool returned no readable content: {result}")


async def call_tool(tool_name: str, arguments: dict | None = None) -> dict:
    """Start the server, initialize a session, list its tools, and call one.

    Connection failures - the server process can't start, the pipe
    closes before the handshake finishes, or the server never responds
    at all - are collapsed into one clear MCPUnavailableError. The
    SDK's own transport runs its background work in nested TaskGroups,
    so any exception raised inside the `async with` blocks below,
    including this client's own, comes back wrapped in a nested
    ExceptionGroup; that's why interpreting the result (the allowlist
    check, the is_error check, JSON parsing) happens below, after both
    blocks have already exited cleanly - only genuine transport
    failures are meant to reach the except clause here.
    """
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(BASE_DIR / "mcp_server.py")],
        cwd=str(BASE_DIR),
    )

    async def _connect_and_call() -> tuple[set[str], Any]:
        async with stdio_client(params) as (read, write):  # start the server
            async with ClientSession(read, write) as session:
                await session.initialize()  # initialize a session
                listed = await session.list_tools()  # list its tools
                available_tools = {tool.name for tool in listed.tools}
                result = await session.call_tool(tool_name, arguments or {})  # call one
                return available_tools, result

    try:
        available_tools, result = await asyncio.wait_for(_connect_and_call(), timeout=CONNECT_TIMEOUT_SECONDS)
    except (OSError, ExceptionGroup, TimeoutError) as exc:
        raise MCPUnavailableError(f"Could not reach the MCP server: {exc}") from exc

    _verify_tool_allowlist(available_tools)
    if result.is_error:
        raise RuntimeError(f"MCP tool call failed: {tool_name}")
    return _structured(result)


def call_tool_sync(tool_name: str, arguments: dict | None = None) -> dict:
    """Synchronous wrapper for callers outside an async context."""
    return asyncio.run(call_tool(tool_name, arguments))
