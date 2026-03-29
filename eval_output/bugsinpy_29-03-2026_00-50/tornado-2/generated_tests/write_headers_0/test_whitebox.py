import asyncio
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from tornado.http1connection import HTTP1Connection
from tornado import httputil, iostream
from tornado.concurrent import Future


# ---------------------------------------------------------------------------
# Helpers to build a minimal HTTP1Connection-like object without real I/O
# ---------------------------------------------------------------------------

def _make_mock_stream(closed=False):
    stream = MagicMock()
    stream.closed.return_value = closed
    write_future = Future()
    write_future.set_result(None)
    stream.write.return_value = write_future
    return stream


def _make_connection(is_client=True, stream_closed=False,
                     request_version="HTTP/1.1",
                     request_method="GET",
                     disconnect_on_finish=False,
                     request_connection_header=""):
    """
    Build a real HTTP1Connection with just enough state patched in for
    write_headers to run without a real socket.
    """
    conn = HTTP1Connection.__new__(HTTP1Connection)

    # Stream
    conn.stream = _make_mock_stream(closed=stream_closed)

    # Flags
    conn.is_client = is_client
    conn._disconnect_on_finish = disconnect_on_finish

    # Primed server-side state
    req_headers = httputil.HTTPHeaders()
    if request_connection_header:
        req_headers["Connection"] = request_connection_header

    conn._request_headers = req_headers
    conn._request_start_line = httputil.RequestStartLine(
        method=request_method, path="/", version=request_version
    )

    # Future placeholders
    conn._write_future = None
    conn._pending_write = None
    conn._expected_content_remaining = None
    conn._chunking_output = False

    # _format_chunk: produce a minimal chunked encoding
    def _format_chunk(chunk):
        return ("%x\r\n" % len(chunk)).encode("latin1") + chunk + b"\r\n"
    conn._format_chunk = _format_chunk

    # _on_write_complete: no-op
    conn._on_write_complete = MagicMock()

    return conn


def _client_start_line(method="GET", path="/"):
    return httputil.RequestStartLine(method=method, path=path, version="HTTP/1.1")


def _response_start_line(code=200, reason="OK"):
    return httputil.ResponseStartLine(version="HTTP/1.1", code=code, reason=reason)


# ---------------------------------------------------------------------------
# --- Statement Coverage ---
# ---------------------------------------------------------------------------

def test_statement_client_get_no_chunking():
    """Client GET: basic lines built, no chunking (method not POST/PUT/PATCH)."""
    conn = _make_connection(is_client=True)
    headers = httputil.HTTPHeaders()
    future = conn.write_headers(_client_start_line("GET"), headers)

    # A correct write_headers SHOULD return a Future
    assert isinstance(future, Future)
    # GET has no body -> chunking SHOULD be False
    assert conn._chunking_output is False
    # Transfer-Encoding SHOULD NOT be set
    assert "Transfer-Encoding" not in headers


def test_statement_client_post_chunking():
    """Client POST without Content-Length/Transfer-Encoding -> chunked."""
    conn = _make_connection(is_client=True)
    headers = httputil.HTTPHeaders()
    conn.write_headers(_client_start_line("POST"), headers)

    # A correct implementation SHOULD enable chunked output for POST without CL
    assert conn._chunking_output is True
    assert headers.get("Transfer-Encoding") == "chunked"


def test_statement_server_response_basic():
    """Server: writes a 200 response start line."""
    conn = _make_connection(is_client=False)
    headers = httputil.HTTPHeaders()
    future = conn.write_headers(_response_start_line(200, "OK"), headers)

    assert isinstance(future, Future)
    assert conn._response_start_line.code == 200


def test_statement_stream_closed_exception():
    """When stream is closed, future carries StreamClosedError."""
    conn = _make_connection(is_client=True, stream_closed=True)
    headers = httputil.HTTPHeaders()
    future = conn.write_headers(_client_start_line("GET"), headers)

    assert isinstance(future, Future)
    assert future.done()
    assert isinstance(future.exception(), iostream.StreamClosedError)


def test_statement_chunk_appended():
    """If a chunk is provided, it is appended to the written data."""
    conn = _make_connection(is_client=True)
    headers = httputil.HTTPHeaders()
    conn.write_headers(_client_start_line("GET"), headers, chunk=b"hello")

    written_data = conn.stream.write.call_args[0][0]
    assert b"hello" in written_data


def test_statement_newline_in_header_raises():
    """A header value containing a newline must raise ValueError."""
    conn = _make_connection(is_client=True)
    headers = httputil.HTTPHeaders()
    # Inject a header with a newline via internal dict to bypass HTTPHeaders guard
    headers._dict["X-Bad"] = ["val\ninjected"]
    headers._as_list["X-Bad"] = ["val\ninjected"]
    with pytest.raises(ValueError, match="Newline in header"):
        conn.write_headers(_client_start_line("GET"), headers)


def test_statement_content_length_sets_expected_remaining():
    """Content-Length header sets _expected_content_remaining."""
    conn = _make_connection(is_client=False)
    headers = httputil.HTTPHeaders({"Content-Length": "42"})
    conn.write_headers(_response_start_line(200), headers)
    assert conn._expected_content_remaining == 42


# ---------------------------------------------------------------------------
# --- Block Coverage ---
# ---------------------------------------------------------------------------

def test_block_client_branch():
    """Exercises the is_client == True block."""
    # Covered by test_statement_client_get_no_chunking; verify request start line stored
    conn = _make_connection(is_client=True)
    headers = httputil.HTTPHeaders()
    conn.write_headers(_client_start_line("PUT"), headers)
    assert conn._request_start_line.method == "PUT"


def test_block_server_branch():
    """Exercises the is_client == False block."""
    conn = _make_connection(is_client=False)
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(200), headers)
    assert conn._response_start_line is not None


def test_block_server_disconnect_on_finish_adds_connection_close():
    """
    Block: HTTP/1.1 server with _disconnect_on_finish=True
    -> headers["Connection"] = "close"
    """
    conn = _make_connection(is_client=False, disconnect_on_finish=True,
                            request_version="HTTP/1.1")
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(200), headers)
    # A correct implementation SHOULD add Connection: close
    assert headers.get("Connection") == "close"


def test_block_server_http10_keep_alive():
    """
    Block: HTTP/1.0 client requested keep-alive
    -> headers["Connection"] = "Keep-Alive"
    """
    conn = _make_connection(is_client=False,
                            request_version="HTTP/1.0",
                            request_connection_header="keep-alive")
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(200), headers)
    # A correct implementation SHOULD echo Keep-Alive for HTTP/1.0 clients
    assert headers.get("Connection") == "Keep-Alive"


def test_block_chunking_sets_transfer_encoding():
    """Block: _chunking_output True -> Transfer-Encoding: chunked added."""
    conn = _make_connection(is_client=True)
    headers = httputil.HTTPHeaders()
    conn.write_headers(_client_start_line("POST"), headers)
    assert headers["Transfer-Encoding"] == "chunked"


def test_block_head_request_expected_content_zero():
    """
    Block: HEAD request on server side sets _expected_content_remaining = 0.
    """
    conn = _make_connection(is_client=False, request_method="HEAD")
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(200), headers)
    assert conn._expected_content_remaining == 0


def test_block_304_response_expected_content_zero():
    """
    Block: 304 response sets _expected_content_remaining = 0
    (condition via start_line.code == 304).
    """
    conn = _make_connection(is_client=False, request_method="GET")
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(304, "Not Modified"), headers)
    assert conn._expected_content_remaining == 0


def test_block_no_content_length_expected_remaining_none():
    """Block: No Content-Length and not HEAD/304 -> _expected_content_remaining is None."""
    conn = _make_connection(is_client=False, request_method="GET")
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(200), headers)
    assert conn._expected_content_remaining is None


def test_block_stream_open_write_called():
    """Block: stream open -> stream.write is called."""
    conn = _make_connection(is_client=True)
    headers = httputil.HTTPHeaders()
    conn.write_headers(_client_start_line("GET"), headers)
    conn.stream.write.assert_called_once()


def test_block_stream_closed_write_not_called():
    """Block: stream closed -> stream.write is NOT called."""
    conn = _make_connection(is_client=True, stream_closed=True)
    headers = httputil.HTTPHeaders()
    conn.write_headers(_client_start_line("GET"), headers)
    conn.stream.write.assert_not_called()


# ---------------------------------------------------------------------------
# --- Condition Coverage ---
# ---------------------------------------------------------------------------

# _chunking_output for CLIENT:
#   start_line.method in ("POST","PUT","PATCH")  [M]
#   "Content-Length" not in headers              [CL]
#   "Transfer-Encoding" not in headers           [TE]

def test_condition_client_chunking_all_true():
    """
    Client chunking: M=True, CL=True (absent), TE=True (absent)
    -> _chunking_output True
    # M: True, CL-absent: True, TE-absent: True
    """
    conn = _make_connection(is_client=True)
    headers = httputil.HTTPHeaders()
    conn.write_headers(_client_start_line("POST"), headers)
    assert conn._chunking_output is True  # M: True, CL: True, TE: True


def test_condition_client_chunking_method_false():
    """
    Client chunking: M=False (GET) -> _chunking_output False
    # M: False
    """
    conn = _make_connection(is_client=True)
    headers = httputil.HTTPHeaders()
    conn.write_headers(_client_start_line("GET"), headers)
    assert conn._chunking_output is False  # M: False


def test_condition_client_chunking_content_length_present():
    """
    Client chunking: M=True, CL=False (present) -> _chunking_output False
    # M: True, CL-absent: False
    """
    conn = _make_connection(is_client=True)
    headers = httputil.HTTPHeaders({"Content-Length": "10"})
    conn.write_headers(_client_start_line("POST"), headers)
    assert conn._chunking_output is False  # M: True, CL: False


def test_condition_client_chunking_transfer_encoding_present():
    """
    Client chunking: M=True, CL=True (absent), TE=False (present) -> _chunking_output False
    # M: True, CL-absent: True, TE-absent: False
    """
    conn = _make_connection(is_client=True)
    headers = httputil.HTTPHeaders({"Transfer-Encoding": "chunked"})
    conn.write_headers(_client_start_line("PUT"), headers)
    assert conn._chunking_output is False  # M: True, CL: True, TE: False


# _chunking_output for SERVER:
#   version == "HTTP/1.1"                       [V]
#   code not in (204, 304)                      [C]
#   code < 100 or code >= 200                   [R]
#   "Content-Length" not in headers             [CL]
#   "Transfer-Encoding" not in headers          [TE]

def test_condition_server_chunking_all_true():
    """
    Server chunking: V=True, C=True, R=True (200 >= 200), CL=True, TE=True
    -> _chunking_output True
    # V: True, C: True, R: True, CL: True, TE: True
    """
    conn = _make_connection(is_client=False, request_version="HTTP/1.1")
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(200), headers)
    assert conn._chunking_output is True


def test_condition_server_chunking_version_false():
    """
    Server chunking: V=False (HTTP/1.0) -> _chunking_output False
    # V: False
    """
    conn = _make_connection(is_client=False, request_version="HTTP/1.0")
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(200), headers)
    assert conn._chunking_output is False


def test_condition_server_chunking_code_204():
    """
    Server chunking: V=True, C=False (204 in excluded set) -> _chunking_output False
    # V: True, C: False
    """
    conn = _make_connection(is_client=False, request_version="HTTP/1.1")
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(204, "No Content"), headers)
    assert conn._chunking_output is False


def test_condition_server_chunking_code_1xx():
    """
    Server chunking: V=True, C=True (not 204/304), R=False (100 in [100,199]) -> False
    # V: True, C: True, R: False
    """
    conn = _make_connection(is_client=False, request_version="HTTP/1.1")
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(100, "Continue"), headers)
    assert conn._chunking_output is False


def test_condition_server_chunking_content_length_present():
    """
    Server chunking: V=True, C=True, R=True, CL=False (present) -> False
    # V: True, C: True, R: True, CL: False
    """
    conn = _make_connection(is_client=False, request_version="HTTP/1.1")
    headers = httputil.HTTPHeaders({"Content-Length": "5"})
    conn.write_headers(_response_start_line(200), headers)
    assert conn._chunking_output is False


def test_condition_server_chunking_transfer_encoding_present():
    """
    Server chunking: V=True, C=True, R=True, CL=True, TE=False (present) -> False
    # V: True, C: True, R: True, CL: True, TE: False
    """
    conn = _make_connection(is_client=False, request_version="HTTP/1.1")
    headers = httputil.HTTPHeaders({"Transfer-Encoding": "identity"})
    conn.write_headers(_response_start_line(200), headers)
    assert conn._chunking_output is False


# disconnect_on_finish condition:
#   version == "HTTP/1.1"   [V]
#   _disconnect_on_finish   [D]

def test_condition_disconnect_v11_d_true():
    """
    disconnect block: V=True, D=True -> Connection: close
    # V: True, D: True
    """
    conn = _make_connection(is_client=False, request_version="HTTP/1.1",
                            disconnect_on_finish=True)
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(200), headers)
    assert headers.get("Connection") == "close"  # V: True, D: True


def test_condition_disconnect_v11_d_false():
    """
    disconnect block: V=True, D=False -> no Connection: close added
    # V: True, D: False
    """
    conn = _make_connection(is_client=False, request_version="HTTP/1.1",
                            disconnect_on_finish=False)
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(200), headers)
    assert headers.get("Connection") != "close"  # V: True, D: False


def test_condition_disconnect_v10_d_true():
    """
    disconnect block: V=False (HTTP/1.0), D=True -> Connection: close NOT set by this branch
    # V: False, D: True
    """
    conn = _make_connection(is_client=False, request_version="HTTP/1.0",
                            disconnect_on_finish=True)
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(200), headers)
    # The HTTP/1.1-specific close-header block should NOT fire for 1.0 clients
    assert headers.get("Connection") != "close"  # V: False, D: True


# keep-alive condition:
#   version == "HTTP/1.0"                                    [V10]
#   Connection header == "keep-alive" (case-insensitive)     [KA]

def test_condition_keepalive_v10_ka_true():
    """
    keep-alive: V10=True, KA=True -> Connection: Keep-Alive
    # V10: True, KA: True
    """
    conn = _make_connection(is_client=False, request_version="HTTP/1.0",
                            request_connection_header="keep-alive")
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(200), headers)
    assert headers.get("Connection") == "Keep-Alive"  # V10: True, KA: True


def test_condition_keepalive_v10_ka_false():
    """
    keep-alive: V10=True, KA=False (no Connection header) -> no Keep-Alive
    # V10: True, KA: False
    """
    conn = _make_connection(is_client=False, request_version="HTTP/1.0",
                            request_connection_header="")
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(200), headers)
    assert headers.get("Connection") != "Keep-Alive"  # V10: True, KA: False


def test_condition_keepalive_v11_ka_true():
    """
    keep-alive: V10=False (HTTP/1.1), KA=True -> Keep-Alive block NOT entered
    # V10: False, KA: True
    """
    conn = _make_connection(is_client=False, request_version="HTTP/1.1",
                            request_connection_header="keep-alive")
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(200), headers)
    # Keep-Alive header SHOULD NOT be set for HTTP/1.1 via this branch
    # (Connection: close might be set if disconnect_on_finish, but not Keep-Alive)
    assert headers.get("Connection") != "Keep-Alive"  # V10: False


# HEAD/304 expected_content_remaining condition:
#   not is_client and (method=="HEAD" or code==304)   [HEAD_OR_304]

def test_condition_head_method_true():
    """
    expected_content: not client=True, HEAD=True -> remaining=0
    # not_client: True, HEAD: True
    """
    conn = _make_connection(is_client=False, request_method="HEAD")
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(200), headers)
    assert conn._expected_content_remaining == 0  # HEAD: True


def test_condition_head_method_false_code_304_true():
    """
    expected_content: not client=True, HEAD=False (GET), code==304=True -> remaining=0
    # not_client: True, HEAD: False, code==304: True
    """
    conn = _make_connection(is_client=False, request_method="GET")
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(304, "Not Modified"), headers)
    assert conn._expected_content_remaining == 0  # HEAD: False, 304: True


def test_condition_is_client_skips_head_check():
    """
    expected_content: is_client=True -> HEAD/304 block skipped, falls to Content-Length
    # not_client: False
    """
    conn = _make_connection(is_client=True)
    headers = httputil.HTTPHeaders({"Content-Length": "7"})
    conn.write_headers(_client_start_line("GET"), headers)
    # A correct implementation SHOULD read CL even for client connections
    assert conn._expected_content_remaining == 7  # not_client: False


# ---------------------------------------------------------------------------
# --- Path Coverage ---
# ---------------------------------------------------------------------------

def test_path_client_post_no_cl_no_te_stream_open_no_chunk():
    """
    path: is_client -> POST no CL no TE -> chunking=True -> not HEAD/304 -> no CL ->
          remaining=None -> stream open -> no chunk -> write
    # path: client-branch → chunking-true → no-head-304 → no-CL → stream-open → no-chunk
    """
    conn = _make_connection(is_client=True)
    headers = httputil.HTTPHeaders()
    future = conn.write_headers(_client_start_line("POST"), headers)

    assert isinstance(future, Future)
    assert conn._chunking_output is True
    assert conn._expected_content_remaining is None
    conn.stream.write.assert_called_once()
    written = conn.stream.write.call_args[0][0]
    assert b"chunked" in written


def test_path_client_post_no_cl_no_te_stream_open_with_chunk():
    """
    path: is_client → POST → chunking=True → stream open → chunk provided → write with chunk
    # path: client-branch → chunking-true → stream-open → with-chunk
    """
    conn = _make_connection(is_client=True)
    headers = httputil.HTTPHeaders()
    future = conn.write_headers(_client_start_line("POST"), headers, chunk=b"body")

    assert isinstance(future, Future)
    written = conn.stream.write.call_args[0][0]
    assert b"body" in written


def test_path_client_get_stream_closed():
    """
    path: is_client → GET → chunking=False → stream closed → StreamClosedError future
    # path: client-branch → chunking-false → stream-closed → exception-future
    """
    conn = _make_connection(is_client=True, stream_closed=True)
    headers = httputil.HTTPHeaders()
    future = conn.write_headers(_client_start_line("GET"), headers)

    assert future.done()
    assert isinstance(future.exception(), iostream.StreamClosedError)


def test_path_server_http11_200_no_cl_no_te_stream_open():
    """
    path: server → HTTP/1.1 200 → chunking=True → not HEAD/304 → no CL → remaining=None →
          stream open → write chunked
    # path: server-branch → chunking-true → no-head-304 → no-CL → stream-open
    """
    conn = _make_connection(is_client=False, request_version="HTTP/1.1")
    headers = httputil.HTTPHeaders()
    future = conn.write_headers(_response_start_line(200), headers)

    assert isinstance(future, Future)
    assert conn._chunking_output is True
    assert conn._expected_content_remaining is None
    written = conn.stream.write.call_args[0][0]
    assert b"HTTP/1.1 200 OK" in written
    assert b"Transfer-Encoding: chunked" in written


def test_path_server_http11_200_with_content_length():
    """
    path: server → HTTP/1.1 200 → CL present → chunking=False → remaining=CL value
    # path: server-branch → chunking-false(CL present) → CL-branch → remaining=int
    """
    conn = _make_connection(is_client=False, request_version="HTTP/1.1")
    headers = httputil.HTTPHeaders({"Content-Length": "100"})
    conn.write_headers(_response_start_line(200), headers)

    assert conn._chunking_output is False
    assert conn._expected_content_remaining == 100


def test_path_server_http11_head_request():
    """
    path: server → HTTP/1.1 → HEAD method → remaining=0
    # path: server-branch → HEAD-true → remaining=0
    """
    conn = _make_connection(is_client=False, request_method="HEAD",
                            request_version="HTTP/1.1")
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(200), headers)

    assert conn._expected_content_remaining == 0


def test_path_server_http11_304():
    """
    path: server → 304 → chunking=False (304 excluded) → remaining=0
    # path: server-branch → code=304 → chunking-false → head-or-304=True → remaining=0
    """
    conn = _make_connection(is_client=False, request_version="HTTP/1.1",
                            request_method="GET")
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(304, "Not Modified"), headers)

    assert conn._chunking_output is False
    assert conn._expected_content_remaining == 0


def test_path_server_http11_disconnect_on_finish():
    """
    path: server → HTTP/1.1 → disconnect_on_finish=True → Connection: close added
    # path: server-branch → disconnect-branch-true → Connection:close
    """
    conn = _make_connection(is_client=False, request_version="HTTP/1.1",
                            disconnect_on_finish=True)
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(200), headers)

    assert headers.get("Connection") == "close"
    written = conn.stream.write.call_args[0][0]
    assert b"Connection: close" in written


def test_path_server_http10_keepalive_stream_open():
    """
    path: server → HTTP/1.0 → keep-alive request → Connection:Keep-Alive → stream open → write
    # path: server-branch → http10-keepalive-branch → stream-open
    """
    conn = _make_connection(is_client=False, request_version="HTTP/1.0",
                            request_connection_header="keep-alive")
    headers = httputil.HTTPHeaders()
    future = conn.write_headers(_response_start_line(200), headers)

    assert isinstance(future, Future)
    assert headers.get("Connection") == "Keep-Alive"
    written = conn.stream.write.call_args[0][0]
    assert b"Keep-Alive" in written


def test_path_server_http10_no_keepalive_no_chunking():
    """
    path: server → HTTP/1.0 → no keep-alive → chunking=False → stream open → plain write
    # path: server-branch → http10-no-keepalive → chunking-false → stream-open
    """
    conn = _make_connection(is_client=False, request_version="HTTP/1.0")
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(200), headers)

    assert conn._chunking_output is False
    conn.stream.write.assert_called_once()


def test_path_server_204_no_body():
    """
    path: server → 204 → chunking=False (204 excluded) → not HEAD (GET) → no CL → remaining=None
    # path: server-branch → code=204 → chunking-false → no-head-304 → no-CL → remaining=None
    """
    conn = _make_connection(is_client=False, request_version="HTTP/1.1",
                            request_method="GET")
    headers = httputil.HTTPHeaders()
    conn.write_headers(_response_start_line(204, "No Content"), headers)

    assert conn._chunking_output is False
    # 204 is not 304 and method is not HEAD so expected_content_remaining should be None
    assert conn._expected_content_remaining is None


def test_path_newline_in_header_raises_before_write():
    """
    path: client → header with newline → ValueError raised before stream.write
    # path: client-branch → newline-check-raises
    """
    conn = _make_connection(is_client=True)
    headers = httputil.HTTPHeaders()
    headers._dict["X-Evil"] = ["bad\nvalue"]
    headers._as_list["X-Evil"] = ["bad\nvalue"]

    with pytest.raises(ValueError):
        conn.write_headers(_client_start_line("GET"), headers)

    # stream.write SHOULD NOT have been called
    conn.stream.write.assert_not_called()


def test_path_client_put_with_chunk_stream_open():
    """
    path: client → PUT no CL no TE → chunking=True → stream open → chunk provided
    # path: client-branch → PUT → chunking-true → stream-open → chunk
    """
    conn = _make_connection(is_client=True)
    headers = httputil.HTTPHeaders()
    conn.write_headers(_client_start_line("PUT"), headers, chunk=b"data")

    assert conn._chunking_output is True
    written = conn.stream.write.call_args[0][0]
    assert b"PUT / HTTP/1.1" in written
    assert b"data" in written


def test_path_server_stream_closed():
    """
    path: server → stream closed → StreamClosedError future (no write)
    # path: server-branch → stream-closed → exception-future
    """
    conn = _make_connection(is_client=False, stream_closed=True)
    headers = httputil.HTTPHeaders()
    future = conn.write_headers(_response_start_line(200), headers)

    assert future.done()
    assert isinstance(future.exception(), iostream.StreamClosedError)
    conn.stream.write.assert_not_called()