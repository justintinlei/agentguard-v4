"""Run AgentGuard v3's security evaluation suite.

Two passes, mirroring run_v2_evals.py's pattern: regression first
(python -m pytest -q - did everything built through Day 7 stay
correct), then a category-by-category rerun of docs/v3_threat_model.md's
checklist, using the exact test names each entry maps to. Regression
runs first and fails fast, since there's no point proving individual
threat categories on top of a baseline that's already broken. There's
no "AI output quality" matrix here the way v2's evals has - v3's
security suite is entirely deterministic, so the second pass exists to
prove the checklist itself, not to grade anything.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# One entry per docs/v3_threat_model.md category, mapped to the exact
# test names that formally prove it - grepped directly from the real
# test files while writing this, not typed from memory.
CHECKLIST: list[tuple[str, list[str]]] = [
    (
        "Path traversal / absolute paths",
        [
            "tests/test_mcp_security.py::test_safe_child_blocks_traversal_even_if_allowlist_is_misconfigured",
            "tests/test_mcp_security.py::test_safe_child_rejects_a_traversal_string_via_the_allowlist_alone",
            "tests/test_mcp_security.py::test_safe_child_rejects_an_absolute_path_via_the_allowlist_alone",
            "tests/test_mcp_security.py::test_safe_child_blocks_an_absolute_path_even_if_allowlist_is_misconfigured",
        ],
    ),
    (
        "Unapproved filenames / symlink escape",
        [
            "tests/test_mcp_security.py::test_safe_child_rejects_name_not_on_the_allowlist",
            "tests/test_mcp_security.py::test_safe_child_rejects_untrusted_notes_even_though_it_exists",
            "tests/test_mcp_security.py::test_safe_child_blocks_a_symlink_even_when_its_target_stays_inside_base_dir",
            "tests/test_mcp_security.py::test_safe_child_blocks_a_symlink_pointing_completely_outside_base_dir",
            "tests/test_mcp_security.py::test_safe_child_rejects_a_near_miss_filename",
            "tests/test_mcp_security.py::test_safe_child_blocks_a_directory_masquerading_as_a_file",
        ],
    ),
    (
        "Missing fields, wrong types, oversized names",
        [
            "tests/test_mcp_security.py::test_safe_child_rejects_a_missing_relative_name",
            "tests/test_mcp_security.py::test_safe_child_rejects_an_empty_string_relative_name",
            "tests/test_mcp_security.py::test_safe_child_rejects_a_non_string_relative_name",
            "tests/test_mcp_security.py::test_safe_child_rejects_an_unhashable_relative_name",
            "tests/test_mcp_security.py::test_safe_child_rejects_an_oversized_relative_name",
        ],
    ),
    (
        "Prompt injection as untrusted data",
        [
            "tests/test_untrusted_content.py::test_untrusted_notes_fixture_is_labeled_as_intentional_test_content",
            "tests/test_untrusted_content.py::test_untrusted_notes_fixture_documents_the_scanner_authority_rule",
            "tests/test_untrusted_content.py::test_read_json_with_provenance_treats_injected_instructions_as_inert_data",
            "tests/test_untrusted_content.py::test_read_json_with_provenance_treats_the_real_injection_fixture_as_inert_data",
        ],
    ),
    (
        "Unexpected server tool name (capability expansion)",
        [
            "tests/test_mcp_security.py::test_safe_child_rejects_a_wildcard_allowlist_entry",
            "tests/test_mcp_security.py::test_safe_child_grants_no_access_beyond_the_explicit_allowlist",
        ],
    ),
    (
        "Byte-for-byte file integrity",
        [
            "tests/test_mcp_security.py::test_reading_every_allowlisted_file_through_the_real_pipeline_leaves_bytes_unchanged",
            "tests/test_untrusted_content.py::test_untrusted_notes_file_remains_byte_for_byte_unchanged",
        ],
    ),
]


def run(command: list[str]) -> None:
    print(f"\n>>> {' '.join(command)}", flush=True)
    result = subprocess.run(command, cwd=PROJECT_ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)


def main() -> None:
    print("=== AgentGuard v3 Security Evaluation Suite ===")
    run([sys.executable, "-m", "pytest", "-q"])

    print("\n=== Threat Model Checklist Coverage ===")
    for category, test_ids in CHECKLIST:
        run([sys.executable, "-m", "pytest", "-q", *test_ids])
        print(f"[PASS] {category} ({len(test_ids)} tests)")

    print("\nV3 SECURITY EVAL SUITE PASS")


if __name__ == "__main__":
    main()
