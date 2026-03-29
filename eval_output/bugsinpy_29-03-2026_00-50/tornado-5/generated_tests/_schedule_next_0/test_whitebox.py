import time
import threading
from unittest.mock import MagicMock, patch, call
import pytest

from tornado.ioloop import PeriodicCallback

# ---------------------------------------------------------------------------
# Helpers – build a PeriodicCallback with fully mocked internals so we never
# touch a real IOLoop.
# ---------------------------------------------------------------------------

def _make_pc(running: bool, callback_time_ms: float = 1000.0):
    """Return a PeriodicCallback whose IOLoop is fully mocked."""
    cb = PeriodicCallback.__new__(PeriodicCallback)

    # Minimal attributes that PeriodicCallback.__init__ would normally set
    cb._running = running
    cb.callback_time = callback_time_ms
    cb._next_timeout = 0.0
    cb._timeout = None

    # Mocked io_loop
    mock_io_loop = MagicMock()
    mock_io_loop.time.return_value = 1000.0        # current time
    mock_io_loop.add_timeout.return_value = object()  # sentinel timeout handle
    cb.io_loop = mock_io_loop

    # Mocked _update_next and _run so we only test _schedule_next's own logic
    cb._update_next = MagicMock()
    cb._run = MagicMock()

    return cb


# ===========================================================================
# --- Statement Coverage ---
# Every executable statement inside _schedule_next must run at least once.
# ===========================================================================

def test_sc_running_true_calls_update_next():
    """
    When _running is True the body executes:
    _update_next and add_timeout are both called.
    """
    # path: _running=True → body executes
    pc = _make_pc(running=True)
    pc._schedule_next()

    pc._update_next.assert_called_once()
    pc.io_loop.add_timeout.assert_called_once()


def test_sc_running_false_no_statements_executed():
    """
    When _running is False the if-body is skipped entirely;
    no internal calls are made.
    # path: _running=False → guard fails → return (implicit)
    """
    pc = _make_pc(running=False)
    pc._schedule_next()

    pc._update_next.assert_not_called()
    pc.io_loop.add_timeout.assert_not_called()
    pc.io_loop.time.assert_not_called()


# ===========================================================================
# --- Block Coverage ---
# Two basic blocks exist:
#   Block A: function entry / guard evaluation
#   Block B: the if-body (update_next + add_timeout + assignment)
# ===========================================================================

def test_bc_block_B_entered_when_running():
    """Block B (if-body) is entered; _timeout is assigned the handle returned
    by add_timeout. # block: A → B"""
    sentinel = object()
    pc = _make_pc(running=True)
    pc.io_loop.add_timeout.return_value = sentinel

    pc._schedule_next()

    # The assignment `self._timeout = ...` must have been executed
    assert pc._timeout is sentinel


def test_bc_block_B_skipped_when_not_running():
    """Block B is NOT entered; _timeout stays at its initial value.
    # block: A only (guard False)"""
    pc = _make_pc(running=False)
    pc._timeout = None  # explicit initial value

    pc._schedule_next()

    assert pc._timeout is None  # unchanged


# ===========================================================================
# --- Condition Coverage ---
# The single boolean sub-expression is `self._running`.
# It must be True in at least one test and False in at least one test.
# ===========================================================================

def test_cc_running_is_true():
    """
    self._running evaluates to True.
    # self._running: True
    """
    pc = _make_pc(running=True)
    pc._schedule_next()
    # A correct implementation must proceed to schedule work
    pc.io_loop.add_timeout.assert_called_once()


def test_cc_running_is_false():
    """
    self._running evaluates to False.
    # self._running: False
    """
    pc = _make_pc(running=False)
    pc._schedule_next()
    # A correct implementation must NOT schedule anything
    pc.io_loop.add_timeout.assert_not_called()


# ===========================================================================
# --- Path Coverage ---
# There are exactly two paths through this one-branch function:
#   Path 1: entry → guard True  → _update_next → add_timeout → assign → exit
#   Path 2: entry → guard False → exit
# ===========================================================================

def test_path1_running_true_full_body():
    """
    Path 1: _running=True → _update_next called with current time →
            add_timeout called with (_next_timeout, _run) → _timeout assigned.
    # path: if-true → full body → return
    """
    pc = _make_pc(running=True)
    fake_now = 1234.5
    pc.io_loop.time.return_value = fake_now
    fake_handle = object()
    pc.io_loop.add_timeout.return_value = fake_handle

    pc._schedule_next()

    # _update_next receives the current IOLoop time
    pc._update_next.assert_called_once_with(fake_now)

    # add_timeout receives the (possibly updated) _next_timeout and _run
    pc.io_loop.add_timeout.assert_called_once_with(pc._next_timeout, pc._run)

    # _timeout is set to the handle
    assert pc._timeout is fake_handle


def test_path2_running_false_early_exit():
    """
    Path 2: _running=False → guard fails → return immediately.
    No side effects at all.
    # path: if-false → immediate return
    """
    pc = _make_pc(running=False)
    original_timeout = pc._timeout  # should remain unchanged

    pc._schedule_next()

    pc._update_next.assert_not_called()
    pc.io_loop.time.assert_not_called()
    pc.io_loop.add_timeout.assert_not_called()
    assert pc._timeout is original_timeout


def test_path1_add_timeout_args_order():
    """
    Property: add_timeout must be called with positional args
    (_next_timeout, _run) in that exact order — the timeout fires _run.
    # path: if-true → verify argument ordering
    """
    pc = _make_pc(running=True)

    pc._schedule_next()

    args, kwargs = pc.io_loop.add_timeout.call_args
    # First positional arg is the timeout deadline, second is the callable
    assert args[0] is pc._next_timeout or args[0] == pc._next_timeout
    assert args[1] is pc._run


def test_path1_update_next_called_before_add_timeout():
    """
    Property: _update_next must be called BEFORE add_timeout so that
    _next_timeout is current when add_timeout is called.
    # path: if-true → ordering invariant
    """
    call_order = []

    pc = _make_pc(running=True)
    pc._update_next = MagicMock(side_effect=lambda t: call_order.append("update_next"))
    pc.io_loop.add_timeout = MagicMock(side_effect=lambda *a, **k: call_order.append("add_timeout"))

    pc._schedule_next()

    assert call_order == ["update_next", "add_timeout"]


def test_path1_truthy_running_value():
    """
    Path 1 variant: _running is a truthy non-boolean (e.g. 1).
    A correct implementation treats any truthy value as 'running'.
    # path: if-true (via truthy int) → full body
    """
    pc = _make_pc(running=True)
    pc._running = 1  # truthy int, not strict True

    pc._schedule_next()

    pc.io_loop.add_timeout.assert_called_once()


def test_path2_falsy_running_value():
    """
    Path 2 variant: _running is a falsy non-boolean (e.g. 0).
    # path: if-false (via falsy int) → immediate return
    """
    pc = _make_pc(running=False)
    pc._running = 0  # falsy int

    pc._schedule_next()

    pc.io_loop.add_timeout.assert_not_called()