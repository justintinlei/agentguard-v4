"""Checks that the local AgentGuard v3 development environment is ready.

This script checks local setup (Python version, virtual environment,
required project files, pytest installed) and reports two things about
`.env`: what AGENTGUARD_MODE is set to (defaulting to "mock" if unset),
and whether an API key is present. It never reads the key's actual value
into anything printed or logged here — only a True/False presence check.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "README.md",
    "CLAUDE.md",
    "requirements.txt",
    "scanner.py",
]


def check_python_version() -> bool:
    version = sys.version.split()[0]
    print(f"Python version: {version}")
    return sys.version_info >= (3, 9)


def check_virtual_environment_active() -> bool:
    is_active = sys.prefix != sys.base_prefix
    print(f"Virtual environment active: {is_active}")
    return is_active


def check_required_files_present() -> bool:
    missing = [name for name in REQUIRED_FILES if not (PROJECT_ROOT / name).exists()]
    if missing:
        print(f"Required files: FAIL, missing={missing}")
        return False
    print("Required files: PASS")
    return True


def check_pytest_installed() -> bool:
    is_installed = importlib.util.find_spec("pytest") is not None
    print(f"pytest installed: {is_installed}")
    return is_installed


def check_mcp_server_importable() -> bool:
    """True if `from mcp.server import MCPServer` succeeds.

    A real import catches problems find_spec would miss, such as an
    installed-but-broken package - the point of checking this now,
    rather than only discovering it later inside actual server code.
    """
    try:
        from mcp.server import MCPServer  # noqa: F401

        is_importable = True
    except ImportError:
        is_importable = False
    print(f"MCP server importable: {is_importable}")
    return is_importable


def get_mode() -> str:
    """Returns AGENTGUARD_MODE from the environment, defaulting to "mock"."""
    return os.getenv("AGENTGUARD_MODE", "mock")


def has_api_key() -> bool:
    """True if an API key is present in the environment.

    Never returns or exposes the key's value — only whether one is set.
    """
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def main() -> None:
    print("AgentGuard v3 setup verifier")
    print(f"Project root: {PROJECT_ROOT}")

    load_dotenv()

    checks = [
        check_python_version(),
        check_virtual_environment_active(),
        check_required_files_present(),
        check_pytest_installed(),
        check_mcp_server_importable(),
    ]

    print(f"AGENTGUARD_MODE: {get_mode()}")
    print(f"ANTHROPIC_API_KEY present: {has_api_key()}")

    if not all(checks):
        raise SystemExit("SETUP CHECK FAILED - see the results above")

    print("SETUP CHECK PASS")


if __name__ == "__main__":
    main()
