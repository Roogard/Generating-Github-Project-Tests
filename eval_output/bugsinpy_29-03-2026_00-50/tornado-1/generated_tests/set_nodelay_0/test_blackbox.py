import pytest
from unittest.mock import MagicMock, patch
from tornado.websocket import WebSocketHandler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_handler_with_stream(stream=None):
    """
    Build a minimal WebSocketHandler instance without going through the full
    Tornado request lifecycle.  We bypass __init__ entirely and set only the
    attributes that set_nodelay() needs.
    """
    handler = object.__new__(WebSocketHandler)
    handler.stream = stream
    return handler


# --- BVA ---

class TestSetNodelayBVA:

    def test_true_boundary_value(self):
        """BVA: value=True — a correct set_nodelay SHOULD delegate True to stream."""
        mock_stream = MagicMock()
        handler = _make_handler_with_stream(mock_stream)
        handler.set_nodelay(True)
        mock_stream.set_nodelay.assert_called_once_with(True)

    def test_false_boundary_value(self):
        """BVA: value=False — a correct set_nodelay SHOULD delegate False to stream."""
        mock_stream = MagicMock()
        handler = _make_handler_with_stream(mock_stream)
        handler.set_nodelay(False)
        mock_stream.set_nodelay.assert_called_once_with(False)

    def test_none_stream_raises(self):
        """BVA: stream=None — a correct set_nodelay SHOULD raise AssertionError."""
        handler = _make_handler_with_stream(None)
        with pytest.raises(AssertionError):
            handler.set_nodelay(True)

    def test_none_stream_raises_with_false(self):
        """BVA: stream=None with value=False — SHOULD still raise AssertionError."""
        handler = _make_handler_with_stream(None)
        with pytest.raises(AssertionError):
            handler.set_nodelay(False)


# --- ECP ---

class TestSetNodelayECP:

    def test_valid_class_true_with_stream(self):
        """ECP valid class: stream is set, value=True — SHOULD call stream.set_nodelay(True)."""
        mock_stream = MagicMock()
        handler = _make_handler_with_stream(mock_stream)
        handler.set_nodelay(True)
        mock_stream.set_nodelay.assert_called_once_with(True)

    def test_valid_class_false_with_stream(self):
        """ECP valid class: stream is set, value=False — SHOULD call stream.set_nodelay(False)."""
        mock_stream = MagicMock()
        handler = _make_handler_with_stream(mock_stream)
        handler.set_nodelay(False)
        mock_stream.set_nodelay.assert_called_once_with(False)

    def test_invalid_class_no_stream(self):
        """ECP invalid class: stream=None — SHOULD raise AssertionError regardless of value."""
        handler = _make_handler_with_stream(None)
        with pytest.raises(AssertionError):
            handler.set_nodelay(True)

    def test_valid_class_exactly_one_call(self):
        """ECP: set_nodelay SHOULD call stream.set_nodelay exactly once per invocation."""
        mock_stream = MagicMock()
        handler = _make_handler_with_stream(mock_stream)
        handler.set_nodelay(True)
        assert mock_stream.set_nodelay.call_count == 1

    def test_valid_class_no_return_value(self):
        """ECP: a correct set_nodelay SHOULD return None (it's a void setter)."""
        mock_stream = MagicMock()
        handler = _make_handler_with_stream(mock_stream)
        result = handler.set_nodelay(True)
        assert result is None

    def test_valid_class_multiple_calls_preserve_order(self):
        """ECP: repeated calls SHOULD each forward their argument in order."""
        mock_stream = MagicMock()
        handler = _make_handler_with_stream(mock_stream)
        handler.set_nodelay(True)
        handler.set_nodelay(False)
        calls = [c.args[0] for c in mock_stream.set_nodelay.call_args_list]
        assert calls == [True, False]


# --- Mutation Detection ---

class TestSetNodelayMutations:

    def test_mutation_assert_negated_stream_none(self):
        """
        Detects mutation: `assert self.stream is not None` changed to
        `assert self.stream is None`.
        A correct implementation MUST raise when stream IS None,
        and MUST NOT raise when stream is a real object.
        """
        mock_stream = MagicMock()
        handler_ok = _make_handler_with_stream(mock_stream)
        # Should not raise
        handler_ok.set_nodelay(True)

        handler_bad = _make_handler_with_stream(None)
        # Must raise
        with pytest.raises(AssertionError):
            handler_bad.set_nodelay(True)

    def test_mutation_wrong_variable_passes_wrong_value(self):
        """
        Detects mutation: `self.stream.set_nodelay(value)` changed to
        `self.stream.set_nodelay(not value)` or using the wrong variable.
        The argument forwarded MUST equal the argument received.
        """
        mock_stream = MagicMock()
        handler = _make_handler_with_stream(mock_stream)
        handler.set_nodelay(True)
        forwarded_value = mock_stream.set_nodelay.call_args[0][0]
        assert forwarded_value is True  # NOT flipped

    def test_mutation_wrong_variable_false_not_flipped(self):
        """
        Detects mutation: value negated — if False is passed, False MUST be forwarded.
        """
        mock_stream = MagicMock()
        handler = _make_handler_with_stream(mock_stream)
        handler.set_nodelay(False)
        forwarded_value = mock_stream.set_nodelay.call_args[0][0]
        assert forwarded_value is False  # NOT flipped to True

    def test_mutation_calls_wrong_method_on_stream(self):
        """
        Detects mutation: wrong method called on stream (e.g., set_delay vs set_nodelay).
        A correct implementation MUST call exactly stream.set_nodelay.
        """
        mock_stream = MagicMock()
        handler = _make_handler_with_stream(mock_stream)
        handler.set_nodelay(True)
        # set_nodelay MUST have been called
        assert mock_stream.set_nodelay.called
        # No other unexpected calls on the stream related to nodelay
        # (we check call count: exactly one forwarded call)
        assert mock_stream.set_nodelay.call_count == 1

    def test_mutation_skips_delegation_entirely(self):
        """
        Detects mutation: body is skipped or commented out — stream.set_nodelay never called.
        A correct implementation MUST always forward the call to the stream.
        """
        mock_stream = MagicMock()
        handler = _make_handler_with_stream(mock_stream)
        handler.set_nodelay(False)
        mock_stream.set_nodelay.assert_called_once_with(False)

    def test_mutation_assert_uses_equality_instead_of_identity(self):
        """
        Detects mutation: `assert self.stream is not None` changed to
        `assert self.stream != None` — subtle difference for objects that
        override __eq__. Both forms should behave the same for None, but
        identity check is semantically correct. Verify None raises.
        """
        handler = _make_handler_with_stream(None)
        with pytest.raises(AssertionError):
            handler.set_nodelay(True)

    def test_mutation_constant_error_hardcoded_value(self):
        """
        Detects mutation: `self.stream.set_nodelay(True)` hardcoded instead
        of using the `value` parameter.
        Both True and False must be faithfully forwarded.
        """
        for val in (True, False):
            mock_stream = MagicMock()
            handler = _make_handler_with_stream(mock_stream)
            handler.set_nodelay(val)
            forwarded = mock_stream.set_nodelay.call_args[0][0]
            assert forwarded is val, (
                f"A correct set_nodelay SHOULD forward {val!r} but got {forwarded!r}"
            )