import pytest
from unittest.mock import MagicMock, patch
from tornado.websocket import WebSocketHandler


# ---------------------------------------------------------------------------
# Helpers – build a minimal WebSocketHandler without a real HTTP server
# ---------------------------------------------------------------------------

def _make_handler(stream=None):
    """Return a WebSocketHandler instance with mocked internals."""
    application = MagicMock()
    application.settings = {}
    application.ui_methods = {}
    application.ui_modules = {}

    request = MagicMock()
    request.connection = MagicMock()
    request.connection.set_close_callback = MagicMock()
    request.full_url = MagicMock(return_value="ws://localhost/ws")
    request.headers = {"Host": "localhost", "Upgrade": "websocket",
                       "Connection": "Upgrade",
                       "Sec-Websocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                       "Sec-Websocket-Version": "13"}

    handler = WebSocketHandler.__new__(WebSocketHandler)
    handler.application = application
    handler.request = request
    handler.__dict__['settings'] = {}
    handler._finished = False
    handler._headers_written = False
    handler.stream = stream
    return handler


# ---------------------------------------------------------------------------
# --- Statement Coverage ---
# ---------------------------------------------------------------------------

class TestStatementCoverage:
    def test_set_nodelay_true_calls_stream(self):
        """Every statement is reached: assert passes, stream.set_nodelay called."""
        mock_stream = MagicMock()
        handler = _make_handler(stream=mock_stream)

        handler.set_nodelay(True)

        # A correct implementation MUST delegate to the underlying stream.
        mock_stream.set_nodelay.assert_called_once_with(True)

    def test_set_nodelay_false_calls_stream(self):
        """Statement coverage – False value path also reaches every statement."""
        mock_stream = MagicMock()
        handler = _make_handler(stream=mock_stream)

        handler.set_nodelay(False)

        mock_stream.set_nodelay.assert_called_once_with(False)

    def test_assert_raises_when_stream_is_none(self):
        """The assert self.stream is not None statement must be reachable and fire."""
        handler = _make_handler(stream=None)

        with pytest.raises(AssertionError):
            handler.set_nodelay(True)


# ---------------------------------------------------------------------------
# --- Block Coverage ---
# ---------------------------------------------------------------------------
# The function has exactly two basic blocks:
#   Block 1: the assert (raises AssertionError if stream is None)
#   Block 2: self.stream.set_nodelay(value)  (reached only when stream is not None)

class TestBlockCoverage:
    def test_block1_assert_fires(self):
        """Block 1: assert statement fires → AssertionError (stream is None)."""
        # Covered by test_assert_raises_when_stream_is_none above;
        # repeated here for explicitness.
        handler = _make_handler(stream=None)
        with pytest.raises(AssertionError):
            handler.set_nodelay(False)

    def test_block2_stream_set_nodelay_executed(self):
        """Block 2: self.stream.set_nodelay(value) is executed."""
        mock_stream = MagicMock()
        handler = _make_handler(stream=mock_stream)

        handler.set_nodelay(True)

        # Property: the call must have been forwarded exactly once with the correct arg.
        mock_stream.set_nodelay.assert_called_once_with(True)


# ---------------------------------------------------------------------------
# --- Condition Coverage ---
# ---------------------------------------------------------------------------
# The only condition is: `self.stream is not None`

class TestConditionCoverage:
    def test_condition_stream_is_not_none_true(self):
        """Condition `self.stream is not None` → True (stream provided).
        # stream is not None: True
        """
        mock_stream = MagicMock()
        handler = _make_handler(stream=mock_stream)

        # Should NOT raise; stream.set_nodelay should be called.
        handler.set_nodelay(True)
        mock_stream.set_nodelay.assert_called_once_with(True)

    def test_condition_stream_is_not_none_false(self):
        """Condition `self.stream is not None` → False (stream is None).
        # stream is not None: False → AssertionError
        """
        handler = _make_handler(stream=None)

        with pytest.raises(AssertionError):
            handler.set_nodelay(True)


# ---------------------------------------------------------------------------
# --- Path Coverage ---
# ---------------------------------------------------------------------------
# There are exactly two distinct paths from entry to exit:
#   Path A: assert passes  → stream.set_nodelay(value) → return (normal)
#   Path B: assert fails   → AssertionError raised      → exit via exception

class TestPathCoverage:
    def test_path_a_normal_execution_with_true(self):
        """Path A: assert passes → stream.set_nodelay(True) → normal return.
        # path: assert-passes → stream.set_nodelay(True) → return None
        """
        mock_stream = MagicMock()
        handler = _make_handler(stream=mock_stream)

        result = handler.set_nodelay(True)

        # A correct set_nodelay SHOULD return None.
        assert result is None
        mock_stream.set_nodelay.assert_called_once_with(True)

    def test_path_a_normal_execution_with_false(self):
        """Path A (False value): assert passes → stream.set_nodelay(False) → return.
        # path: assert-passes → stream.set_nodelay(False) → return None
        """
        mock_stream = MagicMock()
        handler = _make_handler(stream=mock_stream)

        result = handler.set_nodelay(False)

        assert result is None
        mock_stream.set_nodelay.assert_called_once_with(False)

    def test_path_b_assertion_error(self):
        """Path B: assert fires → AssertionError propagates, stream never touched.
        # path: assert-fails → AssertionError raised → exit via exception
        """
        handler = _make_handler(stream=None)

        with pytest.raises(AssertionError):
            handler.set_nodelay(True)

    def test_path_a_value_forwarded_unchanged(self):
        """Property test: a correct set_nodelay MUST forward the exact value received.
        # path: assert-passes → stream.set_nodelay(value) with value preserved
        """
        for value in (True, False):
            mock_stream = MagicMock()
            handler = _make_handler(stream=mock_stream)
            handler.set_nodelay(value)
            args, kwargs = mock_stream.set_nodelay.call_args
            # The stream MUST receive exactly the value passed in.
            assert args[0] is value, (
                f"set_nodelay(value={value!r}) should forward value as-is"
            )