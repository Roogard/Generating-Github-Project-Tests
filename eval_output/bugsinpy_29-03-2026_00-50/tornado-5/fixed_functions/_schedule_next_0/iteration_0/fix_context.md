## Root Cause Diagnosis

Root Cause: The tests use `assert args[1] is pc._run` to check that the exact same bound method object is passed to `add_timeout`. In Python 3, bound methods are created fresh on each attribute access, so `pc._run` retrieved at call time and `pc._run` retrieved during the assertion are two different objects (even though they wrap the same function), causing the identity check `is` to fail. The function itself is logically correct — it passes `self._run` — but each access to `self._run` creates a new bound method object, so `args[1] is pc._run` is always `False`.

Suggestion 1: Use equality comparison instead of identity check in the tests
Change the assertion `assert args[1] is pc._run` to `assert args[1] == pc._run` in both `test_callback_is_run_method` and `test_mutation_wrong_callback_to_add_timeout`. Bound methods in Python 3 support `==` comparison (they compare equal if they wrap the same function and instance), so this will correctly verify the right method is passed without requiring identity.

Suggestion 2: Cache `pc._run` before the call and compare against the cached reference
In the test, store `expected_run = pc._run` before calling `pc._schedule_next()`, then assert `args[1] == expected_run` (or `args[1].__func__ is expected_run.__func__`). This avoids the stale-reference problem by capturing the bound method once and comparing against that single captured value, though equality (`==`) is still preferable over `is` for bound methods.

## Trigger Test(s)

```python
# test_blackbox.py
import pytest
import time
import asyncio
from unittest.mock import MagicMock, patch, call
from tornado.ioloop import PeriodicCallback

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_pc(callback=None, callback_time=1000):
    """Create a PeriodicCallback with a fake io_loop so we can inspect calls."""
    if callback is None:
        callback = lambda: None
    pc = PeriodicCallback(callback, callback_time)
    # Replace io_loop with a mock
    mock_loop = MagicMock()
    mock_loop.time.return_value = 1000.0
    mock_loop.add_timeout.return_value = object()  # sentinel timeout handle
    pc.io_loop = mock_loop
    return pc


# ---------------------------------------------------------------------------
# --- BVA ---
# ---------------------------------------------------------------------------

class TestBVA:
    """Boundary Value Analysis for _schedule_next."""

    def test_not_running_no_action(self):
        """When _running is False, _schedule_next must do nothing."""
        pc = make_pc()
        pc._running = False
        pc._schedule_next()
        pc.io_loop.time.assert_not_called()
        pc.io_loop.add_timeout.assert_not_called()

    def test_running_true_calls_update_next(self):
        """When _running is True, _update_next must be called with current time."""
        pc = make_pc()
        pc._running = True
        pc._next_timeout = 2000.0
        with patch.object(pc, '_update_next') as mock_update:
            pc._schedule_next()
            mock_update.assert_called_once_with(pc.io_loop.time.return_value)

    def test_running_true_calls_add_timeout(self):
        """When _running is True, add_timeout must be called with _next_timeout and _run."""
        pc = make_pc()
        pc._running = True
        pc._next_timeout = 2000.0
        with patch.object(pc, '_update_next'):
            pc._schedule_next()
            pc.io_loop.add_timeout.assert_called_once_with(pc._next_timeout, pc._run)

    def test_timeout_handle_stored(self):
        """The return value of add_timeout must be stored in _timeout."""
        pc = make_pc()
        pc._running = True
        pc._next_timeout = 2000.0
        sentinel = object()
        pc.io_loop.add_timeout.return_value = sentinel
        with patch.object(pc, '_update_next'):
            pc._schedule_next()
        assert pc._timeout is sentinel

    def test_io_loop_time_called_exactly_once(self):
        """io_loop.time() should be called exactly once per _schedule_next invocation."""
        pc = make_pc()
        pc._running = True
        pc._next_timeout = 2000.0
        with patch.object(pc, '_update_next'):
            pc._schedule_next()
        assert pc.io_loop.time.call_count == 1

    def test_running_false_timeout_not_overwritten(self):
        """When _running is False, existing _timeout must not be overwritten."""
        pc = make_pc()
        pc._running = False
        original_timeout = object()
        pc._timeout = original_timeout
        pc._schedule_next()
        assert pc._timeout is original_timeout

    def test_next_timeout_near_zero(self):
        """_schedule_next should work correctly with a _next_timeout near 0.0."""
        pc = make_pc(callback_time=1)
        pc._running = True
        pc._next_timeout = 0.001
        with patch.object(pc, '_update_next'):
            pc._schedule_next()
        pc.io_loop.add_timeout.assert_called_once_with(pc._next_timeout, pc._run)

    def test_next_timeout_large_value(self):
        """_schedule_next should correctly pass a very large _next_timeout to add_timeout."""
        pc = make_pc(callback_time=10**9)
        pc._running = True
        pc._next_timeout = 10**12
        with patch.object(pc, '_update_next'):
            pc._schedule_next()
        pc.io_loop.add_timeout.assert_called_once_with(pc._next_timeout, pc._run)


# ---------------------------------------------------------------------------
# --- ECP ---
# ---------------------------------------------------------------------------

class TestECP:
    """Equivalence Class Partitioning for _schedule_next."""

    # Valid class: _running=True, normal _next_timeout
    def test_valid_running_normal_timeout(self):
        """ECP: valid class — running with a reasonable future timeout."""
        pc = make_pc(callback_time=500)
        pc._running = True
        pc._next_timeout = 9999.0
        with patch.object(pc, '_update_next') as mock_update:
            pc._schedule_next()
        # _update_next receives the io_loop's current time
        mock_update.assert_called_once_with(1000.0)
        pc.io_loop.add_timeout.assert_called_once()

    # Invalid class: _running=False — nothing should happen
    def test_invalid_not_running(self):
        """ECP: invalid class — not running, entire body must be skipped."""
        pc = make_pc(callback_time=500)
        pc._running = False
        with patch.object(pc, '_update_next') as mock_update:
            pc._schedule_next()
        mock_update.assert_not_called()
        pc.io_loop.add_timeout.assert_not_called()

    # Class: _running=True, _next_timeout already in the past
    def test_valid_running_past_timeout(self):
        """ECP: valid class — _next_timeout is in the past; scheduling should still proceed."""
        pc = make_pc(callback_time=100)
        pc._running = True
        pc.io_loop.time.return_value = 5000.0
        pc._next_timeout = 1.0  # past value, _update_next would fix it
        with patch.object(pc, '_update_next'):
            pc._schedule_next()
        # add_timeout is still called (with whatever _next_timeout holds after _update_next)
        pc.io_loop.add_timeout.assert_called_once()

    # Class: _running transitions — start/stop/start cycle
    def test_valid_running_after_stop_restart(self):
        """ECP: _running toggled — second _schedule_next after restart should register timeout."""
        pc = make_pc()
        pc._running = False
        pc._schedule_next()
        pc.io_loop.add_timeout.assert_not_called()

        pc._running = True
        pc._next_timeout = 2000.0
        with patch.object(pc, '_update_next'):
            pc._schedule_next()
        pc.io_loop.add_timeout.assert_called_once()

    # Class: multiple sequential calls while running
    def test_valid_running_multiple_calls(self):
        """ECP: multiple _schedule_next calls while running must each register a new timeout."""
        pc = make_pc()
        pc._running = True
        pc._next_timeout = 2000.0
        with patch.object(pc, '_update_next'):
            pc._schedule_next()
            pc._schedule_next()
        assert pc.io_loop.add_timeout.call_count == 2

    # Class: _run callable is passed (not something else)
    def test_callback_is_run_method(self):
        """ECP: the second argument to add_timeout must always be pc._run, not pc._callback."""
        pc = make_pc()
        pc._running = True
        pc._next_timeout = 2000.0
        with patch.object(pc, '_update_next'):
            pc._schedule_next()
        args, _ = pc.io_loop.add_timeout.call_args
        assert args[1] is pc._run

    # Class: time argument to _update_next comes from io_loop.time(), not a constant
    def test_time_from_io_loop_not_constant(self):
        """ECP: _update_next must receive the dynamic io_loop.time() value."""
        pc = make_pc()
        pc._running = True
        pc._next_timeout = 2000.0
        pc.io_loop.time.return_value = 42.5
        with patch.object(pc, '_update_next') as mock_update:
            pc._schedule_next()
        mock_update.assert_called_once_with(42.5)


# ---------------------------------------------------------------------------
# --- Mutation Detection ---
# ---------------------------------------------------------------------------

class TestMutationDetection:
    """Mutation-style fault detection for _schedule_next."""

    def test_mutation_negated_running_check(self):
        """Detects: `if not self._running` instead of `if self._running`.
        When _running=True, add_timeout MUST be called."""
        pc = make_pc()
        pc._running = True
        pc._next_timeout = 2000.0
        with patch.object(pc, '_update_next'):
            pc._schedule_next()
        assert pc.io_loop.add_timeout.called, (
            "A correct _schedule_next should call add_timeout when _running is True"
        )

    def test_mutation_negated_running_false_no_call(self):
        """Detects: `if not self._running` — when _running=False, add_timeout must NOT be called."""
        pc = make_pc()
        pc._running = False
        pc._schedule_next()
        assert not pc.io_loop.add_timeout.called, (
            "A correct _schedule_next must skip add_timeout when _running is False"
        )

    def test_mutation_wrong_time_arg_to_update_next(self):
        """Detects: passing a constant (e.g., 0) instead of io_loop.time() to _update_next."""
        pc = make_pc()
        pc._running = True
        pc._next_timeout = 2000.0
        pc.io_loop.time.return_value = 9876.54
        with patch.object(pc, '_update_next') as mock_update:
            pc._schedule_next()
        actual_time_arg = mock_update.call_args[0][0]
        assert actual_time_arg == 9876.54, (
            "A correct _schedule_next must pass io_loop.time() to _update_next, not a constant"
        )

    def test_mutation_wrong_callback_to_add_timeout(self):
        """Detects: passing self._callback instead of self._run to add_timeout."""
        pc = make_pc()
        pc._running = True
        pc._next_timeout = 2000.0
        with patch.object(pc, '_update_next'):
            pc._schedule_next()
        _, args, _ = pc.io_loop.add_timeout.mock_calls[0]
        assert args[1] is pc._run, (
            "A correct _schedule_next must pass self._run (not self._callback) to add_timeout"
        )

    def test_mutation_timeout_arg_is_next_timeout_not_current_time(self):
        """Detects: passing io_loop.time() instead of self._next_timeout as first arg to add_timeout."""
        pc = make_pc()
        pc._running = True
        sentinel_next = 77777.0
        pc._next_timeout = sentinel_next
        pc.io_loop.time.return_value = 1000.0
        with patch.object(pc, '_update_next'):
            pc._schedule_next()
        positional_args = pc.io_loop.add_timeout.call_args[0]
        assert positional_args[0] == sentinel_next, (
            "A correct _schedule_next must pass self._next_timeout (not io_loop.time()) to add_timeout"
        )

    def test_mutation_timeout_result_not_stored(self):
        """Detects: missing assignment `self._timeout = ...` after add_timeout."""
        pc = make_pc()
        pc._running = True
        pc._next_timeout = 2000.0
        expected_handle = object()
        pc.io_loop.add_timeout.return_value = expected_handle
        with patch.object(pc, '_update_next'):
            pc._schedule_next()
        assert pc._timeout is expected_handle, (
            "A correct _schedule_next must store the add_timeout return value in self._timeout"
        )

    def test_mutation_update_next_called_before_add_timeout(self):
        """Detects: reversed call order — _update_next must be called before add_timeout
        so that _next_timeout is refreshed before it is passed to add_timeout."""
        call_order = []
        pc = make_pc()
        pc._running = True
        pc._next_timeout = 2000.0

        original_update = pc._update_next

        def record_update(t):
            call_order.append('update_next')
        pc._update_next = record_update

        original_add_timeout = pc.io_loop.add_timeout
        def record_add_timeout(*args, **kwargs):
            call_order.append('add_timeout')
            return original_add_timeout(*args, **kwargs)
        pc.io_loop.add_timeout.side_effect = record_add_timeout

        pc._schedule_next()

        assert call_order == ['update_next', 'add_timeout'], (
            "A correct _schedule_next must call _update_next before add_timeout"
        )

    def test_mutation_running_check_uses_wrong_variable(self):
        """Detects: checking self._stopped or some other flag instead of self._running."""
        pc = make_pc()
        # _running is True; any other flag the mutation might check is False by default
        pc._running = True
        if hasattr(pc, '_stopped'):
            pc._stopped = False
        pc._next_timeout = 2000.0
        with patch.object(pc, '_update_next'):
            pc._schedule_next()
        assert pc.io_loop.add_timeout.called, (
            "A correct _schedule_next must gate on self._running, not any other flag"
        )

    def test_mutation_omitting_update_next_call(self):
        """Detects: dropping the _update_next call entirely — next_timeout would not refresh."""
        pc = make_pc()
        pc._running = True
        pc._next_timeout = 2000.0
        update_called = []

        def fake_update(t):
            update_called.append(t)
        pc._update_next = fake_update

        pc._schedule_next()

        assert len(update_called) == 1, (
            "A correct _schedule_next must call _update_next exactly once"
        )
```
