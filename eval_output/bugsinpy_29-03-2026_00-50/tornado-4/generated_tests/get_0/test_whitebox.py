import asyncio
import os
import tempfile
import shutil
import pytest
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock

from tornado.web import StaticFileHandler
from tornado import httputil, iostream


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_handler(
    tmp_dir: str,
    *,
    path: str = "",
    method: str = "GET",
    range_header: str = None,
    status_304: bool = False,
    absolute_path_override=None,
):
    """
    Build a minimally-configured StaticFileHandler mock that delegates only
    the real path-resolution / range-parsing logic to the actual
    implementation under test.  Everything that touches the network or the
    real Tornado application stack is replaced with lightweight stubs.
    """
    handler = MagicMock(spec=StaticFileHandler)

    # ---- request -----------------------------------------------------------
    headers = {}
    if range_header is not None:
        headers["Range"] = range_header
    handler.request = MagicMock()
    handler.request.method = method
    handler.request.headers = headers

    # ---- path helpers -------------------------------------------------------
    handler.root = tmp_dir
    handler.parse_url_path = lambda p: p
    handler.get_absolute_path = lambda root, p: os.path.join(root, p)

    real_abs = (
        absolute_path_override
        if absolute_path_override is not None
        else os.path.join(tmp_dir, path)
    )
    handler.validate_absolute_path = lambda root, ap: real_abs

    # ---- mtime / headers ----------------------------------------------------
    handler.get_modified_time = MagicMock(return_value=None)
    handler.set_headers = MagicMock()
    handler.should_return_304 = MagicMock(return_value=status_304)

    # ---- content ------------------------------------------------------------
    # Default: return whole file content as bytes
    handler.get_content = MagicMock(return_value=b"Hello, World!")
    handler.get_content_size = MagicMock(return_value=13)  # len("Hello, World!")

    # ---- response helpers ---------------------------------------------------
    handler.set_status = MagicMock()
    handler.set_header = MagicMock()
    handler.write = MagicMock()
    handler.flush = AsyncMock()

    return handler


def run(coro):
    """Run a coroutine synchronously inside a fresh event loop."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Shared tmp directory fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_dir():
    d = tempfile.mkdtemp()
    # Write a small test file
    with open(os.path.join(d, "test.txt"), "wb") as f:
        f.write(b"Hello, World!")  # 13 bytes
    yield d
    shutil.rmtree(d)


# ===========================================================================
# --- Statement Coverage ---
# ===========================================================================

class TestStatementCoverage:

    def test_absolute_path_is_none_returns_early(self, tmp_dir):
        """validate_absolute_path returns None → function returns immediately."""
        handler = _make_handler(tmp_dir, path="missing.txt")
        handler.validate_absolute_path = lambda root, ap: None

        run(StaticFileHandler.get(handler, "missing.txt"))

        # A correct implementation must not call set_headers when path is None
        handler.set_headers.assert_not_called()
        handler.write.assert_not_called()

    def test_304_path_sets_status_and_returns(self, tmp_dir):
        """should_return_304() → True: set_status(304) is called and body not written."""
        handler = _make_handler(tmp_dir, path="test.txt", status_304=True)

        run(StaticFileHandler.get(handler, "test.txt"))

        handler.set_status.assert_called_once_with(304)
        handler.write.assert_not_called()

    def test_full_file_served_no_range(self, tmp_dir):
        """No Range header, include_body=True: content is written."""
        handler = _make_handler(tmp_dir, path="test.txt")

        run(StaticFileHandler.get(handler, "test.txt"))

        handler.write.assert_called()
        # Content-Length must equal full file size
        handler.set_header.assert_any_call("Content-Length", 13)

    def test_head_request_no_body(self, tmp_dir):
        """include_body=False (HEAD): write must not be called."""
        handler = _make_handler(tmp_dir, path="test.txt", method="HEAD")
        handler.request.method = "HEAD"

        run(StaticFileHandler.get(handler, "test.txt", include_body=False))

        handler.write.assert_not_called()

    def test_range_satisfiable_partial_content(self, tmp_dir):
        """Valid Range header with a partial range: 206 Partial Content."""
        handler = _make_handler(
            tmp_dir, path="test.txt", range_header="bytes=0-4"
        )
        handler.get_content = MagicMock(return_value=b"Hello")

        run(StaticFileHandler.get(handler, "test.txt"))

        handler.set_status.assert_called_with(206)
        handler.write.assert_called()

    def test_range_not_satisfiable_start_gte_size(self, tmp_dir):
        """Range start >= size → 416 Range Not Satisfiable."""
        handler = _make_handler(
            tmp_dir, path="test.txt", range_header="bytes=100-200"
        )

        run(StaticFileHandler.get(handler, "test.txt"))

        handler.set_status.assert_called_with(416)
        handler.write.assert_not_called()

    def test_range_end_zero_returns_416(self, tmp_dir):
        """Range with suffix length 0 (end == 0) → 416."""
        handler = _make_handler(
            tmp_dir, path="test.txt", range_header="bytes=0-0"
        )
        # Force parsed range to (0, 0) so end == 0 triggers the condition
        with patch("tornado.httputil._parse_request_range", return_value=(0, 0)):
            run(StaticFileHandler.get(handler, "test.txt"))

        handler.set_status.assert_called_with(416)

    def test_stream_closed_error_exits_gracefully(self, tmp_dir):
        """StreamClosedError during write → function returns without raising."""
        handler = _make_handler(tmp_dir, path="test.txt")
        handler.flush = AsyncMock(side_effect=iostream.StreamClosedError)

        # A correct implementation must swallow StreamClosedError
        run(StaticFileHandler.get(handler, "test.txt"))  # should not raise

    def test_content_generator_iterated(self, tmp_dir):
        """get_content returns a generator: every chunk must be written."""

        def gen_chunks():
            yield b"chunk1"
            yield b"chunk2"

        handler = _make_handler(tmp_dir, path="test.txt")
        handler.get_content = MagicMock(return_value=gen_chunks())

        run(StaticFileHandler.get(handler, "test.txt"))

        assert handler.write.call_count == 2


# ===========================================================================
# --- Block Coverage ---
# ===========================================================================

class TestBlockCoverage:

    # Block: start < 0 (negative start clamped)
    def test_negative_start_clamped(self, tmp_dir):
        """Negative start in range → adjusted by adding size."""
        # bytes=-5 means last 5 bytes
        handler = _make_handler(
            tmp_dir, path="test.txt", range_header="bytes=-5"
        )
        # _parse_request_range("bytes=-5") returns (None, -5) or (size-5, None)
        # depending on Tornado version; let's control it directly
        with patch("tornado.httputil._parse_request_range", return_value=(-5, None)):
            run(StaticFileHandler.get(handler, "test.txt"))
        # A correct implementation: content_length = size - adjusted_start = 13 - 8 = 5
        handler.set_header.assert_any_call("Content-Length", 5)

    # Block: end > size (end capped at size)
    def test_end_capped_at_size(self, tmp_dir):
        """Range end beyond file size must be capped at file size."""
        with patch("tornado.httputil._parse_request_range", return_value=(0, 9999)):
            handler = _make_handler(
                tmp_dir, path="test.txt", range_header="bytes=0-9999"
            )
            run(StaticFileHandler.get(handler, "test.txt"))
        # Entire file: no 206
        handler.set_status.assert_not_called()
        handler.set_header.assert_any_call("Content-Length", 13)

    # Block: full range requested (no 206)
    def test_full_range_no_206(self, tmp_dir):
        """Range bytes=0- (full file) must NOT result in 206."""
        with patch("tornado.httputil._parse_request_range", return_value=(0, None)):
            handler = _make_handler(
                tmp_dir, path="test.txt", range_header="bytes=0-"
            )
            run(StaticFileHandler.get(handler, "test.txt"))
        handler.set_status.assert_not_called()

    # Block: start is not None, end is None → content_length = size - start
    def test_content_length_start_only(self, tmp_dir):
        """start set, end is None → content_length = size - start."""
        with patch("tornado.httputil._parse_request_range", return_value=(3, None)):
            handler = _make_handler(
                tmp_dir, path="test.txt", range_header="bytes=3-"
            )
            run(StaticFileHandler.get(handler, "test.txt"))
        handler.set_header.assert_any_call("Content-Length", 10)  # 13 - 3

    # Block: end is not None, start is None → content_length = end
    def test_content_length_end_only(self, tmp_dir):
        """start is None, end set → content_length = end."""
        with patch("tornado.httputil._parse_request_range", return_value=(None, 7)):
            handler = _make_handler(
                tmp_dir, path="test.txt", range_header="bytes=-7"
            )
            run(StaticFileHandler.get(handler, "test.txt"))
        handler.set_header.assert_any_call("Content-Length", 7)

    # Block: both start and end are not None → content_length = end - start
    def test_content_length_start_and_end(self, tmp_dir):
        """start and end both set → content_length = end - start."""
        with patch("tornado.httputil._parse_request_range", return_value=(2, 8)):
            handler = _make_handler(
                tmp_dir, path="test.txt", range_header="bytes=2-7"
            )
            run(StaticFileHandler.get(handler, "test.txt"))
        handler.set_header.assert_any_call("Content-Length", 6)  # 8 - 2

    # Block: no range → start = end = None → content_length = size
    def test_content_length_no_range(self, tmp_dir):
        """No range header → content_length = size."""
        handler = _make_handler(tmp_dir, path="test.txt")
        run(StaticFileHandler.get(handler, "test.txt"))
        handler.set_header.assert_any_call("Content-Length", 13)

    # Block: content is bytes (wrapped in list)
    def test_bytes_content_wrapped_and_written(self, tmp_dir):
        """get_content returning plain bytes must still be written once."""
        handler = _make_handler(tmp_dir, path="test.txt")
        handler.get_content = MagicMock(return_value=b"data")

        run(StaticFileHandler.get(handler, "test.txt"))

        handler.write.assert_called_once_with(b"data")

    # Block: finally/else in flush loop — second chunk after StreamClosedError
    def test_stream_closed_stops_loop(self, tmp_dir):
        """StreamClosedError on first flush → subsequent chunks must not be written."""

        def gen_chunks():
            yield b"first"
            yield b"second"

        handler = _make_handler(tmp_dir, path="test.txt")
        handler.get_content = MagicMock(return_value=gen_chunks())
        handler.flush = AsyncMock(side_effect=iostream.StreamClosedError)

        run(StaticFileHandler.get(handler, "test.txt"))

        # Only one write before StreamClosedError
        assert handler.write.call_count == 1


# ===========================================================================
# --- Condition Coverage ---
# ===========================================================================

class TestConditionCoverage:

    # Condition: self.absolute_path is None
    def test_absolute_path_none_true(self, tmp_dir):
        # absolute_path is None: True
        handler = _make_handler(tmp_dir)
        handler.validate_absolute_path = lambda root, ap: None
        run(StaticFileHandler.get(handler, "x"))
        handler.set_headers.assert_not_called()

    def test_absolute_path_none_false(self, tmp_dir):
        # absolute_path is None: False (normal path)
        handler = _make_handler(tmp_dir, path="test.txt")
        run(StaticFileHandler.get(handler, "test.txt"))
        handler.set_headers.assert_called_once()

    # Condition: self.should_return_304()
    def test_should_304_true(self, tmp_dir):
        # should_return_304: True
        handler = _make_handler(tmp_dir, path="test.txt", status_304=True)
        run(StaticFileHandler.get(handler, "test.txt"))
        handler.set_status.assert_called_once_with(304)

    def test_should_304_false(self, tmp_dir):
        # should_return_304: False
        handler = _make_handler(tmp_dir, path="test.txt", status_304=False)
        run(StaticFileHandler.get(handler, "test.txt"))
        # 304 must NOT be set
        for call in handler.set_status.call_args_list:
            assert call.args[0] != 304

    # Condition: range_header truthy/falsy
    def test_range_header_truthy(self, tmp_dir):
        # range_header: True (Range header present)
        with patch("tornado.httputil._parse_request_range", return_value=(0, 5)):
            handler = _make_handler(
                tmp_dir, path="test.txt", range_header="bytes=0-4"
            )
            run(StaticFileHandler.get(handler, "test.txt"))
        # A parse attempt occurred (206 or full response depending on size match)
        # Content-Length must be set
        handler.set_header.assert_any_call("Content-Length", 5)

    def test_range_header_falsy(self, tmp_dir):
        # range_header: False (no Range header)
        handler = _make_handler(tmp_dir, path="test.txt")
        run(StaticFileHandler.get(handler, "test.txt"))
        handler.set_header.assert_any_call("Content-Length", 13)

    # Condition: (start is not None and start >= size) or end == 0
    # Sub-expr A: start is not None and start >= size
    # Sub-expr B: end == 0

    def test_start_gte_size_true_end_nonzero(self, tmp_dir):
        # A: True (start=100 >= size=13), B: False (end=200 != 0) → 416
        with patch("tornado.httputil._parse_request_range", return_value=(100, 200)):
            handler = _make_handler(tmp_dir, path="test.txt", range_header="bytes=100-200")
            run(StaticFileHandler.get(handler, "test.txt"))
        handler.set_status.assert_called_with(416)

    def test_start_none_end_zero(self, tmp_dir):
        # A: False (start is None), B: True (end == 0) → 416
        with patch("tornado.httputil._parse_request_range", return_value=(None, 0)):
            handler = _make_handler(tmp_dir, path="test.txt", range_header="bytes=-0")
            run(StaticFileHandler.get(handler, "test.txt"))
        handler.set_status.assert_called_with(416)

    def test_start_lt_size_end_nonzero(self, tmp_dir):
        # A: False (start=0 < 13), B: False (end=5 != 0) → NOT 416
        with patch("tornado.httputil._parse_request_range", return_value=(0, 5)):
            handler = _make_handler(tmp_dir, path="test.txt", range_header="bytes=0-4")
            run(StaticFileHandler.get(handler, "test.txt"))
        for call in handler.set_status.call_args_list:
            assert call.args[0] != 416

    # Condition: start is not None and start < 0
    def test_start_negative_true(self, tmp_dir):
        # start is not None: True, start < 0: True → start adjusted
        with patch("tornado.httputil._parse_request_range", return_value=(-3, None)):
            handler = _make_handler(tmp_dir, path="test.txt", range_header="bytes=-3")
            run(StaticFileHandler.get(handler, "test.txt"))
        # content_length = size - (size + (-3)) = size - (13-3) = 3
        handler.set_header.assert_any_call("Content-Length", 3)

    def test_start_non_negative_false(self, tmp_dir):
        # start < 0: False → no adjustment
        with patch("tornado.httputil._parse_request_range", return_value=(2, 8)):
            handler = _make_handler(tmp_dir, path="test.txt", range_header="bytes=2-7")
            run(StaticFileHandler.get(handler, "test.txt"))
        handler.set_header.assert_any_call("Content-Length", 6)

    # Condition: end is not None and end > size
    def test_end_gt_size_true(self, tmp_dir):
        # end > size: True → end capped at 13, full file, no 206
        with patch("tornado.httputil._parse_request_range", return_value=(0, 9999)):
            handler = _make_handler(tmp_dir, path="test.txt", range_header="bytes=0-9998")
            run(StaticFileHandler.get(handler, "test.txt"))
        handler.set_header.assert_any_call("Content-Length", 13)

    def test_end_lte_size_false(self, tmp_dir):
        # end > size: False → end kept
        with patch("tornado.httputil._parse_request_range", return_value=(0, 5)):
            handler = _make_handler(tmp_dir, path="test.txt", range_header="bytes=0-4")
            run(StaticFileHandler.get(handler, "test.txt"))
        handler.set_header.assert_any_call("Content-Length", 5)

    # Condition: size != (end or size) - (start or 0) → 206
    def test_partial_range_206_condition_true(self, tmp_dir):
        # 13 != (8 or 13) - (0 or 0) = 8 → True → 206
        with patch("tornado.httputil._parse_request_range", return_value=(0, 8)):
            handler = _make_handler(tmp_dir, path="test.txt", range_header="bytes=0-7")
            run(StaticFileHandler.get(handler, "test.txt"))
        handler.set_status.assert_called_with(206)

    def test_full_range_206_condition_false(self, tmp_dir):
        # 13 != (None or 13) - (0 or 0) = 13 → False → no 206
        with patch("tornado.httputil._parse_request_range", return_value=(0, None)):
            handler = _make_handler(tmp_dir, path="test.txt", range_header="bytes=0-")
            run(StaticFileHandler.get(handler, "test.txt"))
        for call in handler.set_status.call_args_list:
            assert call.args[0] != 206

    # Condition: isinstance(content, bytes)
    def test_content_is_bytes_true(self, tmp_dir):
        # isinstance(content, bytes): True → wrapped in list
        handler = _make_handler(tmp_dir, path="test.txt")
        handler.get_content = MagicMock(return_value=b"abc")
        run(StaticFileHandler.get(handler, "test.txt"))
        handler.write.assert_called_once_with(b"abc")

    def test_content_is_bytes_false(self, tmp_dir):
        # isinstance(content, bytes): False → iterated directly
        handler = _make_handler(tmp_dir, path="test.txt")
        handler.get_content = MagicMock(return_value=iter([b"part1", b"part2"]))
        run(StaticFileHandler.get(handler, "test.txt"))
        assert handler.write.call_count == 2

    # Condition: include_body
    def test_include_body_true(self, tmp_dir):
        # include_body: True → write called
        handler = _make_handler(tmp_dir, path="test.txt")
        run(StaticFileHandler.get(handler, "test.txt", include_body=True))
        handler.write.assert_called()

    def test_include_body_false(self, tmp_dir):
        # include_body: False → write NOT called
        handler = _make_handler(tmp_dir, path="test.txt", method="HEAD")
        run(StaticFileHandler.get(handler, "test.txt", include_body=False))
        handler.write.assert_not_called()


# ===========================================================================
# --- Path Coverage ---
# ===========================================================================

class TestPathCoverage:

    def test_path_early_return_none(self, tmp_dir):
        """
        Path: validate_absolute_path → None → early return.
        # path: validate→None → return
        """
        handler = _make_handler(tmp_dir)
        handler.validate_absolute_path = lambda root, ap: None
        run(StaticFileHandler.get(handler, "x"))
        handler.set_headers.assert_not_called()
        handler.write.assert_not_called()

    def test_path_304_return(self, tmp_dir):
        """
        Path: validate→ok → 304 → return.
        # path: validate→ok → should_return_304→True → return
        """
        handler = _make_handler(tmp_dir, path="test.txt", status_304=True)
        run(StaticFileHandler.get(handler, "test.txt"))
        handler.set_status.assert_called_once_with(304)
        handler.write.assert_not_called()

    def test_path_no_range_full_body(self, tmp_dir):
        """
        Path: validate→ok → no-304 → no-range → full body → write all.
        # path: validate→ok → 304→False → no-range → include_body→True → write
        """
        handler = _make_handler(tmp_dir, path="test.txt")
        run(StaticFileHandler.get(handler, "test.txt"))
        handler.write.assert_called()
        handler.set_header.assert_any_call("Content-Length", 13)

    def test_path_range_416_start_gte_size(self, tmp_dir):
        """
        Path: validate→ok → no-304 → range parsed → start≥size → 416 → return.
        # path: validate→ok → 304→False → range→True → 416(start≥size) → return
        """
        with patch("tornado.httputil._parse_request_range", return_value=(50, 100)):
            handler = _make_handler(tmp_dir, path="test.txt", range_header="bytes=50-100")
            run(StaticFileHandler.get(handler, "test.txt"))
        handler.set_status.assert_called_with(416)
        handler.write.assert_not_called()

    def test_path_range_416_end_zero(self, tmp_dir):
        """
        Path: validate→ok → no-304 → range parsed → end==0 → 416 → return.
        # path: validate→ok → 304→False → range→True → 416(end==0) → return
        """
        with patch("tornado.httputil._parse_request_range", return_value=(None, 0)):
            handler = _make_handler(tmp_dir, path="test.txt", range_header="bytes=-0")
            run(StaticFileHandler.get(handler, "test.txt"))
        handler.set_status.assert_called_with(416)

    def test_path_range_206_partial(self, tmp_dir):
        """
        Path: valid range → partial (206) → write.
        # path: validate→ok → 304→False → range→True → satisfiable → 206 → write
        """
        with patch("tornado.httputil._parse_request_range", return_value=(2, 7)):
            handler = _make_handler(tmp_dir, path="test.txt", range_header="bytes=2-6")
            handler.get_content = MagicMock(return_value=b"lo, W")
            run(StaticFileHandler.get(handler, "test.txt"))
        handler.set_status.assert_called_with(206)
        handler.write.assert_called()

    def test_path_range_full_no_206(self, tmp_dir):
        """
        Path: range parsed but encompasses entire file → no 206 → write full body.
        # path: validate→ok → 304→False → range→True → size==(end or size)-(start or 0) → no-206 → write
        """
        with patch("tornado.httputil._parse_request_range", return_value=(0, None)):
            handler = _make_handler(tmp_dir, path="test.txt", range_header="bytes=0-")
            run(StaticFileHandler.get(handler, "test.txt"))
        for call in handler.set_status.call_args_list:
            assert call.args[0] not in (206, 416)
        handler.write.assert_called()

    def test_path_stream_closed_mid_loop(self, tmp_dir):
        """
        Path: write chunk → flush raises StreamClosedError → return inside loop.
        # path: validate→ok → 304→False → no-range → include_body→True → write → StreamClosedError → return
        """
        handler = _make_handler(tmp_dir, path="test.txt")
        handler.get_content = MagicMock(return_value=iter([b"a", b"b", b"c"]))
        handler.flush = AsyncMock(side_effect=iostream.StreamClosedError)

        run(StaticFileHandler.get(handler, "test.txt"))

        # Exactly one write; remaining chunks skipped
        assert handler.write.call_count == 1

    def test_path_head_request_no_body(self, tmp_dir):
        """
        Path: include_body=False → assert HEAD → no write.
        # path: validate→ok → 304→False → no-range → include_body→False → no write
        """
        handler = _make_handler(tmp_dir, path="test.txt", method="HEAD")
        run(StaticFileHandler.get(handler, "test.txt", include_body=False))
        handler.write.assert_not_called()

    def test_path_range_negative_start_adjusted(self, tmp_dir):
        """
        Path: range parsed → start < 0 → adjusted → partial check → write.
        # path: validate→ok → 304→False → range→True → satisfiable → start<0→adjusted → 206 check → write
        """
        with patch("tornado.httputil._parse_request_range", return_value=(-3, None)):
            handler = _make_handler(tmp_dir, path="test.txt", range_header="bytes=-3")
            run(StaticFileHandler.get(handler, "test.txt"))
        # Correct: content_length = size - (size-3) = 3
        handler.set_header.assert_any_call("Content-Length", 3)

    def test_path_range_end_capped_full_file(self, tmp_dir):
        """
        Path: end > size → capped → no 206 (full file effectively) → write all.
        # path: validate→ok → 304→False → range→True → satisfiable → end>size→capped → no-206 → write
        """
        with patch("tornado.httputil._parse_request_range", return_value=(0, 9999)):
            handler = _make_handler(tmp_dir, path="test.txt", range_header="bytes=0-9998")
            run(StaticFileHandler.get(handler, "test.txt"))
        handler.set_header.assert_any_call("Content-Length", 13)
        for call in handler.set_status.call_args_list:
            assert call.args[0] != 206

    def test_path_multiple_chunks_written(self, tmp_dir):
        """
        Path: content is a generator with multiple chunks → all chunks written.
        # path: validate→ok → 304→False → no-range → include_body→True → loop 3 iters → done
        """
        chunks = [b"aaa", b"bbb", b"ccc"]

        handler = _make_handler(tmp_dir, path="test.txt")
        handler.get_content = MagicMock(return_value=iter(chunks))

        run(StaticFileHandler.get(handler, "test.txt"))

        assert handler.write.call_count == 3
        written = [call.args[0] for call in handler.write.call_args_list]
        assert written == chunks