"""Pins step 6 of the simplification pass: typo'd provider names should
fail loudly with a list of valid providers, not silently fall back to a
default that costs the user real money on the wrong vendor."""
import pytest

from src.llm import build_config


def test_unknown_provider_raises():
    with pytest.raises(ValueError, match="unknown provider"):
        build_config("anthopic")  # typo


def test_unknown_provider_lists_valid_options():
    """The error message tells the caller what they should have typed."""
    with pytest.raises(ValueError) as exc_info:
        build_config("not-a-real-provider")
    msg = str(exc_info.value)
    assert "anthropic" in msg
    assert "openai" in msg
    assert "deepseek" in msg


def test_known_provider_builds_config():
    cfg = build_config("anthropic", model="claude-haiku-4-5", api_key="test-key")
    assert cfg["provider"] == "anthropic"
    assert cfg["model"] == "claude-haiku-4-5"
    assert cfg["api_key"] == "test-key"
