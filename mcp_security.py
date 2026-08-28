"""Security helpers shared by the MCP server, client adapter, and tests.

Kept as its own module, separate from discovery_core.py, so security
logic (path safety, allowlisting) has exactly one place to live and one
place to test - independent of both the discovery functions that will
use it and the transport layer that will eventually call those
functions. The real path-safety logic is built incrementally in later
Day 4 labs (the file allowlist, safe path resolution, symlink defense);
this lab only establishes the module and its shared error type.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class MCPAccessError(ValueError):
    """Raised when a requested connected-environment file is not safe to read.

    A subclass of ValueError, not a bare Exception, so callers already
    handling standard input-validation errors catch this too without a
    separate except clause.
    """


def safe_child(base_dir: Path, relative_name: str, allowed_names: set[str]) -> Path:
    """Return one allowlisted, non-symlink, regular file inside base_dir.

    Security order matters:
    1. relative_name must be a string at all - Python's `in` operator
       on a set has to hash its left operand first, and an unhashable
       value (a list, a dict) would raise a raw TypeError here instead
       of a clean MCPAccessError if this check ran second.
    2. The caller must request an exact allowlisted filename.
    3. The raw path is checked for a symbolic link *before* resolve() -
       a resolved path's parent can look perfectly safe even when it was
       reached through a redirect, so this has to happen first.
    4. The resolved path must remain directly inside base_dir.
    5. The target must be a regular file, not a directory or anything
       else masquerading under an allowlisted name.

    Note: resolve(strict=True) requires the target to actually exist, so
    a name that passes the allowlist but doesn't exist on disk still
    raises Python's own FileNotFoundError here, not MCPAccessError -
    left as-is, since wrapping it isn't in scope for these labs.
    """
    if not isinstance(relative_name, str) or relative_name not in allowed_names:
        raise MCPAccessError(f"File is not allowlisted: {relative_name!r}")

    base = base_dir.resolve(strict=True)
    raw_candidate = base / relative_name
    if raw_candidate.is_symlink():
        raise MCPAccessError("Symbolic links are not allowed.")

    candidate = raw_candidate.resolve(strict=True)
    if candidate.parent != base:
        raise MCPAccessError("Resolved path escaped the connected environment.")
    if not candidate.is_file():
        raise MCPAccessError("Only regular files are allowed.")
    return candidate


def read_json_with_provenance(path: Path) -> dict:
    """Read JSON from path and return it alongside proof of what was read.

    The SHA-256 hash is computed from the exact raw bytes on disk, before
    any parsing - so it's a fingerprint of the real file content, not of
    whatever Python's JSON parser produced. A later re-hash of the same
    file can be compared against this value to confirm the data hasn't
    changed since it was scanned.

    This function trusts that path was already validated - it does not
    re-check the allowlist itself, since that's safe_child's job.
    """
    raw = path.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    return {
        "source_name": path.name,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "payload": payload,
    }
