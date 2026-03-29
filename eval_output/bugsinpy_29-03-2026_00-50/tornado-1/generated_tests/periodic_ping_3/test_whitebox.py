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

    # ping_interval and ping_timeout are properties without setters on
    # WebSocketProtocol13, so we store directly in the instance dict to
    # shadow the class-level property descriptors.
    proto.__dict__['ping_interval'] = ping_interval
    proto.__dict__['ping_timeout'] = ping_timeout
    proto.__dict__['last_pong'] = now - last_pong_offset
    proto.__dict__['last_ping'] = now - last_ping_offset

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
    → the inner if-body is NOT entered; execution returns early since
      is_closing=True causes an early return regardless of ping_callback.
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
    # is_closing=True → early return, write_ping should NOT be called
    proto.write_ping.assert_not_called()


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
# Path 2: is_closing=T, ping_callback=None  → early return (is_closing always returns)
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
    # path: is_closing=True → ping_callback is None → skip stop → early return
    A correct implementation returns early when is_closing() is True,
    regardless of ping_callback being None.
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
    proto.write_ping.assert_not_called()


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