"""Tests for mcp_security.py's shared exception type and safe_child().

Only imports mcp_security itself - no MCP package, no server. Proof that
a protocol-independent module can be tested in complete isolation.
"""

import hashlib
import json
from pathlib import Path

import pytest

from mcp_security import MCPAccessError, read_json_with_provenance, safe_child

BASE_DIR = Path(__file__).resolve().parent.parent / "connected_environment"
ALLOWED_FILES = {"agents.json", "tool_catalog.json", "ownership.json"}


def test_mcp_access_error_is_a_value_error():
    assert issubclass(MCPAccessError, ValueError)


def test_mcp_access_error_carries_its_message():
    error = MCPAccessError("File is not allowlisted: secret.json")
    assert str(error) == "File is not allowlisted: secret.json"


def test_safe_child_returns_path_for_allowlisted_name():
    result = safe_child(BASE_DIR, "agents.json", ALLOWED_FILES)
    assert result == BASE_DIR / "agents.json"


def test_safe_child_rejects_name_not_on_the_allowlist():
    with pytest.raises(MCPAccessError):
        safe_child(BASE_DIR, "secret.json", ALLOWED_FILES)


def test_safe_child_rejects_a_missing_relative_name():
    with pytest.raises(MCPAccessError):
        safe_child(BASE_DIR, None, ALLOWED_FILES)


def test_safe_child_rejects_an_empty_string_relative_name():
    with pytest.raises(MCPAccessError):
        safe_child(BASE_DIR, "", ALLOWED_FILES)


def test_safe_child_rejects_a_non_string_relative_name():
    with pytest.raises(MCPAccessError):
        safe_child(BASE_DIR, 12345, ALLOWED_FILES)


def test_safe_child_rejects_an_unhashable_relative_name():
    """The bug-fix test: verified by hand before writing this that a
    list used to crash safe_child() with a raw TypeError, because
    Python's `in` operator on a set must hash its left operand first,
    and a list can't be hashed. The isinstance(relative_name, str)
    check now runs before that comparison, so this raises the same
    clean MCPAccessError every other malformed name produces."""
    with pytest.raises(MCPAccessError):
        safe_child(BASE_DIR, ["agents.json"], ALLOWED_FILES)


def test_safe_child_rejects_an_oversized_relative_name():
    with pytest.raises(MCPAccessError):
        safe_child(BASE_DIR, "x" * 100_000, ALLOWED_FILES)


def test_safe_child_rejects_untrusted_notes_even_though_it_exists():
    """The concrete proof of this lab's learning goal: the file is real
    and sits in the same folder, but it was never authorized, so the
    server refuses it purely because it's not on the allowlist."""
    assert (BASE_DIR / "untrusted_notes.txt").exists()
    with pytest.raises(MCPAccessError):
        safe_child(BASE_DIR, "untrusted_notes.txt", ALLOWED_FILES)


def test_safe_child_returns_a_fully_resolved_path():
    result = safe_child(BASE_DIR, "agents.json", ALLOWED_FILES)
    assert result == result.resolve(strict=True)


def test_safe_child_blocks_a_symlink_even_when_its_target_stays_inside_base_dir(tmp_path):
    """The core lesson of this lab: a symlink can redirect to another
    file that's still inside base_dir, so a resolve()+parent check
    (Lab 3) alone would not catch it - the resolved path's parent looks
    perfectly fine. Only an explicit symlink check catches the
    indirection itself, regardless of where it points. Uses tmp_path,
    not the real connected_environment fixtures, so nothing real gets
    modified."""
    real_file = tmp_path / "real_data.json"
    real_file.write_text("{}")
    symlink_path = tmp_path / "agents.json"
    symlink_path.symlink_to(real_file)

    with pytest.raises(MCPAccessError):
        safe_child(tmp_path, "agents.json", {"agents.json"})


def test_safe_child_blocks_a_symlink_pointing_completely_outside_base_dir(tmp_path):
    """Completes the claim the test above only partly proves: the
    symlink check catches an indirection "regardless of where it
    points" - this is the more obvious direction (a resolve()+parent
    check alone would also catch this one), proving the symlink check
    is a real, independent layer, not one that only happened to work
    because of where the previous test's target landed."""
    outside_dir = tmp_path.parent / "outside_symlink_target"
    outside_dir.mkdir()
    real_file = outside_dir / "real_data.json"
    real_file.write_text("{}")
    symlink_path = tmp_path / "agents.json"
    symlink_path.symlink_to(real_file)

    with pytest.raises(MCPAccessError):
        safe_child(tmp_path, "agents.json", {"agents.json"})


def test_safe_child_rejects_a_near_miss_filename():
    """The allowlist is an exact string match, not a prefix or
    substring check - a name that merely resembles an allowed one is
    exactly as unapproved as a completely unrelated one."""
    with pytest.raises(MCPAccessError):
        safe_child(BASE_DIR, "agents.json.bak", ALLOWED_FILES)


def test_safe_child_blocks_a_directory_masquerading_as_a_file(tmp_path):
    fake_file = tmp_path / "agents.json"
    fake_file.mkdir()

    with pytest.raises(MCPAccessError):
        safe_child(tmp_path, "agents.json", {"agents.json"})


def test_safe_child_blocks_traversal_even_if_allowlist_is_misconfigured():
    """Defense in depth: resolve() plus the parent check block a path
    escape independently of the allowlist, in case a traversal string
    were ever mistakenly added to allowed_names by a future caller."""
    traversal_name = "../requirements.txt"
    misconfigured_allowlist = {"agents.json", traversal_name}
    # The target genuinely exists one level above connected_environment/,
    # so resolve(strict=True) succeeds - it's the parent check, not a
    # missing file, that has to catch this escape.
    assert (BASE_DIR / traversal_name).resolve(strict=True).exists()
    with pytest.raises(MCPAccessError):
        safe_child(BASE_DIR, traversal_name, misconfigured_allowlist)


def test_safe_child_rejects_a_traversal_string_via_the_allowlist_alone():
    """The realistic case, distinct from the misconfigured-allowlist
    test above: against the real, correctly-configured allowlist, a
    traversal string is rejected by the allowlist check itself - no
    filesystem access ever happens, since "../requirements.txt" simply
    isn't one of the three allowed exact names."""
    with pytest.raises(MCPAccessError):
        safe_child(BASE_DIR, "../requirements.txt", ALLOWED_FILES)


def test_safe_child_rejects_an_absolute_path_via_the_allowlist_alone():
    with pytest.raises(MCPAccessError):
        safe_child(BASE_DIR, "/etc/passwd", ALLOWED_FILES)


def test_safe_child_blocks_an_absolute_path_even_if_allowlist_is_misconfigured(tmp_path):
    """A different escape mechanism than a relative traversal string:
    in Python's pathlib, joining an absolute path onto base_dir with
    `/` does not concatenate at all - `Path("/a/b") / "/etc/passwd"`
    silently discards "/a/b" and evaluates to "/etc/passwd" alone.
    Verified this by hand before writing this test. So even once the
    allowlist is misconfigured to allow it, the parent check still
    catches it, because the resolved candidate's parent is nowhere
    near connected_environment/."""
    outside_file = tmp_path.parent / "outside_target.json"
    outside_file.write_text("{}")
    absolute_name = str(outside_file)
    misconfigured_allowlist = {"agents.json", absolute_name}

    with pytest.raises(MCPAccessError):
        safe_child(BASE_DIR, absolute_name, misconfigured_allowlist)


def test_read_json_with_provenance_returns_payload_name_and_hash(tmp_path):
    data_file = tmp_path / "sample.json"
    data_file.write_text('{"key": "value"}')

    result = read_json_with_provenance(data_file)

    assert result["payload"] == {"key": "value"}
    assert result["source_name"] == "sample.json"
    assert result["source_sha256"] == hashlib.sha256(data_file.read_bytes()).hexdigest()


def test_read_json_with_provenance_hash_changes_when_content_changes(tmp_path):
    """The concrete proof of this lab's learning goal: the same file
    path, with different content, produces a different hash - proving
    the hash genuinely reflects what was read, not just a filename
    label that could go stale."""
    data_file = tmp_path / "sample.json"

    data_file.write_text('{"key": "value"}')
    first_hash = read_json_with_provenance(data_file)["source_sha256"]

    data_file.write_text('{"key": "different"}')
    second_hash = read_json_with_provenance(data_file)["source_sha256"]

    assert first_hash != second_hash


def test_read_json_with_provenance_composes_with_safe_child_on_a_real_file():
    path = safe_child(BASE_DIR, "agents.json", ALLOWED_FILES)
    result = read_json_with_provenance(path)

    assert result["source_name"] == "agents.json"
    assert "agents" in result["payload"]
    assert len(result["source_sha256"]) == 64


def test_read_json_with_provenance_rejects_malformed_json(tmp_path):
    """A forbidden-input case, distinct from every forbidden-access case
    tested above: a file can pass every access check (allowlisted,
    safely resolved, not a symlink, a real file) and still be
    unreadable as JSON. This should fail loudly and specifically, not
    silently return garbage."""
    bad_file = tmp_path / "corrupt.json"
    bad_file.write_text("{not valid json")

    with pytest.raises(json.JSONDecodeError):
        read_json_with_provenance(bad_file)


def test_safe_child_rejects_a_wildcard_allowlist_entry():
    """Day 8, Lab 6: allowed_names is a capability allowlist too, just
    for files instead of MCP tool names - the same "unexpected
    capability" defense mcp_client.py's EXPECTED_TOOLS provides for
    tools (tested in tests/test_mcp_client.py, out of this lab's file
    scope). A wildcard entry is rejected the same as any other
    unlisted name, proving there's no special-case interpretation of
    "*" anywhere in the exact-match logic - mirroring v1's own AG-001
    rule, which already treats a wildcard as the single riskiest
    pattern a tool list can contain."""
    with pytest.raises(MCPAccessError):
        safe_child(BASE_DIR, "agents.json", {"*"})


def test_safe_child_grants_no_access_beyond_the_explicit_allowlist():
    """A real, legitimate file in the same folder - not a fake or
    malicious name - is still rejected when this specific call's
    allowlist doesn't happen to include it. No "same folder" or
    "adjacent file" capability is ever implicitly granted beyond the
    literal set passed to this one call."""
    with pytest.raises(MCPAccessError):
        safe_child(BASE_DIR, "ownership.json", {"agents.json"})


def test_reading_every_allowlisted_file_through_the_real_pipeline_leaves_bytes_unchanged():
    """The concrete proof of this lab's learning goal: safe_child() and
    read_json_with_provenance() together are the only way anything in
    v3 ever touches connected_environment/ files - discovery_core.py's
    own functions call nothing else. Hashing all three real files
    before and after exercising both real functions on each one,
    several times over, proves the whole system performs no writes -
    not just this one function in isolation."""

    def hash_all_files() -> dict[str, str]:
        return {
            name: hashlib.sha256((BASE_DIR / name).read_bytes()).hexdigest()
            for name in ALLOWED_FILES
        }

    before_hashes = hash_all_files()

    for _ in range(3):
        for name in ALLOWED_FILES:
            path = safe_child(BASE_DIR, name, ALLOWED_FILES)
            read_json_with_provenance(path)

    after_hashes = hash_all_files()

    assert before_hashes == after_hashes
