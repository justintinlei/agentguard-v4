"""Fail if any tracked text file contains a key- or token-shaped string.

Run it directly, or via `scripts/run_release_gate.py` (step 5 of the gate).
Import `PATTERNS` / `scan()` to test it.

Each pattern is deliberately precise - it requires the full credential
shape (a real prefix plus a long body). Documentation that merely *names*
a token prefix (this module's own comments, the learning log, the demo
setup doc) therefore never trips the scan.

Files are picked by suffix (TEXT_SUFFIXES) or, for the extensionless
config files, by exact name (TEXT_NAMES): `.gitignore`, plus `Dockerfile`
and `.dockerignore` since Day 9 Lab 6.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATTERNS = (
    re.compile(r"sk-ant-[A-Za-z0-9_-]{16,}"),      # Anthropic API key
    re.compile(r"github_pat_[A-Za-z0-9_]{16,}"),   # GitHub fine-grained PAT
    re.compile(r"gh[oprsu]_[A-Za-z0-9]{36,}"),     # GitHub OAuth / classic PAT / server / refresh / user token
)

TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".yml", ".yaml", ".example", ".gitignore"}
# Config files with no suffix, matched by exact name (Day 9 Lab 6 added
# the two Docker ones so a credential cannot be baked into the image
# config undetected).
TEXT_NAMES = {".gitignore", ".dockerignore", "Dockerfile"}
SKIP_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache"}


def scan(root: Path = ROOT) -> list[str]:
    """Return the relative path of every tracked text file under `root`
    that contains a string matching one of PATTERNS."""
    hits: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in TEXT_NAMES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.search(text) for pattern in PATTERNS):
            hits.append(str(path.relative_to(root)))
    return hits


def main() -> None:
    hits = scan()
    if hits:
        raise SystemExit("SECRET CHECK FAIL: " + ", ".join(hits))
    print("SECRET CHECK PASS")


if __name__ == "__main__":
    main()
