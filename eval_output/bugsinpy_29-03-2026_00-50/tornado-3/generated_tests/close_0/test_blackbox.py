import pytest
from unittest.mock import MagicMock, patch
from tornado.httpclient import AsyncHTTPClient


# ---------------------------------------------------------------------------
# Helpers – build a minimal AsyncHTTPClient-like instance without touching
# the real singleton cache or requiring a running IOLoop.
# ---------------------------------------------------------------------------

def _make_client(closed=False, instance_cache=None, io_loop=None):
    """Return an AsyncHTTPClient whose internal state we control directly."""
    # Use force_instance so the real cache is not polluted
    client = object.__new__(AsyncHTTPClient)
    client._closed = closed
    client._instance_cache = instance_cache
    client.io_loop = io_loop
    return client


# --- BVA ---

class TestCloseBVA:
    def test_close_when_already_closed_no_error(self):
        """BVA: calling close() on an already-closed client must be a no-op."""
        client = _make_client(closed=True, instance_cache=None)
        # A correct close() on an already-closed client should not raise and
        # should leave _closed == True.
        client.close()
        assert client._closed is True

    def test_close_sets_closed_flag(self):
        """BVA: calling close() on an open client with no cache must set _closed."""
        client = _make_client(closed=False, instance_cache=None)
        client.close()
        assert client._closed is True

    def test_close_with_none_instance_cache_skips_cache_logic(self):
        """BVA: _instance_cache is None → no RuntimeError, _closed becomes True."""
        client = _make_client(closed=False, instance_cache=None)
        client.close()  # must not raise
        assert client._closed is True

    def test_close_with_empty_cache_matching_self(self):
        """BVA: _instance_cache is a dict containing exactly this client → normal removal."""
        io_loop = object()
        cache = {}
        client = _make_client(closed=False, instance_cache=cache, io_loop=io_loop)
        cache[io_loop] = client
        client.close()
        assert client._closed is True
        assert io_loop not in cache

    def test_close_idempotent_second_call_no_side_effects(self):
        """BVA: second close() call must not re-enter cache logic."""
        io_loop = object()
        cache = {}
        client = _make_client(closed=False, instance_cache=cache, io_loop=io_loop)
        cache[io_loop] = client
        client.close()
        # At this point io_loop is already removed from cache.
        # A second close() must be a pure no-op (guard: self._closed is True).
        client.close()
        assert client._closed is True


# --- ECP ---

class TestCloseECP:
    # Valid class 1: client not closed, no instance cache
    def test_valid_no_cache(self):
        """ECP: open client, no cache – a correct close should set _closed=True."""
        client = _make_client(closed=False, instance_cache=None)
        client.close()
        assert client._closed is True

    # Valid class 2: client not closed, cache present and consistent
    def test_valid_consistent_cache(self):
        """ECP: open client, consistent cache – should remove entry and set _closed."""
        io_loop = object()
        cache = {}
        client = _make_client(closed=False, instance_cache=cache, io_loop=io_loop)
        cache[io_loop] = client
        client.close()
        assert client._closed is True
        assert io_loop not in cache

    # Invalid class: cache present but inconsistent (different client stored)
    def test_invalid_inconsistent_cache_raises(self):
        """ECP: cache exists but holds a *different* client → RuntimeError."""
        io_loop = object()
        other_client = object()
        cache = {io_loop: other_client}
        client = _make_client(closed=False, instance_cache=cache, io_loop=io_loop)
        with pytest.raises(RuntimeError, match="inconsistent AsyncHTTPClient cache"):
            client.close()

    # Invalid class 2: cache present but io_loop not in cache (get returns None → not self)
    def test_invalid_io_loop_absent_from_cache_raises(self):
        """ECP: cache exists but io_loop key absent → get() returns None, not self → RuntimeError."""
        io_loop = object()
        cache = {}  # io_loop not present
        client = _make_client(closed=False, instance_cache=cache, io_loop=io_loop)
        with pytest.raises(RuntimeError, match="inconsistent AsyncHTTPClient cache"):
            client.close()

    # Valid class 3: already-closed client
    def test_valid_already_closed(self):
        """ECP: _closed is True → early return, no mutation of state."""
        io_loop = object()
        cache = {}
        client = _make_client(closed=True, instance_cache=cache, io_loop=io_loop)
        # Calling close() must not raise and must not touch cache
        client.close()
        assert client._closed is True
        assert io_loop not in cache  # cache was never written, nothing to remove


# --- Mutation Detection ---

class TestCloseMutationDetection:
    def test_mutation_wrong_flag_check_if_not_closed(self):
        """
        Mutation: `if not self._closed` instead of `if self._closed`.
        A correct close() on an already-closed client should be a no-op.
        If the guard were inverted the method would try to re-close.
        """
        client = _make_client(closed=True, instance_cache=None)
        client.close()  # must not raise or change any cache
        assert client._closed is True

    def test_mutation_flag_not_set_to_true(self):
        """
        Mutation: `self._closed = False` instead of `self._closed = True`.
        A correct close() must leave _closed == True.
        """
        client = _make_client(closed=False, instance_cache=None)
        client.close()
        assert client._closed is True  # detects wrong constant

    def test_mutation_del_wrong_key(self):
        """
        Mutation: deletes a wrong key (e.g., `del self._instance_cache[None]`).
        After a correct close(), the exact io_loop key must be absent.
        """
        io_loop = object()
        other_key = object()
        cache = {io_loop: None}  # placeholder; will be replaced
        client = _make_client(closed=False, instance_cache=cache, io_loop=io_loop)
        cache[io_loop] = client
        cache[other_key] = object()  # unrelated entry
        client.close()
        # Correct implementation removes only io_loop
        assert io_loop not in cache
        assert other_key in cache  # unrelated entry must survive

    def test_mutation_is_vs_equality_in_cache_check(self):
        """
        Mutation: `!=` instead of `is not` in cache consistency check.
        Using a distinct object that equals self would break == but not `is`.
        We test that the exact same object passes the identity check.
        """
        io_loop = object()
        cache = {}
        client = _make_client(closed=False, instance_cache=cache, io_loop=io_loop)
        cache[io_loop] = client  # same object
        # A correct close() must NOT raise when the identity matches
        client.close()
        assert client._closed is True

    def test_mutation_cache_check_inverted_raises_wrong_direction(self):
        """
        Mutation: `if self._instance_cache.get(self.io_loop) is self` (inverted guard).
        Correct behaviour: raises when cache entry is NOT self.
        """
        io_loop = object()
        other = object()
        cache = {io_loop: other}
        client = _make_client(closed=False, instance_cache=cache, io_loop=io_loop)
        # A correct implementation must raise here
        with pytest.raises(RuntimeError):
            client.close()

    def test_mutation_returns_before_setting_closed(self):
        """
        Mutation: `return` placed before `self._closed = True`.
        A correct close() must set _closed even if no cache is present.
        """
        client = _make_client(closed=False, instance_cache=None)
        client.close()
        assert client._closed is True  # would fail if return is premature

    def test_mutation_cache_not_deleted_after_close(self):
        """
        Mutation: the `del self._instance_cache[self.io_loop]` line is missing.
        A correct close() must remove the io_loop key from the cache dict.
        """
        io_loop = object()
        cache = {}
        client = _make_client(closed=False, instance_cache=cache, io_loop=io_loop)
        cache[io_loop] = client
        client.close()
        assert io_loop not in cache  # detects missing del