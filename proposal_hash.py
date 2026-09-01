"""Canonical content hashing for proposals and approval binding.

An approval in v4 is pinned to two fingerprints: the exact proposal that
was reviewed, and the exact source environment it was built against.
`validate_approval()` (see `approval.py`) refuses to let a proposal
proceed unless both fingerprints still match. That only works if the same
content *always* produces the same fingerprint.

`canonical_json()` gives us that. `json.dumps` on its own lets two things
that are not part of the data leak into the bytes you hash:

  - key order - Python dicts remember insertion order, so
    `{"a": 1, "b": 2}` and `{"b": 2, "a": 1}` serialise to different
    text. `sort_keys=True` fixes the order.
  - whitespace - the default puts a space after every `:` and `,`.
    `separators=(",", ":")` removes it.

`ensure_ascii=True` also pins non-ASCII characters to fixed `\\uXXXX`
escapes so the text does not depend on file or terminal encoding.

With all three, equal data becomes byte-identical text, so equal data
gets an identical SHA-256 digest.

Note: unlike the Day 3 slice, this does not pass `default=str`. Only
genuine JSON types (dict / list / str / int / float / bool / None) can be
hashed; anything else raises `TypeError` instead of being silently
coerced to a string a different object might share.
"""

from __future__ import annotations

import hashlib
import json


def canonical_json(value: object) -> str:
    """Serialise `value` to JSON with one fixed spelling per value.

    Sorted keys + no incidental whitespace + ASCII escapes, so equal data
    always produces byte-identical text.
    """
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_value(value: object) -> str:
    """SHA-256 hex digest of the canonical JSON of `value` (64 hex chars)."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
