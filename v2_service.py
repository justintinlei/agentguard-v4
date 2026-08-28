"""Orchestrates the full AgentGuard v2 pipeline: deterministic scan,
policy retrieval, an AI explanation (mock or live), and grounding
validation - the one function a real caller (later, the UI) uses.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from dotenv import load_dotenv

from analysis_schema import GroundedAnalysis
from claude_analyst import UsageRecord, analyze_with_claude
from grounding import validate_grounding
from mock_analyst import analyze_with_mock
from policy_library import load_policy_chunks
from retrieval import build_retrieval_query, retrieve
from scanner import Agent, ScanResult, evaluate_agent

BASE_DIR = Path(__file__).resolve().parent
POLICIES_DIR = BASE_DIR / "policies"


def analyze_agent(agent: Agent, mode: str | None = None) -> tuple[GroundedAnalysis, UsageRecord]:
    """Run the full pipeline for one agent: scan, retrieve, explain, validate.

    mode picks the analyst: "mock" (free, deterministic) or "live" (real,
    billed Claude API call). Defaults to AGENTGUARD_MODE from the
    environment, which itself defaults to "mock" - the safe choice.
    The result is always passed through validate_grounding before being
    returned, in either mode, so nothing ungrounded is ever handed back.
    """
    # v2_service is the one real entry point everything else calls
    # through, so it's the natural single place to load .env - safe to
    # call every time: it never overwrites a variable already set.
    load_dotenv()

    scan_result: ScanResult = evaluate_agent(agent)
    chunks = load_policy_chunks(POLICIES_DIR)
    query = build_retrieval_query(scan_result)
    evidence = retrieve(query, chunks, top_k=3)

    if not evidence:
        raise RuntimeError("No relevant policy evidence was retrieved.")

    selected_mode = (mode or os.getenv("AGENTGUARD_MODE", "mock")).lower()

    if selected_mode == "live":
        analysis, usage = analyze_with_claude(scan_result, evidence)
    elif selected_mode == "mock":
        start = time.perf_counter()
        analysis = analyze_with_mock(scan_result, evidence)
        latency_ms = int((time.perf_counter() - start) * 1000)
        usage = UsageRecord(
            mode="mock",
            model="mock",
            input_tokens=0,
            output_tokens=0,
            latency_ms=latency_ms,
            estimated_cost_usd=0.0,
        )
    else:
        raise ValueError(f"Unknown mode: {selected_mode!r}. Use 'mock' or 'live'.")

    validate_grounding(analysis, scan_result, evidence)
    return analysis, usage
