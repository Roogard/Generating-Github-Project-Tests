_(showing 10 of 18 failures)_

## Trigger Test(s)

```python
# test_blackbox.py
import asyncio
import time
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from tornado.websocket import WebSocketProtocol13


# ---------------------------------------------------------------------------
# Helpers to build a minimal WebSocketProtocol13-like object without needing
# a live TCP connection.  We monkey-patch the instance so that periodic_ping
# can be called as a plain method.
# ---------------------------------------------------------------------------

def make_protocol(
    is_closing=False,
    last_ping_offset=0.0,
    last_pong_offset=0.0,
    ping_interval=30.0,
    ping_timeout=60.0,
    has_ping_callback=True,
):
    """Return a mock object that satisfies periodic_ping's interface."""
    obj = MagicMock(spec=WebSocketProtocol13)

    # Bind the real method to our mock object
    obj.periodic_ping = lambda: WebSocketProtocol13.periodic_ping(obj)

    now = 100.0  # arbitrary fixed "now"

    obj.is_closing.return_value = is_closing
    obj.ping_interval = ping_interval
    obj.ping_timeout = ping_timeout

    # last_ping / last_pong are set relative to 'now'
    obj.last_ping = now - last_ping_offset
    obj.last_pong = now - last_pong_offset

    if has_ping_callback:
        obj.ping_callback = MagicMock()
    else:
        obj.ping_callback = None

    # Patch IOLoop.current().time() to return a deterministic value
    ioloop_mock = MagicMock()
    ioloop_mock.time.return_value = now
    obj._ioloop_mock = ioloop_mock  # keep reference to prevent GC

    return obj, ioloop_mock


# ---------------------------------------------------------------------------
# Shared patcher so every test gets a deterministic IOLoop.current()
# ---------------------------------------------------------------------------

def run_periodic_ping(obj, ioloop_mock):
    with patch("tornado.websocket.IOLoop") as mock_ioloop_class:
        mock_ioloop_class.current.return_value = ioloop_mock
        WebSocketProtocol13.periodic_ping(obj)


# ===========================================================================
# --- BVA ---
# ===========================================================================

class TestBVA:
    """Boundary Value Analysis tests for periodic_ping."""

    # --- Boundary: since_last_ping exactly equals 2 * ping_interval ----------

    def test_bva_since_last_ping_exactly_2x_interval_no_timeout(self):
        """since_last_ping == 2*interval (boundary), pong not timed out → should ping."""
        obj, iol = make_protocol(
            last_ping_offset=60.0,   # since_last_ping = 60 == 2*30
            last_pong_offset=10.0,   # since_last_pong = 10 < ping_timeout=60
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        run_periodic_ping(obj, iol)
        # NOT closing scenario, condition not met → write_ping should be called
        obj.write_ping.assert_called_once_with(b"")

    def test_bva_since_last_ping_just_below_2x_interval_pong_timed_out(self):
        """since_last_ping < 2*interval AND since_last_pong > ping_timeout → close."""
        obj, iol = make_protocol(
            last_ping_offset=59.9,   # since_last_ping = 59.9 < 60 → TRUE
            last_pong_offset=61.0,   # since_last_pong = 61 > 60 → TRUE
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        run_periodic_ping(obj, iol)
        obj.close.assert_called_once()
        obj.write_ping.assert_not_called()

    def test_bva_since_last_pong_exactly_equals_ping_timeout_no_close(self):
        """since_last_pong == ping_timeout (not strictly greater) → should NOT close."""
        obj, iol = make_protocol(
            last_ping_offset=10.0,   # since_last_ping = 10 < 60 → TRUE
            last_pong_offset=60.0,   # since_last_pong = 60 == ping_timeout → NOT > → FALSE
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        run_periodic_ping(obj, iol)
        obj.close.assert_not_called()
        obj.write_ping.assert_called_once_with(b"")

    def test_bva_since_last_pong_one_unit_above_timeout_causes_close(self):
        """since_last_pong just above ping_timeout → close triggered."""
        obj, iol = make_protocol(
            last_ping_offset=10.0,
            last_pong_offset=60.001,  # strictly > 60
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        run_periodic_ping(obj, iol)
        obj.close.assert_called_once()

    def test_bva_since_last_ping_just_above_2x_interval_pong_timed_out_no_close(self):
        """since_last_ping >= 2*interval even though pong timed out → machine suspended, no close."""
        obj, iol = make_protocol(
            last_ping_offset=60.001,  # since_last_ping > 60 → first condition FALSE → short-circuit
            last_pong_offset=61.0,
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        run_periodic_ping(obj, iol)
        obj.close.assert_not_called()
        obj.write_ping.assert_called_once_with(b"")

    # --- Boundary: ping_timeout at zero ------------------------------------

    def test_bva_ping_timeout_zero_pong_any_positive_age(self):
        """ping_timeout=0 means any positive since_last_pong triggers close (if ping recent)."""
        obj, iol = make_protocol(
            last_ping_offset=5.0,    # recent ping
            last_pong_offset=0.001,  # slightly stale pong
            ping_interval=30.0,
            ping_timeout=0.0,
        )
        run_periodic_ping(obj, iol)
        obj.close.assert_called_once()

    # --- Boundary: ping_interval very large --------------------------------

    def test_bva_large_ping_interval_threshold_very_large(self):
        """With a huge interval the 2*interval threshold is huge → recent ping never triggers close."""
        obj, iol = make_protocol(
            last_ping_offset=1000.0,  # large but < 2*1e9
            last_pong_offset=5000.0,
            ping_interval=1e9,
            ping_timeout=60.0,
        )
        run_periodic_ping(obj, iol)
        # since_last_ping (1000) << 2*1e9 → TRUE; since_last_pong (5000) > 60 → TRUE → close
        obj.close.assert_called_once()


# ===========================================================================
# --- ECP ---
# ===========================================================================

class TestECP:
    """Equivalence Class Partitioning tests for periodic_ping."""

    # ECP Class 1: is_closing=True → stop callback and return immediately
    def test_ecp_closing_with_callback_stops_and_returns(self):
        obj, iol = make_protocol(is_closing=True, has_ping_callback=True)
        run_periodic_ping(obj, iol)
        obj.ping_callback.stop.assert_called_once()
        obj.write_ping.assert_not_called()
        obj.close.assert_not_called()

    # ECP Class 2: is_closing=True, ping_callback is None → return without stop
    def test_ecp_closing_without_callback_returns_immediately(self):
        obj, iol = make_protocol(is_closing=True, has_ping_callback=False)
        run_periodic_ping(obj, iol)
        obj.write_ping.assert_not_called()
        obj.close.assert_not_called()

    # ECP Class 3: not closing, timeout condition not met → normal ping
    def test_ecp_not_closing_no_timeout_sends_ping(self):
        obj, iol = make_protocol(
            is_closing=False,
            last_ping_offset=10.0,
            last_pong_offset=5.0,
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        run_periodic_ping(obj, iol)
        obj.write_ping.assert_called_once_with(b"")
        obj.close.assert_not_called()

    # ECP Class 4: not closing, both timeout conditions met → close
    def test_ecp_not_closing_timeout_conditions_met_closes(self):
        obj, iol = make_protocol(
            is_closing=False,
            last_ping_offset=10.0,   # recent ping
            last_pong_offset=120.0,  # pong very stale
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        run_periodic_ping(obj, iol)
        obj.close.assert_called_once()
        obj.write_ping.assert_not_called()

    # ECP Class 5: ping very old (since_last_ping >= 2*interval) even if pong stale → no close
    def test_ecp_old_ping_stale_pong_no_close_machine_suspend_guard(self):
        obj, iol = make_protocol(
            is_closing=False,
            last_ping_offset=200.0,  # > 2*30
            last_pong_offset=120.0,  # stale
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        run_periodic_ping(obj, iol)
        obj.close.assert_not_called()

    # ECP Class 6: normal ping updates last_ping to 'now'
    def test_ecp_last_ping_updated_after_successful_ping(self):
        obj, iol = make_protocol(
            is_closing=False,
            last_ping_offset=50.0,
            last_pong_offset=5.0,
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        now = iol.time.return_value
        run_periodic_ping(obj, iol)
        # A correct implementation must update last_ping to the current IOLoop time
        assert obj.last_ping == now

    # ECP Class 7: close path does NOT update last_ping
    def test_ecp_last_ping_not_updated_on_close_path(self):
        obj, iol = make_protocol(
            is_closing=False,
            last_ping_offset=10.0,
            last_pong_offset=120.0,
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        original_last_ping = obj.last_ping
        run_periodic_ping(obj, iol)
        obj.close.assert_called_once()
        # last_ping should not be updated when we close instead of pinging
        assert obj.last_ping == original_last_ping


# ===========================================================================
# --- Mutation Detection ---
# ===========================================================================

class TestMutationDetection:
    """Tests designed to catch common mutations in periodic_ping."""

    # Mutation: `<` → `<=` in `since_last_ping < 2 * self.ping_interval`
    # If mutated, equality case would NOT trigger close even when it should not;
    # more critically the off-by-one below catches the boundary flip.
    def test_mutation_lt_vs_lte_in_ping_age_check(self):
        """Detects < vs <= mutation: exactly at boundary should NOT close."""
        obj, iol = make_protocol(
            last_ping_offset=60.0,   # since_last_ping == 2*30 → NOT < 60 → condition FALSE
            last_pong_offset=120.0,
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        run_periodic_ping(obj, iol)
        # With correct `<`, since_last_ping == 60 is NOT less than 60 → no close
        obj.close.assert_not_called()

    # Mutation: `>` → `>=` in `since_last_pong > self.ping_timeout`
    def test_mutation_gt_vs_gte_in_pong_timeout_check(self):
        """Detects > vs >= mutation: at boundary pong==timeout should NOT close."""
        obj, iol = make_protocol(
            last_ping_offset=10.0,
            last_pong_offset=60.0,   # since_last_pong == ping_timeout → NOT > → no close
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        run_periodic_ping(obj, iol)
        # Correct `>`: equality does not trigger close
        obj.close.assert_not_called()
        obj.write_ping.assert_called_once_with(b"")

    # Mutation: `and` → `or` in the combined condition
    def test_mutation_and_vs_or_condition_both_false(self):
        """Detects `and` → `or`: when BOTH sub-conditions are False, no close must occur."""
        obj, iol = make_protocol(
            last_ping_offset=200.0,  # since_last_ping NOT < 2*30 → FALSE
            last_pong_offset=5.0,    # since_last_pong NOT > 60 → FALSE
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        run_periodic_ping(obj, iol)
        # With `and`: FALSE and FALSE → no close (correct)
        # With `or`: FALSE or FALSE → no close (same result here; see next test)
        obj.close.assert_not_called()

    def test_mutation_and_vs_or_first_true_second_false(self):
        """Detects `and` → `or`: first TRUE, second FALSE → `or` would wrongly close."""
        obj, iol = make_protocol(
            last_ping_offset=10.0,   # since_last_ping=10 < 60 → TRUE
            last_pong_offset=5.0,    # since_last_pong=5 NOT > 60 → FALSE
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        run_periodic_ping(obj, iol)
        # Correct `and`: TRUE and FALSE → no close
        # Mutated `or`: TRUE or FALSE → close (wrong)
        obj.close.assert_not_called()
        obj.write_ping.assert_called_once_with(b"")

    def test_mutation_and_vs_or_first_false_second_true(self):
        """Detects `and` → `or`: second TRUE, first FALSE → `or` would wrongly close."""
        obj, iol = make_protocol(
            last_ping_offset=200.0,  # since_last_ping=200 NOT < 60 → FALSE
            last_pong_offset=120.0,  # since_last_pong=120 > 60 → TRUE
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        run_periodic_ping(obj, iol)
        # Correct `and`: FALSE and TRUE → no close
        # Mutated `or`: FALSE or TRUE → close (wrong)
        obj.close.assert_not_called()

    # Mutation: wrong constant, `2 *` removed → `since_last_ping < ping_interval`
    def test_mutation_missing_factor_of_2_in_ping_interval(self):
        """Detects removal of the '2 *' multiplier."""
        obj, iol = make_protocol(
            last_ping_offset=45.0,   # 30 < 45 < 60; with 2x: 45 < 60 → TRUE; without 2x: 45 < 30 → FALSE
            last_pong_offset=120.0,  # pong stale
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        run_periodic_ping(obj, iol)
        # Correct: 2*30=60, 45 < 60 → TRUE AND pong stale → close
        obj.close.assert_called_once()

    # Mutation: `is_closing()` check negated → closes callback when NOT closing
    def test_mutation_negated_is_closing_check(self):
        """Detects negation of is_closing(): not-closing case must NOT stop callback."""
        obj, iol = make_protocol(
            is_closing=False,
            last_ping_offset=10.0,
            last_pong_offset=5.0,
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        run_periodic_ping(obj, iol)
        # Correct: is_closing() is False → skip the early-return block entirely
        if obj.ping_callback is not None:
            obj.ping_callback.stop.assert_not_called()

    # Mutation: `ping_callback is not None` → `ping_callback is None` (flipped None check)
    def test_mutation_flipped_none_check_on_ping_callback(self):
        """Detects flipped None check: when closing AND callback exists, callback.stop() must be called."""
        obj, iol = make_protocol(is_closing=True, has_ping_callback=True)
        run_periodic_ping(obj, iol)
        # Correct: callback is not None → stop it
        obj.ping_callback.stop.assert_called_once()

    # Mutation: write_ping called with wrong argument (e.g., None instead of b"")
    def test_mutation_write_ping_called_with_empty_bytes(self):
        """Detects wrong argument to write_ping: must be b'' not None or other."""
        obj, iol = make_protocol(
            is_closing=False,
            last_ping_offset=10.0,
            last_pong_offset=5.0,
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        run_periodic_ping(obj, iol)
        call_args = obj.write_ping.call_args
        assert call_args is not None, "write_ping must be called"
        assert call_args[0][0] == b"", "write_ping must be called with b''"

    # Mutation: last_ping assigned wrong variable (e.g., last_pong instead of now)
    def test_mutation_last_ping_updated_to_now_not_last_pong(self):
        """Detects wrong variable assignment: last_ping must equal current time, not last_pong."""
        obj, iol = make_protocol(
            is_closing=False,
            last_ping_offset=50.0,
            last_pong_offset=5.0,  # last_pong = 100 - 5 = 95
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        now = iol.time.return_value   # 100
        run_periodic_ping(obj, iol)
        # A correct implementation sets last_ping = now (100), not last_pong (95)
        assert obj.last_ping == now

    # Mutation: callback.stop() called even when ping_callback is None while closing
    def test_mutation_callback_none_no_stop_called(self):
        """When closing but ping_callback is None, stop() must not be attempted."""
        obj, iol = make_protocol(is_closing=True, has_ping_callback=False)
        # Should not raise AttributeError; correct code guards with `is not None`
        run_periodic_ping(obj, iol)
        obj.write_ping.assert_not_called()

    # Mutation: close() followed by continued execution (missing `return`)
    def test_mutation_return_after_close_no_write_ping(self):
        """Detects missing `return` after self.close(): write_ping must NOT be called after close."""
        obj, iol = make_protocol(
            is_closing=False,
            last_ping_offset=10.0,
            last_pong_offset=120.0,
            ping_interval=30.0,
            ping_timeout=60.0,
        )
        run_periodic_ping(obj, iol)
        obj.close.assert_called_once()
        obj.write_ping.assert_not_called()

    # Mutation: return after callback.stop() missing → continues to timeout logic
    def test_mutation_return_after_stop_callback_no_further_action(self):
        """Detects missing `return` after ping_callback.stop(): must not write_ping or close."""
        obj, iol = make_protocol(is_closing=True, has_ping_callback=True)
        run_periodic_ping(obj, iol)
        obj.ping_callback.stop.assert_called_once()
        obj.write_ping.assert_not_called()
        obj.close.assert_not_called()
```

```python
# test_whitebox.py
import asyncio
import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from tornado.websocket import WebSocketProtocol13
from tornado.ioloop import IOLoop

# ---------------------------------------------------------------------------
# Helpers to build a minimal WebSocketProtocol13-like object without needing
# a real TCP connection.  We monkey-patch the instance so that only the
# logic inside periodic_ping is exercised.
# ---------------------------------------------------------------------------

def _make_protocol(
    is_closing: bool,
    ping_callback_not_none: bool,
    ping_interval: float,
    ping_timeout: float,
    last_pong_offset: float,   # now - last_pong  (positive = pong was this long ago)
    last_ping_offset: float,   # now - last_ping  (positive = ping was this long ago)
    now: float = 1000.0,
):
    """
    Build a duck-typed object that satisfies the attributes and methods
    accessed by periodic_ping, without constructing a real
    WebSocketProtocol13 (which requires a live handler/stream).
    """
    proto = object.__new__(WebSocketProtocol13)

    proto.ping_interval = ping_interval
    proto.ping_timeout = ping_timeout
    proto.last_pong = now - last_pong_offset
    proto.last_ping = now - last_ping_offset

    proto.is_closing = MagicMock(return_value=is_closing)

    if ping_callback_not_none:
        proto.ping_callback = MagicMock()
    else:
        proto.ping_callback = None

    proto.close = MagicMock()
    proto.write_ping = MagicMock()

    return proto, now


def _run_periodic_ping(proto, now: float):
    """Invoke periodic_ping with a patched IOLoop.current().time()."""
    mock_ioloop = MagicMock()
    mock_ioloop.time.return_value = now
    with patch("tornado.websocket.IOLoop.current", return_value=mock_ioloop):
        WebSocketProtocol13.periodic_ping(proto)


# ---------------------------------------------------------------------------
# --- Statement Coverage ---
# Every executable statement is hit by at least one test below.
# ---------------------------------------------------------------------------

def test_sc_is_closing_with_callback_stops_and_returns():
    """
    Statement: is_closing() True + ping_callback not None
    → ping_callback.stop() called, early return (write_ping never reached).
    """
    # path: is_closing=True, ping_callback set → stop + return
    proto, now = _make_protocol(
        is_closing=True,
        ping_callback_not_none=True,
        ping_interval=30,
        ping_timeout=60,
        last_pong_offset=5,
        last_ping_offset=5,
    )
    _run_periodic_ping(proto, now)

    proto.ping_callback.stop.assert_called_once()
    proto.write_ping.assert_not_called()
    proto.close.assert_not_called()


def test_sc_timeout_triggers_close():
    """
    Statement: timeout branch → self.close() + return.
    since_last_ping < 2*ping_interval  AND  since_last_pong > ping_timeout
    """
    # ping_interval=30, so 2*ping_interval=60; last_ping 10s ago → 10 < 60 ✓
    # ping_timeout=20; last_pong 30s ago → 30 > 20 ✓
    proto, now = _make_protocol(
        is_closing=False,
        ping_callback_not_none=False,
        ping_interval=30,
        ping_timeout=20,
        last_pong_offset=30,   # since_last_pong=30 > 20
        last_ping_offset=10,   # since_last_ping=10 < 60
    )
    _run_periodic_ping(proto, now)

    proto.close.assert_called_once()
    proto.write_ping.assert_not_called()


def test_sc_normal_ping_sent():
    """
    Statement: normal flow → write_ping(b"") called and last_ping updated.
    """
    proto, now = _make_protocol(
        is_closing=False,
        ping_callback_not_none=False,
        ping_interval=30,
        ping_timeout=60,
        last_pong_offset=5,    # since_last_pong=5 < 60, no timeout
        last_ping_offset=10,   # since_last_ping=10 < 60
    )
    _run_periodic_ping(proto, now)

    proto.write_ping.assert_called_once_with(b"")
    assert proto.last_ping == now  # last_ping updated to now
    proto.close.assert_not_called()


# ---------------------------------------------------------------------------
# --- Block Coverage ---
# Every basic block (including else/fall-through blocks) is executed.
# ---------------------------------------------------------------------------

def test_bc_is_closing_no_callback_falls_through():
    """
    Block: is_closing=True but ping_callback is None
    → the inner if-body is NOT entered; execution continues past the
      is_closing block, through the timeout check, to write_ping.
    A correct implementation should still send a ping if the timeout
    condition is not met.
    """
    # since_last_ping=10 < 2*30=60, since_last_pong=5 < 60 → no timeout
    proto, now = _make_protocol(
        is_closing=True,
        ping_callback_not_none=False,
        ping_interval=30,
        ping_timeout=60,
        last_pong_offset=5,
        last_ping_offset=10,
    )
    _run_periodic_ping(proto, now)

    # ping_callback is None so stop() must NOT be called
    # is_closing=True but ping_callback=None → falls through
    # No timeout → write_ping should be called
    proto.write_ping.assert_called_once_with(b"")


def test_bc_not_closing_no_timeout_normal():
    """
    Block: is_closing=False → skip first if entirely; no timeout → write_ping.
    (Covered also by test_sc_normal_ping_sent; kept for block labelling.)
    """
    proto, now = _make_protocol(
        is_closing=False,
        ping_callback_not_none=False,
        ping_interval=10,
        ping_timeout=30,
        last_pong_offset=2,
        last_ping_offset=2,
    )
    _run_periodic_ping(proto, now)

    proto.write_ping.assert_called_once_with(b"")
    proto.close.assert_not_called()


# The "timeout block" and "early-return-after-stop block" are covered by
# test_sc_is_closing_with_callback_stops_and_returns and test_sc_timeout_triggers_close.


# ---------------------------------------------------------------------------
# --- Condition Coverage ---
# Each boolean sub-expression evaluates to both True and False.
#
# Outer condition: self.is_closing() [A]  AND  self.ping_callback is not None [B]
# Inner condition:
#   C: since_last_ping < 2 * self.ping_interval
#   D: since_last_pong > self.ping_timeout
# ---------------------------------------------------------------------------

# A=True, B=True  → tested by test_sc_is_closing_with_callback_stops_and_returns
# A=True, B=False → tested by test_bc_is_closing_no_callback_falls_through

def test_cc_A_false():
    """
    Condition A (is_closing) = False.
    # A: False
    """
    proto, now = _make_protocol(
        is_closing=False,
        ping_callback_not_none=True,
        ping_interval=30,
        ping_timeout=60,
        last_pong_offset=5,
        last_ping_offset=5,
    )
    _run_periodic_ping(proto, now)

    proto.ping_callback.stop.assert_not_called()
    proto.write_ping.assert_called_once_with(b"")


def test_cc_C_true_D_true():
    """
    Timeout condition: C=True AND D=True → close().
    # C: since_last_ping(10) < 2*ping_interval(60) → True
    # D: since_last_pong(30) > ping_timeout(20)    → True
    """
    proto, now = _make_protocol(
        is_closing=False,
        ping_callback_not_none=False,
        ping_interval=30,
        ping_timeout=20,
        last_pong_offset=30,
        last_ping_offset=10,
    )
    _run_periodic_ping(proto, now)
    proto.close.assert_called_once()


def test_cc_C_false_D_true():
    """
    Timeout condition not met because C=False (ping was too long ago).
    # C: since_last_ping(80) < 2*ping_interval(60) → False
    # D: since_last_pong(30) > ping_timeout(20)    → True (but C short-circuits)
    A correct implementation should send a ping (no close).
    """
    proto, now = _make_protocol(
        is_closing=False,
        ping_callback_not_none=False,
        ping_interval=30,
        ping_timeout=20,
        last_pong_offset=30,   # D=True
        last_ping_offset=80,   # C=False  (80 is NOT < 60)
    )
    _run_periodic_ping(proto, now)

    proto.close.assert_not_called()
    proto.write_ping.assert_called_once_with(b"")


def test_cc_C_true_D_false():
    """
    Timeout condition not met because D=False (pong was recent).
    # C: since_last_ping(10) < 2*ping_interval(60) → True
    # D: since_last_pong(5)  > ping_timeout(20)    → False
    A correct implementation should send a ping (no close).
    """
    proto, now = _make_protocol(
        is_closing=False,
        ping_callback_not_none=False,
        ping_interval=30,
        ping_timeout=20,
        last_pong_offset=5,    # D=False (5 is NOT > 20)
        last_ping_offset=10,   # C=True
    )
    _run_periodic_ping(proto, now)

    proto.close.assert_not_called()
    proto.write_ping.assert_called_once_with(b"")


def test_cc_C_false_D_false():
    """
    Timeout condition not met: C=False AND D=False.
    # C: since_last_ping(80) < 2*ping_interval(60) → False
    # D: since_last_pong(5)  > ping_timeout(20)    → False
    """
    proto, now = _make_protocol(
        is_closing=False,
        ping_callback_not_none=False,
        ping_interval=30,
        ping_timeout=20,
        last_pong_offset=5,
        last_ping_offset=80,
    )
    _run_periodic_ping(proto, now)

    proto.close.assert_not_called()
    proto.write_ping.assert_called_once_with(b"")


# ---------------------------------------------------------------------------
# --- Path Coverage ---
# Distinct entry-to-exit paths through periodic_ping.
#
# Path 1: is_closing=T, ping_callback!=None → stop + return
# Path 2: is_closing=T, ping_callback=None  → fall through → no timeout → write_ping
# Path 3: is_closing=F                      → no timeout → write_ping
# Path 4: is_closing=F                      → timeout (C&D) → close + return
# (Path with is_closing=F and ping_callback exists but is_closing=F skips that branch)
# ---------------------------------------------------------------------------

def test_path1_closing_with_callback():
    """
    # path: is_closing=True → ping_callback not None → stop() → return
    """
    proto, now = _make_protocol(
        is_closing=True,
        ping_callback_not_none=True,
        ping_interval=30,
        ping_timeout=60,
        last_pong_offset=5,
        last_ping_offset=5,
    )
    _run_periodic_ping(proto, now)

    proto.ping_callback.stop.assert_called_once()
    proto.write_ping.assert_not_called()
    proto.close.assert_not_called()


def test_path2_closing_no_callback_no_timeout():
    """
    # path: is_closing=True → ping_callback is None → skip stop
    #       → C=True, D=False → no timeout → write_ping + update last_ping
    """
    proto, now = _make_protocol(
        is_closing=True,
        ping_callback_not_none=False,
        ping_interval=30,
        ping_timeout=60,
        last_pong_offset=5,    # D: 5 > 60 → False
        last_ping_offset=10,   # C: 10 < 60 → True
    )
    _run_periodic_ping(proto, now)

    proto.close.assert_not_called()
    proto.write_ping.assert_called_once_with(b"")
    assert proto.last_ping == now


def test_path3_not_closing_no_timeout():
    """
    # path: is_closing=False → skip first if entirely
    #       → C=True, D=False → no timeout → write_ping + update last_ping
    """
    proto, now = _make_protocol(
        is_closing=False,
        ping_callback_not_none=False,
        ping_interval=30,
        ping_timeout=60,
        last_pong_offset=5,
        last_ping_offset=10,
    )
    _run_periodic_ping(proto, now)

    proto.close.assert_not_called()
    proto.write_ping.assert_called_once_with(b"")
    assert proto.last_ping == now


def test_path4_not_closing_timeout():
    """
    # path: is_closing=False → skip first if
    #       → C=True, D=True → close() → return (write_ping not reached)
    """
    proto, now = _make_protocol(
        is_closing=False,
        ping_callback_not_none=False,
        ping_interval=30,
        ping_timeout=20,
        last_pong_offset=30,   # since_last_pong=30 > 20 → D=True
        last_ping_offset=10,   # since_last_ping=10 < 60 → C=True
    )
    _run_periodic_ping(proto, now)

    proto.close.assert_called_once()
    proto.write_ping.assert_not_called()
    # last_ping should NOT be updated after a close-triggered return
    assert proto.last_ping != now


def test_path_last_ping_updated_correctly():
    """
    Property: after a successful write_ping, last_ping must equal the current
    time returned by IOLoop (a correct implementation MUST do this so the
    next call can correctly compute since_last_ping).
    """
    proto, now = _make_protocol(
        is_closing=False,
        ping_callback_not_none=False,
        ping_interval=30,
        ping_timeout=60,
        last_pong_offset=2,
        last_ping_offset=2,
    )
    _run_periodic_ping(proto, now)

    assert proto.last_ping == now, (
        "A correct periodic_ping MUST update last_ping to the current IOLoop time "
        "after sending a ping."
    )


def test_path_write_ping_receives_empty_bytes():
    """
    Property: write_ping must always be called with b"" (keep-alive with no payload).
    """
    proto, now = _make_protocol(
        is_closing=False,
        ping_callback_not_none=False,
        ping_interval=10,
        ping_timeout=60,
        last_pong_offset=1,
        last_ping_offset=1,
    )
    _run_periodic_ping(proto, now)

    args, _ = proto.write_ping.call_args
    assert args[0] == b"", "A correct periodic_ping MUST call write_ping with b''"
```

## Error Message(s)

### [FAILURE] test_ecp_closing_without_callback_returns_immediately (type: blackbox)
```
eval_output\bugsinpy_29-03-2026_00-50\tornado-1\generated_tests\periodic_ping_3\test_blackbox.py:177: in test_ecp_closing_without_callback_returns_immediately
    obj.write_ping.assert_not_called()
C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.11_3.11.2544.0_x64__qbz5n2kfra8p0\Lib\unittest\mock.py:900: in assert_not_called
    raise AssertionError(msg)
E   AssertionError: Expected 'write_ping' to not have been called. Called 1 times.
E   Calls: [call(b'')].
```

### [FAILURE] test_mutation_callback_none_no_stop_called (type: blackbox)
```
eval_output\bugsinpy_29-03-2026_00-50\tornado-1\generated_tests\periodic_ping_3\test_blackbox.py:397: in test_mutation_callback_none_no_stop_called
    obj.write_ping.assert_not_called()
C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.11_3.11.2544.0_x64__qbz5n2kfra8p0\Lib\unittest\mock.py:900: in assert_not_called
    raise AssertionError(msg)
E   AssertionError: Expected 'write_ping' to not have been called. Called 1 times.
E   Calls: [call(b'')].
```

### [FAILURE] test_sc_is_closing_with_callback_stops_and_returns (type: whitebox)
```
eval_output\bugsinpy_29-03-2026_00-50\tornado-1\generated_tests\periodic_ping_3\test_whitebox.py:69: in test_sc_is_closing_with_callback_stops_and_returns
    proto, now = _make_protocol(
eval_output\bugsinpy_29-03-2026_00-50\tornado-1\generated_tests\periodic_ping_3\test_whitebox.py:32: in _make_protocol
    proto.ping_interval = ping_interval
    ^^^^^^^^^^^^^^^^^^^
E   AttributeError: property 'ping_interval' of 'WebSocketProtocol13' object has no setter
```

### [FAILURE] test_sc_timeout_triggers_close (type: whitebox)
```
eval_output\bugsinpy_29-03-2026_00-50\tornado-1\generated_tests\periodic_ping_3\test_whitebox.py:91: in test_sc_timeout_triggers_close
    proto, now = _make_protocol(
eval_output\bugsinpy_29-03-2026_00-50\tornado-1\generated_tests\periodic_ping_3\test_whitebox.py:32: in _make_protocol
    proto.ping_interval = ping_interval
    ^^^^^^^^^^^^^^^^^^^
E   AttributeError: property 'ping_interval' of 'WebSocketProtocol13' object has no setter
```

### [FAILURE] test_sc_normal_ping_sent (type: whitebox)
```
eval_output\bugsinpy_29-03-2026_00-50\tornado-1\generated_tests\periodic_ping_3\test_whitebox.py:109: in test_sc_normal_ping_sent
    proto, now = _make_protocol(
eval_output\bugsinpy_29-03-2026_00-50\tornado-1\generated_tests\periodic_ping_3\test_whitebox.py:32: in _make_protocol
    proto.ping_interval = ping_interval
    ^^^^^^^^^^^^^^^^^^^
E   AttributeError: property 'ping_interval' of 'WebSocketProtocol13' object has no setter
```

### [FAILURE] test_bc_is_closing_no_callback_falls_through (type: whitebox)
```
eval_output\bugsinpy_29-03-2026_00-50\tornado-1\generated_tests\periodic_ping_3\test_whitebox.py:138: in test_bc_is_closing_no_callback_falls_through
    proto, now = _make_protocol(
eval_output\bugsinpy_29-03-2026_00-50\tornado-1\generated_tests\periodic_ping_3\test_whitebox.py:32: in _make_protocol
    proto.ping_interval = ping_interval
    ^^^^^^^^^^^^^^^^^^^
E   AttributeError: property 'ping_interval' of 'WebSocketProtocol13' object has no setter
```

### [FAILURE] test_bc_not_closing_no_timeout_normal (type: whitebox)
```
eval_output\bugsinpy_29-03-2026_00-50\tornado-1\generated_tests\periodic_ping_3\test_whitebox.py:159: in test_bc_not_closing_no_timeout_normal
    proto, now = _make_protocol(
eval_output\bugsinpy_29-03-2026_00-50\tornado-1\generated_tests\periodic_ping_3\test_whitebox.py:32: in _make_protocol
    proto.ping_interval = ping_interval
    ^^^^^^^^^^^^^^^^^^^
E   AttributeError: property 'ping_interval' of 'WebSocketProtocol13' object has no setter
```

### [FAILURE] test_cc_A_false (type: whitebox)
```
eval_output\bugsinpy_29-03-2026_00-50\tornado-1\generated_tests\periodic_ping_3\test_whitebox.py:195: in test_cc_A_false
    proto, now = _make_protocol(
eval_output\bugsinpy_29-03-2026_00-50\tornado-1\generated_tests\periodic_ping_3\test_whitebox.py:32: in _make_protocol
    proto.ping_interval = ping_interval
    ^^^^^^^^^^^^^^^^^^^
E   AttributeError: property 'ping_interval' of 'WebSocketProtocol13' object has no setter
```

### [FAILURE] test_cc_C_true_D_true (type: whitebox)
```
eval_output\bugsinpy_29-03-2026_00-50\tornado-1\generated_tests\periodic_ping_3\test_whitebox.py:215: in test_cc_C_true_D_true
    proto, now = _make_protocol(
eval_output\bugsinpy_29-03-2026_00-50\tornado-1\generated_tests\periodic_ping_3\test_whitebox.py:32: in _make_protocol
    proto.ping_interval = ping_interval
    ^^^^^^^^^^^^^^^^^^^
E   AttributeError: property 'ping_interval' of 'WebSocketProtocol13' object has no setter
```

### [FAILURE] test_cc_C_false_D_true (type: whitebox)
```
eval_output\bugsinpy_29-03-2026_00-50\tornado-1\generated_tests\periodic_ping_3\test_whitebox.py:234: in test_cc_C_false_D_true
    proto, now = _make_protocol(
eval_output\bugsinpy_29-03-2026_00-50\tornado-1\generated_tests\periodic_ping_3\test_whitebox.py:32: in _make_protocol
    proto.ping_interval = ping_interval
    ^^^^^^^^^^^^^^^^^^^
E   AttributeError: property 'ping_interval' of 'WebSocketProtocol13' object has no setter
```
