"""Tests for scripts/run_release_gate.py - the one-command v4 release gate.

Importing the module is side-effect free: the checks only run under the
`if __name__ == "__main__"` guard. These tests pin *what* the gate runs,
so a future edit can't quietly drop the v3 or v4 security suites from it.
"""

from pathlib import Path

from scripts.run_release_gate import COMMANDS, PASS_MESSAGE

ROOT = Path(__file__).resolve().parent.parent


def test_gate_runs_every_required_check():
    joined = " ".join(COMMANDS)
    assert "scripts/validate_starter_kit.py" in joined   # course scaffolding
    assert "pytest -q" in joined                          # v1 + v2 + v3 unit tests
    assert "evals/run_v2_evals.py" in joined              # v2 evaluation matrix
    assert "evals/run_v3_evals.py" in joined              # v3 security suite
    assert "evals/run_v4_evals.py" in joined              # v4 failure-injection eval
    assert "scripts/check_no_secrets.py" in joined        # secret scan


def test_v3_eval_runs_after_the_full_test_suite():
    # No point grading v3 threats on top of a baseline that is already broken.
    assert COMMANDS.index("python -m pytest -q") < COMMANDS.index(
        "python evals/run_v3_evals.py"
    )


def test_v4_eval_runs_after_the_full_test_suite():
    # Same reason as v3: no point grading v4 failure-injection on top of a
    # baseline whose unit tests are already broken.
    assert COMMANDS.index("python -m pytest -q") < COMMANDS.index(
        "python evals/run_v4_evals.py"
    )


def test_pass_message_names_v4():
    assert PASS_MESSAGE == "RELEASE GATE PASS for AgentGuard v4"


def test_every_script_the_gate_calls_exists():
    for command in COMMANDS:
        for token in command.split():
            if token.endswith(".py"):
                assert (ROOT / token).is_file(), token
