"""Builds the prompt sent to AgentGuard v2's AI explanation layer.

Two parts, two different jobs: SYSTEM_INSTRUCTION is fixed and identical
on every request - it sets the model's hard limits. build_user_prompt()
is assembled fresh each time from the deterministic scan result and the
retrieved policy evidence - nothing else ever goes into it.
"""

from __future__ import annotations

import json

from retrieval import RetrievalHit
from scanner import ScanResult

SYSTEM_INSTRUCTION = """You are AgentGuard's security explanation assistant.

AgentGuard's deterministic scanner has already decided the agent's risk
level, score, and findings. That decision is final and not yours to make.
Your only job is to explain it using the approved policy evidence you are
given below - never invent a policy, never change the score, severity, or
findings.

Every claim you make must be backed by a citation to one of the supplied
evidence chunk IDs, quoting the exact text you are citing. If the supplied
evidence does not actually support a good explanation, say so plainly
instead of guessing or inventing a citation."""


def _scan_result_to_dict(scan_result: ScanResult) -> dict:
    """Turn a ScanResult into a plain dict the prompt can serialize as JSON."""
    return {
        "agent_name": scan_result.agent.agent_name,
        "risk_level": scan_result.risk_level,
        "score": scan_result.score,
        "findings": [
            {
                "rule_id": finding.rule_id,
                "severity": finding.severity,
                "title": finding.title,
                "explanation": finding.explanation,
                "recommendation": finding.recommendation,
            }
            for finding in scan_result.findings
        ],
    }


def build_user_prompt(scan_result: ScanResult, evidence: list[RetrievalHit]) -> str:
    """Assemble the user prompt from the deterministic result and evidence.

    Both sections are serialized as JSON straight from the real objects
    this codebase already trusts - nothing is summarized or re-worded on
    the way in, and nothing beyond these two things is ever included.
    """
    result_payload = _scan_result_to_dict(scan_result)
    evidence_payload = [hit.to_dict() for hit in evidence]
    return (
        "DETERMINISTIC_RESULT\n"
        + json.dumps(result_payload, indent=2)
        + "\n\nAPPROVED_POLICY_EVIDENCE\n"
        + json.dumps(evidence_payload, indent=2)
        + "\n\nReturn a concise grounded explanation in the required JSON structure."
    )
