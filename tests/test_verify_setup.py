"""Tests for the environment-variable helpers in scripts/verify_setup.py.

Uses pytest's monkeypatch fixture to set/unset environment variables for
each test, so nothing here depends on a real .env file or a real key.
"""

from scripts.verify_setup import check_mcp_server_importable, get_mode, has_api_key


def test_mode_defaults_to_mock_when_unset(monkeypatch):
    monkeypatch.delenv("AGENTGUARD_MODE", raising=False)
    assert get_mode() == "mock"


def test_mode_reads_explicit_value(monkeypatch):
    monkeypatch.setenv("AGENTGUARD_MODE", "live")
    assert get_mode() == "live"


def test_has_api_key_true_when_set(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-placeholder")
    assert has_api_key() is True


def test_has_api_key_false_when_unset(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert has_api_key() is False


def test_mcp_server_is_importable():
    assert check_mcp_server_importable() is True
