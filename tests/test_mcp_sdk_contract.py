"""Tests confirming mcp_server.py uses the current MCP 2.x API, and
demonstrating how the SDK's @tool() decorator actually turns a plain
Python function into a protocol-level tool.
"""

import asyncio
import json
import logging
import re
import subprocess
import sys
from pathlib import Path

import pytest

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import UnexpectedToolError

ROOT = Path(__file__).resolve().parent.parent


def test_server_uses_the_current_mcp_2_server_class():
    """Static check: mcp_server.py imports the current API (MCPServer),
    not the deprecated FastMCP class from an earlier MCP release."""
    source = (ROOT / "mcp_server.py").read_text(encoding="utf-8")
    assert "from mcp.server import MCPServer" in source
    assert "FastMCP" not in source


def test_requirements_pin_the_mcp_2_release_line():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "mcp[cli]>=2.0,<3" in requirements


def test_mcp_server_exposes_all_five_discovery_tools():
    """Confirms the server now matches its own instructions text and
    docs/v3_architecture.md's commitment: exactly five allowlisted
    discovery tools, no more, no less."""
    from mcp_server import mcp

    tools = asyncio.run(mcp.list_tools())
    assert [tool.name for tool in tools] == [
        "health_check",
        "list_agent_inventory",
        "get_agent_by_name",
        "list_tool_catalog",
        "list_agent_ownership",
    ]


def test_calling_health_check_through_the_server_returns_real_health_data():
    """The concrete proof of this lab's learning goal: call the tool
    through the server's own protocol-level call_tool() - the same path
    a real client uses - not health() directly, and confirm the result
    carries discovery_core's real data, correctly serialized."""
    from mcp_server import mcp

    result = asyncio.run(mcp.call_tool("health_check", {}))

    assert result.is_error is False
    payload = json.loads(result.content[0].text)
    assert payload["status"] == "ok"
    assert payload["mode"] == "read-only"
    assert payload["tool_count"] == 5


def test_calling_list_agent_inventory_through_the_server_returns_all_three_agents():
    """The concrete proof of this lab's learning goal: call the tool
    through the server's real dispatch path and confirm the full Day 4
    chain (allowlist, path safety, provenance, correlation) actually ran
    and produced the genuine 3-agent inventory - not a mock, not a
    partial result."""
    from mcp_server import mcp

    result = asyncio.run(mcp.call_tool("list_agent_inventory", {}))

    assert result.is_error is False
    payload = json.loads(result.content[0].text)
    assert payload["count"] == 3
    assert {agent["agent_name"] for agent in payload["agents"]} == {
        "Customer Support Agent",
        "Research Agent",
        "Deployment Agent",
    }
    assert payload["source_name"] == "agents.json"
    assert len(payload["source_sha256"]) == 64
    assert payload["correlation_id"]


def test_calling_get_agent_by_name_through_the_server_returns_the_matching_agent():
    from mcp_server import mcp

    result = asyncio.run(mcp.call_tool("get_agent_by_name", {"agent_name": "Research Agent"}))

    assert result.is_error is False
    payload = json.loads(result.content[0].text)
    assert payload["agent"]["agent_name"] == "Research Agent"
    assert payload["agent"]["owner"] == "Product Research"


def test_calling_get_agent_by_name_with_an_empty_name_is_rejected():
    """The concrete proof of this lab's learning goal: discovery_core's
    own input validation (checked before any file access) rejects an
    empty name, and that rejection survives the real dispatch path -
    wrapped as UnexpectedToolError, with the original ValueError
    preserved as the cause. Verified against the SDK's actual behavior,
    not assumed."""
    from mcp_server import mcp

    with pytest.raises(UnexpectedToolError) as exc_info:
        asyncio.run(mcp.call_tool("get_agent_by_name", {"agent_name": ""}))
    assert isinstance(exc_info.value.__cause__, ValueError)


def test_calling_get_agent_by_name_with_an_unknown_name_is_rejected():
    """Distinguishes the two rejection reasons: an unknown (but
    well-formed) name fails differently than an empty one - KeyError,
    not ValueError - and that distinction survives the dispatch path
    too."""
    from mcp_server import mcp

    with pytest.raises(UnexpectedToolError) as exc_info:
        asyncio.run(mcp.call_tool("get_agent_by_name", {"agent_name": "Nonexistent Agent"}))
    assert isinstance(exc_info.value.__cause__, KeyError)


def test_calling_list_tool_catalog_through_the_server_returns_all_eight_entries():
    from mcp_server import mcp

    result = asyncio.run(mcp.call_tool("list_tool_catalog", {}))

    assert result.is_error is False
    payload = json.loads(result.content[0].text)
    assert len(payload["tools"]) == 8
    assert payload["source_name"] == "tool_catalog.json"


def test_calling_list_agent_ownership_through_the_server_returns_all_three_records():
    from mcp_server import mcp

    result = asyncio.run(mcp.call_tool("list_agent_ownership", {}))

    assert result.is_error is False
    payload = json.loads(result.content[0].text)
    assert len(payload["owners"]) == 3
    assert payload["source_name"] == "ownership.json"


def test_tool_catalog_and_ownership_remain_separately_auditable():
    """The concrete proof of this lab's learning goal: two distinct tool
    calls, each carrying its own independent provenance and trace ID -
    never merged into one response where you could no longer tell which
    claim came from which source."""
    from mcp_server import mcp

    catalog_result = asyncio.run(mcp.call_tool("list_tool_catalog", {}))
    ownership_result = asyncio.run(mcp.call_tool("list_agent_ownership", {}))

    catalog = json.loads(catalog_result.content[0].text)
    ownership = json.loads(ownership_result.content[0].text)

    assert catalog["source_name"] != ownership["source_name"]
    assert catalog["source_sha256"] != ownership["source_sha256"]
    assert catalog["correlation_id"] != ownership["correlation_id"]


def test_mcp_tool_decorator_turns_a_python_function_into_a_protocol_tool():
    """The concrete proof of this lab's learning goal: mcp.tool() reads
    a plain function's name and docstring and turns them into a
    protocol-level Tool object with a matching name and description.
    Uses its own disposable MCPServer instance, never the real shared
    `mcp` object in mcp_server.py, so this test can't leave a fake tool
    registered on the actual server."""
    probe_server = MCPServer("probe-only-server")

    @probe_server.tool()
    def example_tool() -> dict:
        """An example tool, used only to prove the decorator mechanism."""
        return {"ok": True}

    tools = asyncio.run(probe_server.list_tools())

    assert len(tools) == 1
    assert tools[0].name == "example_tool"
    assert tools[0].description == (
        "An example tool, used only to prove the decorator mechanism."
    )


def test_mcp_server_never_targets_stdout_for_logging():
    """Static check: mcp_server.py's logging setup never targets stdout
    - STDIO reserves it entirely for protocol messages.

    Not tested by inspecting the live root logger after import: pytest's
    own logging plugin pre-populates the root logger's handlers before
    any test code runs, and logging.basicConfig() is a documented no-op
    once the root logger already has handlers - so checking
    logging.getLogger().handlers here would silently pass or fail based
    on pytest's own internals, not mcp_server.py's actual configuration.
    Confirmed this by hand: a fresh call to basicConfig() had zero
    effect on the handler list under pytest."""
    source = (ROOT / "mcp_server.py").read_text(encoding="utf-8")
    assert "logging.basicConfig(" in source
    assert "stream=sys.stdout" not in source


def test_a_stream_handler_with_no_explicit_stream_defaults_to_stderr():
    """The concrete proof of the underlying mechanism this lab relies
    on: a logging.StreamHandler() created with no stream argument binds
    to sys.stderr, not sys.stdout - the reason mcp_server.py's plain
    logging.basicConfig(level=logging.INFO) call is safe under STDIO
    without needing to pass stream= explicitly."""
    handler = logging.StreamHandler()
    assert handler.stream is sys.stderr


def test_mcp_server_source_declares_exactly_five_tools():
    """Static proof, read directly from source rather than the runtime
    introspection Lab 5 already covers: exactly five @mcp.tool()
    decorators exist in mcp_server.py, one per discovery operation."""
    source = (ROOT / "mcp_server.py").read_text(encoding="utf-8")
    assert source.count("@mcp.tool()") == 5


def test_mcp_server_source_exposes_exactly_the_five_expected_tool_names():
    """Extracts each tool's function name directly from source via the
    decorator-then-def pattern, a second, source-level cross-check
    against Lab 5's runtime tool list."""
    source = (ROOT / "mcp_server.py").read_text(encoding="utf-8")
    tool_names = re.findall(r"@mcp\.tool\(\)\ndef (\w+)\(", source)
    assert tool_names == [
        "health_check",
        "list_agent_inventory",
        "get_agent_by_name",
        "list_tool_catalog",
        "list_agent_ownership",
    ]


def test_no_write_operation_exists_anywhere_in_the_discovery_source():
    """The concrete proof of this lab's learning goal: none of the
    source files backing the five exposed tools contain any code
    pattern that writes, deletes, or modifies a file. Checks specific
    call patterns, not the bare word "write" - discovery_core.py's own
    docstrings use that word in prose ("writes, creates, or deletes
    anything"), which would false-positive a naive substring check."""
    write_indicators = [
        "write_text(",
        "write_bytes(",
        '"w")',
        "'w')",
        "os.remove(",
        "os.unlink(",
        ".unlink(",
        "shutil.rmtree(",
        "shutil.move(",
    ]
    for filename in ["mcp_server.py", "discovery_core.py", "mcp_security.py"]:
        source = (ROOT / filename).read_text(encoding="utf-8")
        for indicator in write_indicators:
            assert indicator not in source, f"{indicator!r} found in {filename}"


def test_mcp_server_imports_cleanly_in_a_fresh_process_with_no_stdout_output():
    """The concrete proof for "imports": every other test imports
    mcp_server within the same pytest process, where Python's module
    cache means the top-level code (logging setup, MCPServer(...), all
    five @mcp.tool() registrations) only truly runs once, the first time
    anything imports it. This runs that first-time import in a genuinely
    separate process and confirms it's silent on stdout - the STDIO
    purity guarantee, verified under real process startup rather than
    inferred from source (Lab 7) or in-process behavior."""
    result = subprocess.run(
        [sys.executable, "-c", "import mcp_server"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == ""


def test_tool_schemas_match_their_function_signatures():
    """The concrete proof for "schemas": get_agent_by_name's real
    generated schema requires exactly agent_name, and the other four
    zero-argument tools generate schemas with no required fields at
    all - the SDK-derived contract matching each function's actual
    signature, not just assumed to."""
    from mcp_server import mcp

    tools = {tool.name: tool for tool in asyncio.run(mcp.list_tools())}

    assert tools["get_agent_by_name"].input_schema.get("required") == ["agent_name"]
    for name in [
        "health_check",
        "list_agent_inventory",
        "list_tool_catalog",
        "list_agent_ownership",
    ]:
        assert not tools[name].input_schema.get("required")
