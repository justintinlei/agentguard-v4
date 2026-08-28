"""Tests for scripts/validate_starter_kit.py's parsing/checking functions."""

from pathlib import Path

import pytest

from scripts.validate_starter_kit import (
    EXPECTED_LAB_COUNT,
    EXPECTED_TOOL_NAMES,
    ROOT,
    check_five_readonly_tools,
    check_no_local_paths,
    check_python_syntax,
    client_expected_tools,
    count_labs,
    local_path_hits,
    missing_paths,
    referenced_prompt_paths,
    server_tool_names,
)

INDEX_PATH = ROOT / "docs" / "lab_execution_index.md"
SERVER_TEXT = (ROOT / "mcp_server.py").read_text(encoding="utf-8")
CLIENT_TEXT = (ROOT / "mcp_client.py").read_text(encoding="utf-8")


def test_index_has_expected_lab_count():
    index_text = INDEX_PATH.read_text(encoding="utf-8")
    assert count_labs(index_text) == EXPECTED_LAB_COUNT


def test_every_referenced_prompt_file_exists():
    index_text = INDEX_PATH.read_text(encoding="utf-8")
    prompts = referenced_prompt_paths(index_text)
    assert len(prompts) == EXPECTED_LAB_COUNT
    assert missing_paths(ROOT, prompts) == []


def test_missing_paths_reports_a_path_that_really_is_missing():
    assert missing_paths(ROOT, ["definitely_not_a_real_file.txt"]) == [
        "definitely_not_a_real_file.txt"
    ]


def test_check_python_syntax_passes_on_this_repo():
    # No exception means every tracked .py file parsed successfully.
    check_python_syntax(ROOT)


# --- Day 10, Lab 2: the "exactly five read-only tools" source check --------

def test_server_registers_exactly_the_five_expected_tools():
    tools = server_tool_names(SERVER_TEXT)
    assert len(tools) == 5
    assert set(tools) == EXPECTED_TOOL_NAMES


def test_client_allowlist_matches_the_server():
    assert client_expected_tools(CLIENT_TEXT) == set(server_tool_names(SERVER_TEXT))


def test_check_five_readonly_tools_passes_on_this_repo():
    check_five_readonly_tools(SERVER_TEXT, CLIENT_TEXT)  # no exception


def test_check_five_readonly_tools_rejects_a_sixth_tool():
    sixth = SERVER_TEXT + '\n\n@mcp.tool()\ndef list_extra_thing() -> dict:\n    return {}\n'
    with pytest.raises(SystemExit, match="registers 6 tools"):
        check_five_readonly_tools(sixth, CLIENT_TEXT)


def test_check_five_readonly_tools_rejects_a_write_verb_tool():
    # Swap one real tool for a write-shaped name so the count stays 5.
    tampered = SERVER_TEXT.replace("def list_tool_catalog(", "def delete_tool_catalog(")
    with pytest.raises(SystemExit, match="write operation"):
        check_five_readonly_tools(tampered, CLIENT_TEXT)


def test_check_five_readonly_tools_rejects_a_client_server_mismatch():
    shrunk_client = CLIENT_TEXT.replace('    "list_agent_ownership",\n', "")
    with pytest.raises(SystemExit, match="EXPECTED_TOOLS"):
        check_five_readonly_tools(SERVER_TEXT, shrunk_client)


# --- Day 10, Lab 7: the public-repo local-path check ----------------------

def test_no_local_paths_on_this_repo():
    check_no_local_paths(ROOT)  # no exception


def test_local_path_hits_flags_a_real_home_path(tmp_path):
    # Built at runtime so this test file's own source has no contiguous
    # "/Users/<realname>/" literal for the repo-wide scan to trip on.
    bad_path = "/" + "Users/realdev/Developer/thing/.venv/bin/python"
    (tmp_path / "notes.md").write_text(f"the venv lives at {bad_path}\n", encoding="utf-8")

    hits = local_path_hits(tmp_path)
    assert len(hits) == 1 and hits[0].startswith("notes.md:")


def test_local_path_hits_ignores_placeholder_users(tmp_path):
    # A deliberately fictional path in a test fixture must not trip the check.
    (tmp_path / "t.py").write_text('BAD = "/Users/alice/.ssh/id_rsa"\n', encoding="utf-8")
    assert local_path_hits(tmp_path) == []
