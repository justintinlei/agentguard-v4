"""Tests for .github/workflows/tests.yml.

No pyyaml in requirements.txt, so these check the raw file text (the
same approach tests/test_app_v3.py uses for app source). The point is to
keep CI enforcing every gate: the full pytest suite, v2's evaluation
matrix, v3's security evaluation suite, and (Day 9 Lab 8) v4's
failure-injection eval + the secret scan, on the project's Python. A
future edit that drops any of them fails here.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "tests.yml"
WORKFLOW_TEXT = WORKFLOW.read_text(encoding="utf-8")


def test_workflow_file_exists_and_looks_like_a_workflow():
    assert WORKFLOW_TEXT.strip()
    assert WORKFLOW_TEXT.lstrip().startswith("name:")
    for key in ("on:", "jobs:", "steps:"):
        assert key in WORKFLOW_TEXT


def test_ci_installs_the_pinned_requirements():
    assert "pip install -r requirements.txt" in WORKFLOW_TEXT


def test_ci_runs_the_full_pytest_suite():
    assert "pytest -q" in WORKFLOW_TEXT


def test_ci_runs_the_v2_evaluation_gate():
    assert "python evals/run_v2_evals.py" in WORKFLOW_TEXT


def test_ci_runs_the_v3_security_evaluation_gate():
    # The assertion this lab exists to protect.
    assert "python evals/run_v3_evals.py" in WORKFLOW_TEXT


def test_ci_runs_the_v4_failure_injection_eval():
    # Day 9 Lab 8: every push now challenges the v4 action boundary - a
    # change that lets a refused operation through fails this eval in CI.
    assert "python evals/run_v4_evals.py" in WORKFLOW_TEXT


def test_ci_runs_the_secret_scan():
    # Day 9 Lab 8: the release-gate secret scan also runs in CI (it now
    # covers the Dockerfile / .dockerignore too).
    assert "python scripts/check_no_secrets.py" in WORKFLOW_TEXT


def test_ci_python_matches_the_project():
    # CI, the local venv, and the python:3.14-slim container must agree.
    assert '"3.14"' in WORKFLOW_TEXT
    assert "3.12" not in WORKFLOW_TEXT


def test_every_eval_script_named_by_ci_exists():
    for script in (
        "evals/run_v2_evals.py",
        "evals/run_v3_evals.py",
        "evals/run_v4_evals.py",
    ):
        assert f"python {script}" in WORKFLOW_TEXT
        assert (ROOT / script).is_file()
