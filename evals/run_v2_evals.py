"""Run AgentGuard v2's full regression and evaluation matrix.

Two different proofs, combined into one gate: regression (python -m
pytest -q - did v1's scanner and every v2 unit/integration test stay
correct) and the evaluation matrix (each case in v2_cases.json - is the
mock explainer's output still the right risk level, with citations where
expected). Regression runs first and fails fast, since there's no point
grading AI output quality on top of code that's already broken.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from audit_log import log_analysis_event
from scanner import Agent
from v2_service import analyze_agent

CASES_PATH = PROJECT_ROOT / "evals" / "v2_cases.json"
ENVIRONMENT_PATH = PROJECT_ROOT / "sample_environment_before.json"
AUDIT_LOG_PATH = PROJECT_ROOT / "audit_events.jsonl"


def run_case(case: dict, agents: list[dict]) -> bool:
    agent = Agent(**agents[case["agent_index"]])
    analysis, usage = analyze_agent(agent, mode="mock")
    log_analysis_event(AUDIT_LOG_PATH, analysis, usage)

    level_ok = analysis.deterministic_risk_level == case["expected_level"]
    has_citation = bool(analysis.citations)
    cite_ok = has_citation if case["must_cite"] else True
    passed = level_ok and cite_ok

    status = "PASS" if passed else "FAIL"
    print(f"{case['case_id']}: {status} level={analysis.deterministic_risk_level} citations={has_citation}")
    return passed


def main() -> None:
    print(">>> python -m pytest -q", flush=True)
    result = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=PROJECT_ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)

    cases = json.loads(CASES_PATH.read_text())
    agents = json.loads(ENVIRONMENT_PATH.read_text())

    failures = [case["case_id"] for case in cases if not run_case(case, agents)]

    if failures:
        raise SystemExit(f"V2 evaluation failures: {failures}")

    print(f"V2 EVALUATION PASS: {len(cases)} of {len(cases)} cases passed")
    print("FULL REGRESSION AND EVALUATION MATRIX PASS")


if __name__ == "__main__":
    main()
