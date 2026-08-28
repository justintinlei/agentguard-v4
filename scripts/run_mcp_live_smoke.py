"""Optional live MCP smoke test.

Starts the real mcp_server.py process and calls two tools through
mcp_client.py - the first true end-to-end proof outside Inspector, and
this lab's readable automated test. Run manually after installing
requirements; not part of the `pytest -q` suite.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp_client import call_tool_sync

health = call_tool_sync("health_check")
assert health["status"] == "ok"
assert health["mode"] == "read-only"
assert health["tool_count"] == 5

inventory = call_tool_sync("list_agent_inventory")
assert inventory["count"] == 3
assert len(inventory["source_sha256"]) == 64

print("MCP LIVE SMOKE PASS")
print("Health:", health["status"], health["mode"])
print("Discovered agents:", inventory["count"])
