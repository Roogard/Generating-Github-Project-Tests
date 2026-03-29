import pytest
from unittest.mock import MagicMock, patch
from tornado.httpclient import AsyncHTTPClient


# ---------------------------------------------------------------------------
# Helpers – build a minimal AsyncHTTPClient-like instance without a real
# IOLoop / network stack.  We patch only the parts that would require live
# I/O; the logic under test (close()) is pure attribute manipulation.
# ---------------------------------------------------------------------------

def _make_client(closed=False, instance_cache=None, io_loop=None):
    """Return a bare AsyncHTTPClient instance whose internal state we control."""
    # Use object.__new__ to skip __init__ (which tries to connect to a real
    # IOLoop).  We then inject exactly the attributes that close() reads.
    client = object.__new__(AsyncHTTPClient)
    client._closed = closed
    client._instance_cache = instance_cache
    client.io_loop = io_loop
    return client


# ---------------------------------------------------------------------------
# --- Statement Coverage ---
# Every executable statement inside close() is reached at least once.
# ---------------------------------------------------------------------------

def test_stmt_already_closed_returns_early():
    # path: _closed is True → early return, nothing else executes
    client = _make_client(closed=True)
    # A correct close() on an already-closed client should be a no-op.
    client.close()  # must not raise
    assert client._closed is True  # still closed, nothing changed


def test_stmt_sets_closed_true():
    # path: _closed is False, _instance_cache is None
    # Executes: "self._closed = True" and the None-guard skips the cache block.
    client = _make_client(closed=False, instance_cache=None)
    client.close()
    assert client._closed is True


def test_stmt_deletes_from_cache():
    # path: _closed is False, cache is not None, cache entry matches self
    # Executes: self._closed = True, cache check, del cache[io_loop]
    loop_key = object()
    cache = {}
    client = _make_client(closed=False, instance_cache=cache, io_loop=loop_key)
    cache[loop_key] = client  # consistent state
    client.close()
    assert client._closed is True
    assert loop_key not in cache  # entry was deleted


def test_stmt_raises_on_inconsistent_cache():
    # path: _closed is False, cache is not None, cache entry does NOT match self
    # Executes: self._closed = True, cache check → RuntimeError
    loop_key = object()
    other = object()
    cache = {loop_key: other}
    client = _make_client(closed=False, instance_cache=cache, io_loop=loop_key)
    with pytest.raises(RuntimeError):
        client.close()


# ---------------------------------------------------------------------------
# --- Block Coverage ---
# Every basic block (contiguous statements between branch points) is entered.
# ---------------------------------------------------------------------------
# Block A: function entry up to "if self._closed" – covered by all tests.
# Block B: body of "if self._closed" (early-return block) – test_stmt_already_closed_returns_early
# Block C: after the first if – "self._closed = True; if self._instance_cache …"
# Block D: body of "if self._instance_cache is not None" – the inner if + del
# Block E: body of "if self._instance_cache.get(…) is not self" → RuntimeError
# Block F: "del self._instance_cache[self.io_loop]" – test_stmt_deletes_from_cache

def test_block_no_cache_skips_inner_if():
    # Block C without entering Block D (cache is None).
    client = _make_client(closed=False, instance_cache=None)
    client.close()
    assert client._closed is True  # Block C executed, Block D skipped

def test_block_cache_present_no_error():
    # Block D with the inner condition FALSE (cache matches → go to del, Block F).
    loop_key = "loop"
    cache = {}
    client = _make_client(closed=False, instance_cache=cache, io_loop=loop_key)
    cache[loop_key] = client
    client.close()
    assert loop_key not in cache

def test_block_cache_inconsistency_raises():
    # Block E: inner condition TRUE → RuntimeError (Block F is NOT reached).
    # _closed=True  # _closed: False, so we enter the main body
    loop_key = "loop"
    cache = {loop_key: "something_else"}
    client = _make_client(closed=False, instance_cache=cache, io_loop=loop_key)
    with pytest.raises(RuntimeError, match="inconsistent"):
        client.close()


# ---------------------------------------------------------------------------
# --- Condition Coverage ---
# Each boolean sub-expression evaluates to both True and False.
#
# Conditions in close():
#   C1: self._closed               (line: if self._closed)
#   C2: self._instance_cache is not None  (line: if self._instance_cache…)
#   C3: self._instance_cache.get(self.io_loop) is not self  (inner if)
# ---------------------------------------------------------------------------

def test_cond_c1_true():
    # C1: self._closed = True → early return
    client = _make_client(closed=True)
    client.close()
    assert client._closed is True  # still True; no mutation


def test_cond_c1_false_c2_false():
    # C1: False (not yet closed), C2: False (cache is None)
    client = _make_client(closed=False, instance_cache=None)
    client.close()
    assert client._closed is True


def test_cond_c1_false_c2_true_c3_false():
    # C1: False, C2: True (cache not None), C3: False (cache entry IS self → no error)
    loop_key = object()
    cache = {}
    client = _make_client(closed=False, instance_cache=cache, io_loop=loop_key)
    cache[loop_key] = client
    client.close()
    assert client._closed is True
    assert loop_key not in cache


def test_cond_c1_false_c2_true_c3_true():
    # C1: False, C2: True, C3: True (cache entry is NOT self → RuntimeError)
    loop_key = object()
    cache = {loop_key: MagicMock()}
    client = _make_client(closed=False, instance_cache=cache, io_loop=loop_key)
    with pytest.raises(RuntimeError):
        client.close()


# ---------------------------------------------------------------------------
# --- Path Coverage ---
# Distinct entry-to-exit routes through close():
#
#   Path 1: _closed=True  → early return
#   Path 2: _closed=False, cache=None  → set closed, skip cache block, return
#   Path 3: _closed=False, cache≠None, cache[io_loop] IS self  → set closed, del, return
#   Path 4: _closed=False, cache≠None, cache[io_loop] is NOT self  → set closed, raise RuntimeError
# ---------------------------------------------------------------------------

def test_path1_early_return():
    # path: if-_closed-True → return
    client = _make_client(closed=True)
    before = client._closed
    client.close()
    assert client._closed == before  # unchanged; early exit


def test_path2_no_cache():
    # path: if-_closed-False → _closed=True → if-cache-None-skip → return
    client = _make_client(closed=False, instance_cache=None)
    client.close()
    assert client._closed is True


def test_path3_cache_consistent():
    # path: if-_closed-False → _closed=True → cache≠None → inner-if-False → del → return
    loop_key = "my_loop"
    cache = {}
    client = _make_client(closed=False, instance_cache=cache, io_loop=loop_key)
    cache[loop_key] = client
    client.close()
    assert client._closed is True
    assert loop_key not in cache


def test_path4_cache_inconsistent_raises():
    # path: if-_closed-False → _closed=True → cache≠None → inner-if-True → raise RuntimeError
    loop_key = "my_loop"
    impostor = object()
    cache = {loop_key: impostor}
    client = _make_client(closed=False, instance_cache=cache, io_loop=loop_key)
    with pytest.raises(RuntimeError, match="inconsistent AsyncHTTPClient cache"):
        client.close()
    # Even though RuntimeError is raised, _closed was set to True before the check
    assert client._closed is True


def test_path3_cache_key_missing():
    # Edge variant of Path 3 / Path 4: cache exists but has NO entry for io_loop.
    # cache.get(io_loop) returns None, which is not self → RuntimeError.
    # A correct implementation should raise RuntimeError when cache state is inconsistent.
    loop_key = "absent_loop"
    cache = {}  # no entry for loop_key
    client = _make_client(closed=False, instance_cache=cache, io_loop=loop_key)
    with pytest.raises(RuntimeError, match="inconsistent"):
        client.close()


def test_idempotent_double_close():
    # Calling close() twice must be safe; the second call is a no-op (Path 1).
    loop_key = object()
    cache = {}
    client = _make_client(closed=False, instance_cache=cache, io_loop=loop_key)
    cache[loop_key] = client
    client.close()  # first call – Path 3
    assert client._closed is True
    assert loop_key not in cache
    client.close()  # second call – Path 1 (already closed)
    assert client._closed is True  # still True, no exception