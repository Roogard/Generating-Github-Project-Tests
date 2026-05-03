"""Pytest-result → Feedback gating.

These tests pin the most important behavioural rule in the harness: pytest
assertion failures are NOT improve signals — they may be the F→P bug
detection we want. Only collection / setup / timeout problems trigger Improve.
"""
from src.harness import build_feedback


def test_assertion_only_failures_done():
    fb = build_feedback({
        "passed": [],
        "failed": ["test_a"],
        "errors": [],
        "failure_details": [{"nodeid": "test_a", "longrepr": "AssertionError: x != y"}],
    })
    assert fb.next_action == "done"
    assert fb.has_infrastructure_problems is False
    assert len(fb.failures) == 1
    assert fb.failures[0]["name"] == "test_a"


def test_collection_error_triggers_improve():
    fb = build_feedback({
        "passed": [], "failed": [],
        "errors": ["__collection_error__"],
        "error_details": [{"nodeid": "__collection_error__",
                           "longrepr": "ImportError: no module named widget"}],
    })
    assert fb.next_action == "improve"
    assert fb.has_infrastructure_problems is True
    assert len(fb.collection_problems) == 1
    assert fb.collection_problems[0]["kind"] == "collection_error"


def test_real_error_triggers_improve():
    fb = build_feedback({
        "passed": [], "failed": [],
        "errors": ["test_setup"],
        "error_details": [{"nodeid": "test_setup",
                           "longrepr": "AttributeError: ..."}],
    })
    assert fb.next_action == "improve"
    assert fb.has_infrastructure_problems is True
    assert len(fb.errors) == 1


def test_timeout_is_infrastructure_problem():
    fb = build_feedback({
        "passed": [], "failed": ["test_b"],
        "errors": [], "timed_out": ["x.py::test_b"],
        "failure_details": [{"nodeid": "test_b", "longrepr": "Timeout"}],
    })
    assert fb.has_infrastructure_problems is True
    assert "test_b" in fb.timeouts


def test_no_tests_collected_is_collection_problem():
    """pytest collects zero tests — also an improve signal."""
    fb = build_feedback({"passed": [], "failed": [], "errors": []})
    assert fb.next_action == "improve"
    assert any(cp["kind"] == "no_tests_collected" for cp in fb.collection_problems)
