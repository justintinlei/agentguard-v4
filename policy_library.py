"""Represents policy source passages as structured Python data.

Loads the markdown files in `policies/`, splits each one into sections
(one PolicyChunk per heading), and records a SHA-256 hash of each
chunk's exact text for provenance.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class PolicyChunk:
    """One retrievable passage from a policy document.

    Frozen (read-only after creation) so nothing downstream in the
    retrieval/grounding pipeline can accidentally change a chunk's
    content once it's been loaded.
    """

    chunk_id: str
    policy_id: str
    title: str
    text: str
    source_path: str
    sha256: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


# Matches a markdown heading line: 1 to 3 "#" characters, then the title.
HEADING_PATTERN = re.compile(r"^#{1,3}\s+(.+)$")


def _policy_id_from_filename(path: Path) -> str:
    """"AGP-001-agent-ownership.md" -> "AGP-001"."""
    name_parts = path.stem.split("-")
    return "-".join(name_parts[:2]).upper()


def _split_into_sections(lines: list[str]) -> list[tuple[str, list[str]]]:
    """Group a file's lines into (heading_title, body_lines) sections.

    Every time a heading line is seen, the section being built so far is
    closed out and a new one starts. Text before the first heading (if
    any) becomes a section with an empty title, which the caller drops.
    """
    sections: list[tuple[str, list[str]]] = []
    current_title = ""
    current_lines: list[str] = []

    for line in lines:
        heading_match = HEADING_PATTERN.match(line.strip())
        if heading_match:
            sections.append((current_title, current_lines))
            current_title = heading_match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    sections.append((current_title, current_lines))
    return sections


def _sections_to_chunks(
    path: Path, policy_id: str, sections: list[tuple[str, list[str]]]
) -> list[PolicyChunk]:
    """Turn non-empty sections into numbered PolicyChunks."""
    chunks: list[PolicyChunk] = []
    section_number = 0

    for title, body_lines in sections:
        text = "\n".join(body_lines).strip()
        if not text:
            continue
        section_number += 1
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        chunks.append(
            PolicyChunk(
                chunk_id=f"{policy_id}-S{section_number:02d}",
                policy_id=policy_id,
                title=title,
                text=text,
                source_path=str(path),
                sha256=digest,
            )
        )

    return chunks


def load_policy_chunks(policy_dir: Path) -> list[PolicyChunk]:
    """Read every .md file in policy_dir and split it into PolicyChunks."""
    all_chunks: list[PolicyChunk] = []

    for path in sorted(policy_dir.glob("*.md")):
        policy_id = _policy_id_from_filename(path)
        lines = path.read_text(encoding="utf-8").splitlines()
        sections = _split_into_sections(lines)
        all_chunks.extend(_sections_to_chunks(path, policy_id, sections))

    return all_chunks
