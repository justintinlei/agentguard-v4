"""Validate that this repo's own course scaffolding is complete and every
tracked Python file at least parses.

Adapted from the reference starter kit's validate_starter_kit.py, which
checks against a lab_manifest.json (an 80-entry JSON file) that this repo
doesn't have - this project uses docs/lab_execution_index.md instead.
Also, unlike the reference kit (a finished, all-labs-done snapshot), this
repo is still mid-course, so this only checks that each lab's PROMPT file
exists (always true from Day 1) - not that every lab's future deliverable
already exists, since many labs later in the course haven't run yet.
"""

from __future__ import annotations

import py_compile
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "docs" / "lab_execution_index.md"
EXPECTED_LAB_COUNT = 80  # 10 days x 8 labs each

LAB_HEADING_PATTERN = re.compile(r"^## Day \d+ · Lab \d+ ·", re.MULTILINE)
PROMPT_LINE_PATTERN = re.compile(r"^- Prompt: `([^`]+)`", re.MULTILINE)

# Public-repo readiness: an absolute /Users/<user>/ or /home/<user>/ path in
# a committed file leaks the author's username and machine layout. The
# [A-Za-z] start deliberately skips an already-redacted "/Users/.../".
LOCAL_PATH_PATTERN = re.compile(r"/(?:Users|home)/([A-Za-z][\w.-]*)/")

# Obviously-fictional user names that test fixtures use on purpose (the
# same idea as the fake API token in tests/test_v2_service.py).
PLACEHOLDER_USERS = {
    "alice", "bob", "carol", "dave", "example", "user",
    "you", "me", "test", "yourname", "youruser",
}

TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".yml", ".yaml", ".example", ".gitignore"}
SKIP_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache"}

# v3's central security promise: the MCP server exposes exactly these five
# tools and every one is read-only. This is the one canonical list; it
# must match mcp_client.EXPECTED_TOOLS exactly.
EXPECTED_TOOL_NAMES = {
    "health_check",
    "list_agent_inventory",
    "get_agent_by_name",
    "list_tool_catalog",
    "list_agent_ownership",
}

# A tool name with any of these as an underscore-separated word reads as
# a write/state-change and has no place in a read-only discovery server.
WRITE_VERBS = {
    "create", "update", "delete", "write", "put", "post", "remove",
    "add", "modify", "patch", "deploy", "rollback", "set",
}

SERVER_TOOL_PATTERN = re.compile(r"@mcp\.tool\(\)\s*\ndef\s+(\w+)\s*\(")
CLIENT_ALLOWLIST_PATTERN = re.compile(r"EXPECTED_TOOLS\s*=\s*\{([^}]*)\}")


def count_labs(index_text: str) -> int:
    """Count how many '## Day N · Lab M ·' headings the index has."""
    return len(LAB_HEADING_PATTERN.findall(index_text))


def referenced_prompt_paths(index_text: str) -> list[str]:
    """Return every prompt file path named in a '- Prompt: `...`' line."""
    return PROMPT_LINE_PATTERN.findall(index_text)


def missing_paths(root: Path, paths: list[str]) -> list[str]:
    """Return every path (relative to root) that doesn't exist on disk."""
    return sorted(path for path in paths if not (root / path).exists())


def check_python_syntax(root: Path) -> None:
    """Confirm every tracked .py file at least parses (raises on failure)."""
    for path in root.rglob("*.py"):
        if any(part in {".venv", "__pycache__", ".git"} for part in path.parts):
            continue
        py_compile.compile(str(path), doraise=True)


def server_tool_names(server_text: str) -> list[str]:
    """Every function name decorated with @mcp.tool() in mcp_server.py,
    in file order - pure source inspection, no import, no server."""
    return SERVER_TOOL_PATTERN.findall(server_text)


def client_expected_tools(client_text: str) -> set[str]:
    """The tool names inside mcp_client.py's EXPECTED_TOOLS = { ... } set."""
    match = CLIENT_ALLOWLIST_PATTERN.search(client_text)
    if not match:
        raise SystemExit("FAIL: mcp_client.py has no EXPECTED_TOOLS set literal")
    return set(re.findall(r'"([^"]+)"', match.group(1)))


def _text_files(root: Path):
    """Yield every tracked-style text file under root, skipping caches/venv."""
    for path in root.rglob("*"):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name == ".gitignore":
            yield path


def local_path_hits(root: Path) -> list[str]:
    """Return 'relpath:line' for every file containing an absolute home path
    that names a real (non-placeholder) user - the kind of string that
    leaks the author's machine layout into a public repo."""
    hits = []
    for path in _text_files(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), 1):
            for match in LOCAL_PATH_PATTERN.finditer(line):
                if match.group(1).lower() not in PLACEHOLDER_USERS:
                    hits.append(f"{path.relative_to(root)}:{lineno}")
    return hits


def check_no_local_paths(root: Path) -> None:
    """Fail if any committed text file carries an absolute author-machine path."""
    hits = local_path_hits(root)
    if hits:
        raise SystemExit(
            "FAIL: absolute home paths found (remove before publishing): "
            + ", ".join(hits)
        )


def check_five_readonly_tools(server_text: str, client_text: str) -> None:
    """Prove, from source alone, that the server exposes exactly the five
    expected tools, the client's allowlist matches, and no tool name is a
    write operation. Raises SystemExit on any mismatch."""
    server_tools = server_tool_names(server_text)
    client_tools = client_expected_tools(client_text)

    if len(server_tools) != 5:
        raise SystemExit(
            f"FAIL: mcp_server.py registers {len(server_tools)} tools, expected 5: {server_tools}"
        )
    for name in server_tools:
        if WRITE_VERBS & set(name.lower().split("_")):
            raise SystemExit(f"FAIL: tool name '{name}' looks like a write operation")
    if set(server_tools) != EXPECTED_TOOL_NAMES:
        raise SystemExit(
            f"FAIL: mcp_server.py tool set {sorted(server_tools)} != {sorted(EXPECTED_TOOL_NAMES)}"
        )
    if client_tools != EXPECTED_TOOL_NAMES:
        raise SystemExit(
            f"FAIL: mcp_client.py EXPECTED_TOOLS {sorted(client_tools)} != {sorted(EXPECTED_TOOL_NAMES)}"
        )


def main() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    lab_count = count_labs(index_text)
    if lab_count != EXPECTED_LAB_COUNT:
        raise SystemExit(f"FAIL: expected {EXPECTED_LAB_COUNT} labs, found {lab_count}")

    missing = missing_paths(ROOT, referenced_prompt_paths(index_text))
    if missing:
        raise SystemExit("FAIL: missing referenced prompt files: " + ", ".join(missing))

    check_python_syntax(ROOT)

    check_no_local_paths(ROOT)
    print("NO LOCAL PATHS: no author machine paths in tracked text")

    check_five_readonly_tools(
        (ROOT / "mcp_server.py").read_text(encoding="utf-8"),
        (ROOT / "mcp_client.py").read_text(encoding="utf-8"),
    )
    print("MCP TOOL SET VERIFIED: 5 read-only tools (mcp_server.py + mcp_client.py)")

    print(f"STARTER KIT VALIDATION PASS: {lab_count} labs and all referenced prompt files exist")


if __name__ == "__main__":
    main()
