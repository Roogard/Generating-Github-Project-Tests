"""Pin the canonical text helpers consolidated from harness.py / agentic.py / base.py."""
from src.text_utils import strip_code_fence, truncate


def test_strip_code_fence_python():
    text = "```python\nimport pytest\ndef test_x(): pass\n```"
    out = strip_code_fence(text)
    assert "import pytest" in out
    assert "```" not in out


def test_strip_code_fence_bare():
    text = "```\nfoo()\n```"
    out = strip_code_fence(text)
    assert out.strip() == "foo()"


def test_strip_code_fence_no_fence_returns_input_unchanged():
    text = "no fence here"
    assert strip_code_fence(text) == text


def test_truncate_under_cap():
    assert truncate("short", 100) == "short"


def test_truncate_over_cap_appends_marker():
    out = truncate("a" * 500, 100)
    assert out.endswith("...[truncated]")
    assert len(out) == 100 + len("...[truncated]")


def test_truncate_strips_whitespace():
    assert truncate("  hello  ", 100) == "hello"


def test_truncate_handles_none():
    assert truncate(None, 100) == ""  # type: ignore[arg-type]
