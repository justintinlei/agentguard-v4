"""Tests for policy_library.py: unique IDs, nonempty text, reproducible hashes."""

import hashlib
from pathlib import Path

from policy_library import load_policy_chunks

POLICIES_DIR = Path(__file__).resolve().parent.parent / "policies"


def test_loading_produces_ten_chunks():
    chunks = load_policy_chunks(POLICIES_DIR)
    assert len(chunks) == 10


def test_all_chunk_ids_are_unique():
    chunks = load_policy_chunks(POLICIES_DIR)
    chunk_ids = [chunk.chunk_id for chunk in chunks]
    assert len(set(chunk_ids)) == len(chunk_ids)


def test_every_chunk_has_nonempty_text():
    chunks = load_policy_chunks(POLICIES_DIR)
    for chunk in chunks:
        assert chunk.text.strip() != ""


def test_hashes_are_reproducible():
    chunks = load_policy_chunks(POLICIES_DIR)
    for chunk in chunks:
        recomputed = hashlib.sha256(chunk.text.encode("utf-8")).hexdigest()
        assert recomputed == chunk.sha256
