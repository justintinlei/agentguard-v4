"""Validates a GroundedAnalysis's content, not just its shape.

Pydantic (analysis_schema.py) already confirmed the response has the
right fields and types. This checks something Pydantic can't: did the
model report v1's real score back unchanged, and does every citation
point at real evidence with a quote that's actually in it.
"""

from __future__ import annotations

from analysis_schema import GroundedAnalysis
from retrieval import RetrievalHit
from scanner import ScanResult


class GroundingError(ValueError):
    """Raised when a GroundedAnalysis fails a grounding check."""


def validate_grounding(
    analysis: GroundedAnalysis,
    scan_result: ScanResult,
    evidence: list[RetrievalHit],
) -> GroundedAnalysis:
    """Check analysis against the real scan result and real evidence.

    Raises GroundingError on the first violation found. Returns analysis
    unchanged if every check passes - this function never edits or
    "fixes" a bad analysis, only accepts or rejects it.
    """
    if analysis.deterministic_risk_level != scan_result.risk_level:
        raise GroundingError("The model changed the deterministic risk level.")
    if analysis.deterministic_risk_score != scan_result.score:
        raise GroundingError("The model changed the deterministic risk score.")

    evidence_by_chunk_id = {hit.chunk_id: hit for hit in evidence}

    for citation in analysis.citations:
        hit = evidence_by_chunk_id.get(citation.chunk_id)
        if hit is None:
            raise GroundingError(f"Unknown citation: {citation.chunk_id}")

        # Real policy text often spans multiple lines, but a citation
        # quote is naturally written as one line - normalize whitespace
        # (and case) on both sides before comparing, or an accurate
        # citation would be falsely rejected over formatting alone.
        normalized_quote = " ".join(citation.quote.split()).lower()
        if not normalized_quote:
            # An empty string is a substring of everything in Python, so
            # without this check a whitespace-only quote (e.g. a single
            # space) would pass the check below against any real chunk_id.
            raise GroundingError(f"Citation quote is empty: {citation.chunk_id}")
        normalized_source = " ".join(hit.text.split()).lower()
        if normalized_quote not in normalized_source:
            raise GroundingError(
                f"Citation quote is not present in source {citation.chunk_id}."
            )

    return analysis
