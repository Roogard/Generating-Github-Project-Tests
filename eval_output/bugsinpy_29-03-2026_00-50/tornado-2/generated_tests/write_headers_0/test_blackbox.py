import asyncio
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from tornado.http1connection import HTTP1Connection
from tornado import httputil
from tornado import iostream
from tornado.concurrent import Future


# ---------------------------------------------------------------------------
# Helpers to build a minimal HTTP1Connection without a real socket
# ---------------------------------------------------------------------------

def make_mock_stream(closed=False):
    stream = MagicMock()
    stream.closed.return_value = closed
    write_future = Future()
    write_future.set_result(None)
    stream.write.return_value = write_future
    return stream


def make_connection(is_client=True, stream=None, http_version="HTTP/1.1",
                    disconnect_on_finish=False, request_headers=None):
    """
    Build an HTTP1Connection-like object by manually setting attributes that
    write_headers consults.  We avoid touching the real __init__ (which needs
    a real stream / params) by constructing a bare instance and monkey-patching.
    """
    conn = object.__new__(HTTP1Connection)
    conn.is_client = is_client
    conn.stream = stream or make_mock_stream()
    conn._disconnect_on_finish = disconnect_on_finish
    conn._write_future = None
    conn._pending_write = None
    conn._expected_content_remaining = None
    conn._chunking_output = False

    if is_client:
        conn._request_start_line = None
    else:
        # Server side: we need a stored request start line
        conn._request_start_line = httputil.RequestStartLine(
            "GET", "/", http_version
        )
        conn._request_headers = request_headers or httputil.HTTPHeaders()

    return conn


def make_request_start_line(method="GET", path="/", version="HTTP/1.1"):
    return httputil.RequestStartLine(method, path, version)


def make_response_start_line(version="HTTP/1.1", code=200, reason="OK"):
    return httputil.ResponseStartLine(version, code, reason)


def run(coro_or_future):
    """Run an asyncio coroutine/future synchronously."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro_or_future)
    finally:
        loop.close()


# ===========================================================================
# --- BVA ---
# ===========================================================================

class TestBVA:

    # --- Status codes at boundaries for _chunking_output ---

    def test_status_code_100_no_chunking(self):
        """1xx codes have no body; chunking MUST be False for code=100."""
        conn = make_connection(is_client=False)
        sl = make_response_start_line(code=100, reason="Continue")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        # A correct implementation MUST NOT chunk 1xx responses
        assert conn._chunking_output is False

    def test_status_code_101_no_chunking(self):
        """101 is still 1xx — no chunking."""
        conn = make_connection(is_client=False)
        sl = make_response_start_line(code=101, reason="Switching Protocols")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is False

    def test_status_code_199_no_chunking(self):
        """199 is still 1xx — no chunking."""
        conn = make_connection(is_client=False)
        sl = make_response_start_line(code=199, reason="Whatever")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is False

    def test_status_code_200_chunking_enabled(self):
        """200 is the first non-1xx code that should allow chunking (HTTP/1.1, no Content-Length)."""
        conn = make_connection(is_client=False)
        sl = make_response_start_line(code=200, reason="OK")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is True

    def test_status_code_203_chunking_enabled(self):
        """203 is a normal 2xx code — chunking should be enabled."""
        conn = make_connection(is_client=False)
        sl = make_response_start_line(code=203, reason="Non-Authoritative")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is True

    def test_status_code_204_no_chunking(self):
        """204 No Content MUST NOT be chunked."""
        conn = make_connection(is_client=False)
        sl = make_response_start_line(code=204, reason="No Content")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is False

    def test_status_code_304_no_chunking(self):
        """304 Not Modified MUST NOT be chunked."""
        conn = make_connection(is_client=False)
        sl = make_response_start_line(code=304, reason="Not Modified")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is False

    def test_status_code_305_chunking_enabled(self):
        """305 is a normal redirect — chunking should be enabled."""
        conn = make_connection(is_client=False)
        sl = make_response_start_line(code=305, reason="Use Proxy")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is True

    def test_status_code_500_chunking_enabled(self):
        """500 has a body — chunking should be enabled when no Content-Length."""
        conn = make_connection(is_client=False)
        sl = make_response_start_line(code=500, reason="Internal Server Error")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is True

    # --- Content-Length boundary values ---

    def test_content_length_zero(self):
        """Content-Length: 0 must set _expected_content_remaining to 0."""
        conn = make_connection(is_client=False)
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders({"Content-Length": "0"})
        conn.write_headers(sl, headers)
        assert conn._expected_content_remaining == 0

    def test_content_length_one(self):
        """Content-Length: 1 must set _expected_content_remaining to 1."""
        conn = make_connection(is_client=False)
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders({"Content-Length": "1"})
        conn.write_headers(sl, headers)
        assert conn._expected_content_remaining == 1

    def test_content_length_large(self):
        """Large Content-Length must be stored correctly."""
        conn = make_connection(is_client=False)
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders({"Content-Length": "999999999"})
        conn.write_headers(sl, headers)
        assert conn._expected_content_remaining == 999999999

    # --- Empty headers ---

    def test_empty_headers_client(self):
        """Client request with empty headers should succeed."""
        conn = make_connection(is_client=True)
        sl = make_request_start_line(method="GET", path="/")
        headers = httputil.HTTPHeaders()
        future = conn.write_headers(sl, headers)
        assert future is not None

    def test_empty_headers_server(self):
        """Server response with empty headers should succeed."""
        conn = make_connection(is_client=False)
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders()
        future = conn.write_headers(sl, headers)
        assert future is not None

    # --- chunk parameter boundaries ---

    def test_chunk_none_no_extra_data(self):
        """No chunk means the stream.write is called once with just headers."""
        stream = make_mock_stream()
        conn = make_connection(is_client=True, stream=stream)
        sl = make_request_start_line(method="GET")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers, chunk=None)
        written = stream.write.call_args[0][0]
        # The written data must end with \r\n\r\n and be bytes
        assert isinstance(written, bytes)
        assert written.endswith(b"\r\n\r\n")

    def test_chunk_empty_bytes(self):
        """chunk=b'' is falsy; a correct implementation treats it like no chunk."""
        stream = make_mock_stream()
        conn = make_connection(is_client=True, stream=stream)
        sl = make_request_start_line(method="GET")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers, chunk=b"")
        written = stream.write.call_args[0][0]
        assert isinstance(written, bytes)

    def test_chunk_single_byte(self):
        """chunk=b'x' should be appended (formatted) to the header data."""
        stream = make_mock_stream()
        conn = make_connection(is_client=True, stream=stream)
        sl = make_request_start_line(method="POST")
        headers = httputil.HTTPHeaders({"Content-Length": "1"})
        conn.write_headers(sl, headers, chunk=b"x")
        written = stream.write.call_args[0][0]
        assert b"x" in written

    def test_chunk_large(self):
        """Large chunk should be appended after headers."""
        stream = make_mock_stream()
        conn = make_connection(is_client=True, stream=stream)
        sl = make_request_start_line(method="POST")
        large_body = b"A" * 100_000
        headers = httputil.HTTPHeaders({"Content-Length": str(len(large_body))})
        conn.write_headers(sl, headers, chunk=large_body)
        written = stream.write.call_args[0][0]
        assert large_body in written


# ===========================================================================
# --- ECP ---
# ===========================================================================

class TestECP:

    # --- Valid classes: client vs server side ---

    def test_valid_client_get_request(self):
        """ECP: valid client GET request produces a future and correct start line."""
        conn = make_connection(is_client=True)
        sl = make_request_start_line(method="GET", path="/index.html")
        headers = httputil.HTTPHeaders()
        future = conn.write_headers(sl, headers)
        assert future is not None
        assert conn._request_start_line == sl

    def test_valid_server_200_response(self):
        """ECP: valid server 200 response produces a future."""
        conn = make_connection(is_client=False)
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders()
        future = conn.write_headers(sl, headers)
        assert future is not None
        assert conn._response_start_line == sl

    # --- Chunking decision classes ---

    def test_client_post_no_content_length_chunked(self):
        """ECP: POST without Content-Length or Transfer-Encoding => chunked output."""
        conn = make_connection(is_client=True)
        sl = make_request_start_line(method="POST", path="/submit")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is True
        assert headers.get("Transfer-Encoding") == "chunked"

    def test_client_put_no_content_length_chunked(self):
        """ECP: PUT without Content-Length => chunked."""
        conn = make_connection(is_client=True)
        sl = make_request_start_line(method="PUT", path="/resource")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is True

    def test_client_patch_no_content_length_chunked(self):
        """ECP: PATCH without Content-Length => chunked."""
        conn = make_connection(is_client=True)
        sl = make_request_start_line(method="PATCH", path="/resource")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is True

    def test_client_post_with_content_length_not_chunked(self):
        """ECP: POST with Content-Length => NOT chunked."""
        conn = make_connection(is_client=True)
        sl = make_request_start_line(method="POST", path="/submit")
        headers = httputil.HTTPHeaders({"Content-Length": "42"})
        conn.write_headers(sl, headers)
        assert conn._chunking_output is False

    def test_client_post_with_transfer_encoding_not_chunked(self):
        """ECP: POST with Transfer-Encoding provided => NOT chunked (leave alone)."""
        conn = make_connection(is_client=True)
        sl = make_request_start_line(method="POST")
        headers = httputil.HTTPHeaders({"Transfer-Encoding": "identity"})
        conn.write_headers(sl, headers)
        assert conn._chunking_output is False

    def test_client_get_not_chunked(self):
        """ECP: GET request must not be chunked even without Content-Length."""
        conn = make_connection(is_client=True)
        sl = make_request_start_line(method="GET")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is False

    def test_client_delete_not_chunked(self):
        """ECP: DELETE request must not be chunked."""
        conn = make_connection(is_client=True)
        sl = make_request_start_line(method="DELETE")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is False

    def test_client_head_not_chunked(self):
        """ECP: HEAD request must not be chunked."""
        conn = make_connection(is_client=True)
        sl = make_request_start_line(method="HEAD")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is False

    # --- Server HTTP/1.0 vs HTTP/1.1 ---

    def test_server_http10_request_no_chunking(self):
        """ECP: HTTP/1.0 client => server must not chunk (HTTP/1.0 doesn't support it)."""
        conn = make_connection(is_client=False, http_version="HTTP/1.0")
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is False

    def test_server_http11_request_chunking(self):
        """ECP: HTTP/1.1 client and 200 with no Content-Length => server chunks."""
        conn = make_connection(is_client=False, http_version="HTTP/1.1")
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is True

    # --- Connection header classes ---

    def test_server_http11_disconnect_on_finish_adds_connection_close(self):
        """ECP: HTTP/1.1 client + disconnect_on_finish => Connection: close must be added."""
        conn = make_connection(is_client=False, http_version="HTTP/1.1",
                               disconnect_on_finish=True)
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert headers.get("Connection", "").lower() == "close"

    def test_server_http11_no_disconnect_no_connection_close(self):
        """ECP: HTTP/1.1 client + no disconnect_on_finish => no Connection: close."""
        conn = make_connection(is_client=False, http_version="HTTP/1.1",
                               disconnect_on_finish=False)
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert headers.get("Connection", "").lower() != "close"

    def test_server_http10_keepalive_request_adds_keepalive_header(self):
        """ECP: HTTP/1.0 client with Connection: keep-alive => server adds Keep-Alive header."""
        req_headers = httputil.HTTPHeaders({"Connection": "keep-alive"})
        conn = make_connection(is_client=False, http_version="HTTP/1.0",
                               request_headers=req_headers)
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert headers.get("Connection") == "Keep-Alive"

    def test_server_http10_no_keepalive_no_header(self):
        """ECP: HTTP/1.0 client without keep-alive => no Connection: Keep-Alive."""
        req_headers = httputil.HTTPHeaders()
        conn = make_connection(is_client=False, http_version="HTTP/1.0",
                               request_headers=req_headers)
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert headers.get("Connection", "") != "Keep-Alive"

    # --- expected_content_remaining classes ---

    def test_head_request_sets_expected_content_remaining_zero(self):
        """ECP: HEAD request => _expected_content_remaining must be 0."""
        conn = make_connection(is_client=False, http_version="HTTP/1.1")
        conn._request_start_line = httputil.RequestStartLine("HEAD", "/", "HTTP/1.1")
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._expected_content_remaining == 0

    def test_304_sets_expected_content_remaining_zero(self):
        """ECP: 304 response => _expected_content_remaining must be 0."""
        conn = make_connection(is_client=False, http_version="HTTP/1.1")
        sl = make_response_start_line(code=304)
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._expected_content_remaining == 0

    def test_content_length_sets_expected_content_remaining(self):
        """ECP: Content-Length present => _expected_content_remaining equals it."""
        conn = make_connection(is_client=False)
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders({"Content-Length": "512"})
        conn.write_headers(sl, headers)
        assert conn._expected_content_remaining == 512

    def test_no_content_length_no_head_expected_content_none(self):
        """ECP: no Content-Length, not HEAD, not 304 => _expected_content_remaining is None."""
        conn = make_connection(is_client=False)
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._expected_content_remaining is None

    # --- Stream state classes ---

    def test_closed_stream_returns_future_with_exception(self):
        """ECP: closed stream => returned future must contain StreamClosedError."""
        stream = make_mock_stream(closed=True)
        conn = make_connection(is_client=True, stream=stream)
        sl = make_request_start_line(method="GET")
        headers = httputil.HTTPHeaders()
        future = conn.write_headers(sl, headers)
        assert future.done()
        assert isinstance(future.exception(), iostream.StreamClosedError)

    def test_open_stream_returns_pending_future(self):
        """ECP: open stream => returned future must not already contain an error."""
        stream = make_mock_stream(closed=False)
        conn = make_connection(is_client=True, stream=stream)
        sl = make_request_start_line(method="GET")
        headers = httputil.HTTPHeaders()
        future = conn.write_headers(sl, headers)
        assert future is not None
        # The future should not have a StreamClosedError
        if future.done() and future.exception():
            assert not isinstance(future.exception(), iostream.StreamClosedError)

    # --- Invalid: newline in header ---

    def test_newline_in_header_value_raises_value_error(self):
        """ECP: invalid — newline in header value must raise ValueError."""
        conn = make_connection(is_client=True)
        sl = make_request_start_line(method="GET")
        headers = httputil.HTTPHeaders()
        headers["X-Evil"] = "bad\nvalue"
        with pytest.raises(ValueError, match="Newline in header"):
            conn.write_headers(sl, headers)

    def test_newline_in_header_name_raises_value_error(self):
        """ECP: invalid — newline embedded anywhere in a serialized header line raises ValueError."""
        conn = make_connection(is_client=True)
        sl = make_request_start_line(method="GET")
        headers = httputil.HTTPHeaders()
        # Force a header with \n in the value
        headers.add("X-Test", "value\nX-Injected: injected")
        with pytest.raises(ValueError, match="Newline in header"):
            conn.write_headers(sl, headers)

    # --- Wrong start line type ---

    def test_client_with_response_start_line_raises(self):
        """ECP: invalid — client connection given a ResponseStartLine must raise AssertionError."""
        conn = make_connection(is_client=True)
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders()
        with pytest.raises(AssertionError):
            conn.write_headers(sl, headers)

    def test_server_with_request_start_line_raises(self):
        """ECP: invalid — server connection given a RequestStartLine must raise AssertionError."""
        conn = make_connection(is_client=False)
        sl = make_request_start_line(method="GET")
        headers = httputil.HTTPHeaders()
        with pytest.raises(AssertionError):
            conn.write_headers(sl, headers)


# ===========================================================================
# --- Mutation Detection ---
# ===========================================================================

class TestMutationDetection:

    def test_mutation_post_boundary_method_options_not_chunked(self):
        """
        Mutation: wrong method list (e.g., 'OPTIONS' added or 'POST' dropped).
        OPTIONS must NOT trigger chunked output.
        """
        conn = make_connection(is_client=True)
        sl = make_request_start_line(method="OPTIONS")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is False  # detects mutation that adds OPTIONS

    def test_mutation_post_chunked_post_in_list(self):
        """
        Mutation: 'POST' removed from the method list.
        POST without Content-Length MUST be chunked.
        """
        conn = make_connection(is_client=True)
        sl = make_request_start_line(method="POST")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is True  # detects mutation that removes POST

    def test_mutation_and_vs_or_chunking_all_conditions_must_hold(self):
        """
        Mutation: 'and' replaced with 'or' in server chunking condition.
        With HTTP/1.0, chunking MUST be False even for 200 with no Content-Length.
        (If 'or' were used, one True condition would enable chunking incorrectly.)
        """
        conn = make_connection(is_client=False, http_version="HTTP/1.0")
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is False

    def test_mutation_content_length_check_inverted(self):
        """
        Mutation: 'not in' replaced with 'in' for Content-Length check.
        When Content-Length IS present, chunking MUST be False.
        """
        conn = make_connection(is_client=False, http_version="HTTP/1.1")
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders({"Content-Length": "100"})
        conn.write_headers(sl, headers)
        assert conn._chunking_output is False  # detects inverted condition

    def test_mutation_transfer_encoding_check_inverted(self):
        """
        Mutation: 'not in' replaced with 'in' for Transfer-Encoding check.
        When Transfer-Encoding IS present, chunking MUST be False.
        """
        conn = make_connection(is_client=False, http_version="HTTP/1.1")
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders({"Transfer-Encoding": "identity"})
        conn.write_headers(sl, headers)
        assert conn._chunking_output is False

    def test_mutation_204_boundary_off_by_one_203(self):
        """
        Mutation: 204 replaced with 203 in the exclusion set.
        Code 203 MUST allow chunking; only 204 and 304 are excluded.
        """
        conn = make_connection(is_client=False, http_version="HTTP/1.1")
        sl = make_response_start_line(code=203, reason="Non-Authoritative")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is True  # detects wrong constant (203 instead of 204)

    def test_mutation_204_boundary_off_by_one_205(self):
        """
        Mutation: 204 replaced with 205 in the exclusion set.
        Code 205 MUST allow chunking; only 204 and 304 are excluded.
        """
        conn = make_connection(is_client=False, http_version="HTTP/1.1")
        sl = make_response_start_line(code=205, reason="Reset Content")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is True  # detects wrong constant

    def test_mutation_1xx_upper_bound_lt_vs_lte(self):
        """
        Mutation: '<' replaced with '<=' in `start_line.code < 100`.
        Code 100 MUST NOT be chunked; if mutation changes to <=100, code 101 might pass.
        Verify code 99 isn't accidentally chunked (boundary below 1xx range).
        """
        conn = make_connection(is_client=False, http_version="HTTP/1.1")
        # Code 99 is below 100 — no chunking (not >= 200 either)
        sl = make_response_start_line(code=99, reason="Hypothetical")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is False

    def test_mutation_1xx_lower_boundary_200_vs_199(self):
        """
        Mutation: '>= 200' replaced with '> 200'.
        Code 200 MUST still be chunked — detects off-by-one on the lower 2xx bound.
        """
        conn = make_connection(is_client=False, http_version="HTTP/1.1")
        sl = make_response_start_line(code=200, reason="OK")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is True

    def test_mutation_http_version_wrong_variable(self):
        """
        Mutation: wrong variable used for version check (e.g., start_line.version
        instead of self._request_start_line.version).
        For HTTP/1.0 client, server MUST NOT chunk regardless of response version.
        """
        conn = make_connection(is_client=False, http_version="HTTP/1.0")
        # Response claims HTTP/1.1 but client is HTTP/1.0
        sl = make_response_start_line(version="HTTP/1.1", code=200)
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        # A correct implementation uses _request_start_line.version
        assert conn._chunking_output is False

    def test_mutation_disconnect_on_finish_wrong_boolean(self):
        """
        Mutation: `self._disconnect_on_finish` negated.
        When disconnect_on_finish=False, Connection: close must NOT be added.
        """
        conn = make_connection(is_client=False, http_version="HTTP/1.1",
                               disconnect_on_finish=False)
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert "Connection" not in headers or headers.get("Connection", "").lower() != "close"

    def test_mutation_disconnect_on_finish_true_adds_close(self):
        """
        Mutation: `and` replaced with `or` in disconnect condition.
        When disconnect_on_finish=True AND HTTP/1.1, Connection: close MUST appear.
        """
        conn = make_connection(is_client=False, http_version="HTTP/1.1",
                               disconnect_on_finish=True)
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert headers.get("Connection", "").lower() == "close"

    def test_mutation_keepalive_check_wrong_version_http11(self):
        """
        Mutation: HTTP/1.0 keep-alive check uses HTTP/1.1 instead.
        For HTTP/1.1 client with Connection: keep-alive, we should NOT get Keep-Alive
        header (that logic is only for HTTP/1.0).
        """
        req_headers = httputil.HTTPHeaders({"Connection": "keep-alive"})
        conn = make_connection(is_client=False, http_version="HTTP/1.1",
                               request_headers=req_headers)
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        # Keep-Alive header must NOT be added for HTTP/1.1 clients
        assert headers.get("Connection", "") != "Keep-Alive"

    def test_mutation_head_check_uses_wrong_method(self):
        """
        Mutation: HEAD check replaced with GET or POST.
        GET request should NOT set _expected_content_remaining to 0.
        """
        conn = make_connection(is_client=False, http_version="HTTP/1.1")
        conn._request_start_line = httputil.RequestStartLine("GET", "/", "HTTP/1.1")
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        # For GET + 200, expected_content_remaining should be None (no Content-Length)
        assert conn._expected_content_remaining is None

    def test_mutation_304_check_uses_wrong_code_303(self):
        """
        Mutation: 304 in _expected_content_remaining check replaced with 303.
        303 MUST NOT have _expected_content_remaining set to 0 via that path.
        """
        conn = make_connection(is_client=False, http_version="HTTP/1.1")
        sl = make_response_start_line(code=303, reason="See Other")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        # 303 with no Content-Length should leave _expected_content_remaining as None
        assert conn._expected_content_remaining is None

    def test_mutation_chunked_header_not_added_when_not_chunking(self):
        """
        Mutation: Transfer-Encoding always added regardless of _chunking_output.
        When chunking is False, Transfer-Encoding: chunked must NOT appear.
        """
        conn = make_connection(is_client=True)
        sl = make_request_start_line(method="GET")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is False
        assert headers.get("Transfer-Encoding") != "chunked"

    def test_mutation_chunked_header_added_when_chunking(self):
        """
        Mutation: Transfer-Encoding header addition omitted.
        When _chunking_output is True, the header MUST be set to 'chunked'.
        """
        conn = make_connection(is_client=True)
        sl = make_request_start_line(method="POST")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._chunking_output is True
        assert headers.get("Transfer-Encoding") == "chunked"

    def test_mutation_request_start_line_not_stored_client(self):
        """
        Mutation: _request_start_line assignment omitted in client branch.
        After write_headers, _request_start_line must equal the given start line.
        """
        conn = make_connection(is_client=True)
        sl = make_request_start_line(method="POST", path="/data")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._request_start_line is sl

    def test_mutation_response_start_line_not_stored_server(self):
        """
        Mutation: _response_start_line assignment omitted in server branch.
        After write_headers, _response_start_line must equal the given start line.
        """
        conn = make_connection(is_client=False)
        sl = make_response_start_line(code=201, reason="Created")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        assert conn._response_start_line is sl

    def test_mutation_content_length_int_conversion_missing(self):
        """
        Mutation: int() conversion missing for Content-Length value.
        _expected_content_remaining MUST be an integer, not a string.
        """
        conn = make_connection(is_client=False)
        sl = make_response_start_line(code=200)
        headers = httputil.HTTPHeaders({"Content-Length": "123"})
        conn.write_headers(sl, headers)
        assert isinstance(conn._expected_content_remaining, int)
        assert conn._expected_content_remaining == 123

    def test_mutation_stream_write_called_with_bytes(self):
        """
        Mutation: data encoding skipped, sending str instead of bytes.
        stream.write must be called with bytes.
        """
        stream = make_mock_stream()
        conn = make_connection(is_client=True, stream=stream)
        sl = make_request_start_line(method="GET", path="/")
        headers = httputil.HTTPHeaders({"Accept": "text/html"})
        conn.write_headers(sl, headers)
        call_args = stream.write.call_args
        assert call_args is not None
        data = call_args[0][0]
        assert isinstance(data, bytes)

    def test_mutation_crlf_separator_vs_lf(self):
        """
        Mutation: \\r\\n replaced with \\n as separator.
        HTTP/1.1 requires CRLF line endings; written data must contain \\r\\n.
        """
        stream = make_mock_stream()
        conn = make_connection(is_client=True, stream=stream)
        sl = make_request_start_line(method="GET", path="/")
        headers = httputil.HTTPHeaders({"Accept": "text/html"})
        conn.write_headers(sl, headers)
        data = stream.write.call_args[0][0]
        assert b"\r\n" in data

    def test_mutation_double_crlf_at_end(self):
        """
        Mutation: trailing \\r\\n\\r\\n replaced with \\r\\n.
        HTTP requires a blank line after headers; data must end with \\r\\n\\r\\n.
        """
        stream = make_mock_stream()
        conn = make_connection(is_client=True, stream=stream)
        sl = make_request_start_line(method="GET", path="/")
        headers = httputil.HTTPHeaders()
        conn.write_headers(sl, headers)
        data = stream.write.call_args[0][0]
        # Find the end of the header section (before any optional chunk)
        assert b"\r\n\r\n" in data

    def test_mutation_closed_stream_still_returns_future(self):
        """
        Mutation: exception branch returns None instead of a future.
        Even for a closed stream, a Future must be returned.
        """
        stream = make_mock_stream(closed=True)
        conn = make_connection(is_client=True, stream=stream)
        sl = make_request_start_line(method="GET")
        headers = httputil.HTTPHeaders()
        future = conn.write_headers(sl, headers)
        assert future is not None
        assert isinstance(future, Future)

    def test_mutation_write_future_assigned(self):
        """
        Mutation: _write_future not assigned.
        After write_headers, _write_future must equal the returned future.
        """
        conn = make_connection(is_client=True)
        sl = make_request_start_line(method="GET")
        headers = httputil.HTTPHeaders()
        future = conn.write_headers(sl, headers)
        assert conn._write_future is future