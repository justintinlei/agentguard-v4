"""Deterministic stand-in for a real Claude call.

Reads real scan data and real retrieved evidence and assembles a real,
schema-validated GroundedAnalysis with plain string templates - no
network call, no API key, no cost, and no run-to-run variation. This is
what lets the rest of the pipeline be built and tested for free.
"""

from __future__ import annotations

from analysis_schema import Citation, GroundedAnalysis
from retrieval import RetrievalHit
from scanner import ScanResult


def _short_quote(text: str, limit: int = 180) -> str:
    """Collapse whitespace and truncate to fit Citation.quote's length limit."""
    single_line = " ".join(text.split())
    return single_line[:limit].rstrip()


def analyze_with_mock(scan_result: ScanResult, evidence: list[RetrievalHit]) -> GroundedAnalysis:
    """Build a GroundedAnalysis from real scan data and evidence, locally.

    Raises ValueError if evidence is empty - refuses to produce an
    explanation with nothing real to cite, the same standard a real,
    well-behaved analyst should be held to.
    """
    if not evidence:
        raise ValueError("At least one evidence chunk is required to build an analysis.")

    finding_titles = [finding.title for finding in scan_result.findings]
    if finding_titles:
        summary = (
            f"{scan_result.agent.agent_name} is {scan_result.risk_level} risk "
            f"with score {scan_result.score} because the deterministic scanner "
            "found: " + "; ".join(finding_titles) + "."
        )
    else:
        summary = (
            f"{scan_result.agent.agent_name} has no risk found under the "
            "current deterministic rules."
        )

    citations = [
        Citation(chunk_id=hit.chunk_id, quote=_short_quote(hit.text))
        for hit in evidence[:2]
    ]

    return GroundedAnalysis(
        agent_name=scan_result.agent.agent_name,
        deterministic_risk_level=scan_result.risk_level,
        deterministic_risk_score=scan_result.score,
        summary=summary,
        why_it_matters=(
            "Agents combine an identity, a set of tools, and data access. An "
            "unsafe combination of these can turn a routine workflow into an "
            "unreviewed, high-impact action."
        ),
        recommended_next_step=(
            "Apply the deterministic recommendation for each finding, keep the "
            "agent's tool list as small as possible, and re-scan before "
            "enabling autonomous operation."
        ),
        citations=citations,
    )
