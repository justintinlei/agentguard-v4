"""Run every gate that must pass before AgentGuard v3 ships, in one command.

One script, one answer. It runs, in order:

  1. scripts/validate_starter_kit.py - the course scaffolding is intact
  2. python -m pytest -q            - every v1, v2, and v3 unit test
  3. evals/run_v2_evals.py          - v2's evaluation matrix (forced mock mode)
  4. evals/run_v3_evals.py          - v3's security evaluation suite
  5. scripts/check_no_secrets.py    - no key-shaped strings in any text file

Fail-fast: the first step to exit non-zero stops the run with that step's
exit code. There is no partial pass - the final line only prints if every
step succeeded.
"""

from __future__ import annotations

import subprocess

COMMANDS = [
    "python scripts/validate_starter_kit.py",
    "python -m pytest -q",
    "python evals/run_v2_evals.py",
    "python evals/run_v3_evals.py",
    "python scripts/check_no_secrets.py",
]

PASS_MESSAGE = "RELEASE GATE PASS for AgentGuard v3"


def main() -> None:
    for command in COMMANDS:
        print(f"\n>>> {command}", flush=True)
        result = subprocess.run(command, shell=True)
        if result.returncode:
            raise SystemExit(result.returncode)
    print(f"\n{PASS_MESSAGE}")


if __name__ == "__main__":
    main()
