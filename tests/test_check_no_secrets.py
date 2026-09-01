"""Tests for scripts/check_no_secrets.py (Day 2, Lab 8).

The scan must catch every credential shape in PATTERNS, must NOT match a
masked or merely-described token, and must pass on this repo as it stands.
Fake tokens are assembled at runtime so this test file never contains a
real match (the same trick tests/test_app_v3.py and test_app_v4.py use).
"""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "check_no_secrets", ROOT / "scripts" / "check_no_secrets.py"
)
cns = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cns)  # importing has no side effects: main() is guarded


def _matches(text: str) -> bool:
    return any(pattern.search(text) for pattern in cns.PATTERNS)


def test_repo_has_no_committed_secret():
    assert cns.scan(ROOT) == []


def test_catches_an_anthropic_api_key():
    assert _matches("sk-ant-" + "A1b2C3d4E5f6G7h8J9k0")


def test_catches_a_github_fine_grained_pat():
    assert _matches("github_pat_" + "A" * 22)


def test_catches_every_github_token_prefix():
    body = "a1B2c3D4" * 5  # 40 chars, well over the 36 minimum
    for prefix in ("gho_", "ghp_", "ghs_", "ghr_", "ghu_"):
        assert _matches(prefix + body), prefix


def test_does_not_match_a_masked_or_described_token():
    # a masked value from `gh auth status`
    assert not _matches("reported as gho_************************************")
    # a sentence that names the prefixes (like this repo's learning log)
    assert not _matches(
        "the scanner catches a ghp_ classic token or a github_pat_ fine-grained one"
    )


def test_short_prefix_alone_is_not_a_match():
    # prefix without a credential body must not fire
    assert not _matches("gho_")
    assert not _matches("sk-ant-")


# --- Day 9 Lab 6: the scan also covers the extensionless Docker config ----

_FAKE_TOKEN = "gho_" + "a1B2c3D4" * 5  # 40-char body, over the 36 minimum


def test_scan_covers_dockerfile_and_dockerignore(tmp_path):
    (tmp_path / "Dockerfile").write_text(f"ENV KEY={_FAKE_TOKEN}\n", encoding="utf-8")
    (tmp_path / ".dockerignore").write_text(f"# leftover note {_FAKE_TOKEN}\n", encoding="utf-8")
    hits = set(cns.scan(tmp_path))
    assert hits == {"Dockerfile", ".dockerignore"}


def test_scan_ignores_other_extensionless_files(tmp_path):
    # The name list is exact - a random extensionless file is not scanned.
    (tmp_path / "LICENSE").write_text(f"granted to {_FAKE_TOKEN}\n", encoding="utf-8")
    assert cns.scan(tmp_path) == []


def test_compose_yaml_is_covered_by_the_suffix_scan(tmp_path):
    (tmp_path / "compose.yaml").write_text(f"    KEY: {_FAKE_TOKEN}\n", encoding="utf-8")
    assert cns.scan(tmp_path) == ["compose.yaml"]
