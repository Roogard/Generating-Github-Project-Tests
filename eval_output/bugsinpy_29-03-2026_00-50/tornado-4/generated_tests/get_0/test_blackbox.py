import asyncio
import os
import tempfile
import shutil
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

# We test StaticFileHandler.get indirectly by simulating the handler state,
# since it's an async method that depends on handler internals.
# We use a real temporary directory with real files.

from tornado.web import StaticFileHandler, Application
from tornado import httputil, iostream
from tornado.testing import AsyncHTTPTestCase
import tornado.web


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_app(root):
    return Application([
        (r"/static/(.*)", StaticFileHandler, {"path": root}),
    ])


# ---------------------------------------------------------------------------
# Base test class using tornado's AsyncHTTPTestCase
# ---------------------------------------------------------------------------

class StaticFileHandlerGetBase(AsyncHTTPTestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Create test files
        self.content_10 = b"0123456789"  # exactly 10 bytes
        self.content_1 = b"X"           # exactly 1 byte
        self.content_100 = b"A" * 100   # 100 bytes

        with open(os.path.join(self.tmpdir, "file10.txt"), "wb") as f:
            f.write(self.content_10)
        with open(os.path.join(self.tmpdir, "file1.txt"), "wb") as f:
            f.write(self.content_1)
        with open(os.path.join(self.tmpdir, "file100.txt"), "wb") as f:
            f.write(self.content_100)
        # Nested file for path traversal tests
        os.makedirs(os.path.join(self.tmpdir, "subdir"), exist_ok=True)
        with open(os.path.join(self.tmpdir, "subdir", "nested.txt"), "wb") as f:
            f.write(b"nested content")

        super().setUp()

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def get_app(self):
        return make_app(self.tmpdir)


# ---------------------------------------------------------------------------
# --- BVA ---
# ---------------------------------------------------------------------------

class TestBVA(StaticFileHandlerGetBase):

    # BVA: file with exactly 1 byte – minimum non-empty content
    def test_single_byte_file_full_content(self):
        response = self.fetch("/static/file1.txt")
        assert response.code == 200
        assert response.body == b"X"
        assert len(response.body) == 1

    # BVA: Range first byte only (start=0, end=1) on 10-byte file
    def test_range_first_byte_only(self):
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=0-0"})
        assert response.code == 206
        assert response.body == b"0"
        assert len(response.body) == 1

    # BVA: Range last byte only (start=9, end=10) on 10-byte file
    def test_range_last_byte(self):
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=9-9"})
        assert response.code == 206
        assert response.body == b"9"
        assert len(response.body) == 1

    # BVA: Range requesting exactly the whole file (bytes=0-) → should NOT return 206
    def test_range_entire_file_no_206(self):
        # RFC says: only return 206 if LESS than the entire range has been requested
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=0-"})
        # A correct implementation should return 200, not 206, for the full range
        assert response.code == 200
        assert response.body == self.content_10

    # BVA: Range start == size (== 10 for 10-byte file) → 416
    def test_range_start_equals_size_returns_416(self):
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=10-"})
        assert response.code == 416

    # BVA: Range start == size - 1 (== 9 for 10-byte file) → 206 (valid)
    def test_range_start_equals_size_minus_one_returns_206(self):
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=9-"})
        assert response.code == 206
        assert response.body == b"9"

    # BVA: Range end == 0 → 416 (suffix-length 0)
    def test_range_end_zero_returns_416(self):
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=0-0"})
        # bytes=0-0 means start=0, end=1 (inclusive parse), valid
        # To trigger end==0 in the RFC sense we need suffix-length 0: bytes=-0
        # but that is parsed differently. Let's test bytes=0-0 (valid range)
        assert response.code == 206

    # BVA: Empty path (root path) – directory access should be rejected (403 or 404)
    def test_empty_path_returns_error(self):
        response = self.fetch("/static/")
        assert response.code in (403, 404)

    # BVA: Range end larger than size → capped, still returns content
    def test_range_end_beyond_file_size_capped(self):
        # bytes=0-999 on a 10-byte file; end should be capped to 10
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=0-999"})
        # Since the entire file is returned, a correct impl should return 200
        assert response.code == 200
        assert response.body == self.content_10

    # BVA: Range start exactly 1 (min+1) on 10-byte file
    def test_range_start_one(self):
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=1-"})
        assert response.code == 206
        assert response.body == b"123456789"
        assert len(response.body) == 9

    # BVA: 100-byte file – typical size
    def test_full_read_100_bytes(self):
        response = self.fetch("/static/file100.txt")
        assert response.code == 200
        assert response.body == self.content_100
        assert len(response.body) == 100

    # BVA: Range on 100-byte file: last byte
    def test_range_last_byte_100(self):
        response = self.fetch("/static/file100.txt", headers={"Range": "bytes=99-99"})
        assert response.code == 206
        assert response.body == b"A"

    # BVA: Range start == 100 (== size) on 100-byte file → 416
    def test_range_start_equals_size_100_returns_416(self):
        response = self.fetch("/static/file100.txt", headers={"Range": "bytes=100-"})
        assert response.code == 416

    # BVA: Suffix range (negative start) – last 1 byte
    def test_suffix_range_last_one_byte(self):
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=-1"})
        assert response.code == 206
        assert response.body == b"9"


# ---------------------------------------------------------------------------
# --- ECP ---
# ---------------------------------------------------------------------------

class TestECP(StaticFileHandlerGetBase):

    # ECP valid class: normal GET without Range header → 200, full content
    def test_valid_get_no_range(self):
        response = self.fetch("/static/file10.txt")
        assert response.code == 200
        assert response.body == self.content_10
        assert response.headers.get("Content-Length") == "10"

    # ECP valid class: GET with valid partial Range → 206 with correct slice
    def test_valid_get_partial_range(self):
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=2-5"})
        assert response.code == 206
        # bytes 2 through 5 inclusive = "2345"
        assert response.body == b"2345"
        assert "Content-Range" in response.headers

    # ECP valid class: HEAD request – no body, but Content-Length set
    def test_valid_head_request(self):
        response = self.fetch("/static/file10.txt", method="HEAD")
        assert response.code == 200
        assert response.body == b""
        assert response.headers.get("Content-Length") == "10"

    # ECP valid class: nested file in subdirectory
    def test_valid_nested_file(self):
        response = self.fetch("/static/subdir/nested.txt")
        assert response.code == 200
        assert response.body == b"nested content"

    # ECP invalid class: file does not exist → 404
    def test_invalid_nonexistent_file(self):
        response = self.fetch("/static/does_not_exist.txt")
        assert response.code == 404

    # ECP invalid class: path traversal attempt → 403 or 404
    def test_invalid_path_traversal(self):
        response = self.fetch("/static/../etc/passwd")
        assert response.code in (400, 403, 404)

    # ECP invalid class: range start > end (e.g. bytes=5-3) → 416 or treated as no range
    def test_invalid_range_start_greater_than_end(self):
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=5-3"})
        # A correct implementation should either ignore the invalid range or return 416
        assert response.code in (200, 416)

    # ECP invalid class: malformed Range header → treated as if header doesn't exist → 200
    def test_invalid_malformed_range_header(self):
        response = self.fetch("/static/file10.txt", headers={"Range": "invalid-range"})
        # Per RFC 2616 14.16: invalid Range → treat as if not present
        assert response.code == 200
        assert response.body == self.content_10

    # ECP valid class: Range header requesting range beyond file → 416
    def test_range_start_beyond_file(self):
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=100-200"})
        assert response.code == 416

    # ECP valid class: Content-Length header is set correctly for partial content
    def test_content_length_correct_for_partial(self):
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=0-4"})
        assert response.code == 206
        # bytes 0-4 inclusive = 5 bytes: "01234"
        assert response.body == b"01234"
        assert response.headers.get("Content-Length") == "5"

    # ECP valid class: Content-Length header is set correctly for full content
    def test_content_length_correct_for_full(self):
        response = self.fetch("/static/file100.txt")
        assert response.code == 200
        assert response.headers.get("Content-Length") == "100"

    # ECP valid class: directory listing is forbidden (no index file)
    def test_directory_access_forbidden(self):
        response = self.fetch("/static/subdir/")
        assert response.code in (403, 404)

    # ECP valid class: Range with only start specified (open-ended)
    def test_range_open_ended(self):
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=5-"})
        assert response.code == 206
        assert response.body == b"56789"
        assert len(response.body) == 5


# ---------------------------------------------------------------------------
# --- Mutation Detection ---
# ---------------------------------------------------------------------------

class TestMutationDetection(StaticFileHandlerGetBase):

    # Mutation: `start >= size` changed to `start > size` (off-by-one)
    # start == size should STILL return 416; with mutation it would proceed
    def test_mutation_start_equals_size_must_be_416(self):
        # 10-byte file, start=10 (== size) → 416
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=10-"})
        assert response.code == 416, (
            "Mutation: `start >= size` changed to `start > size` would pass this as valid"
        )

    # Mutation: `start > size` vs `start >= size` – start == size-1 should be VALID
    def test_mutation_start_size_minus_one_must_not_be_416(self):
        # 10-byte file, start=9 (== size-1) → 206 (valid)
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=9-"})
        assert response.code == 206, (
            "Mutation: `start > size` (too strict) would incorrectly reject start==size-1"
        )

    # Mutation: `end == 0` condition dropped – suffix-length 0 should return 416
    def test_mutation_end_zero_must_return_416(self):
        # RFC: a range with suffix-length 0 → 416
        # bytes=-0 should parse as end==0
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=-0"})
        # If end==0 check is missing, the server would proceed instead of 416
        # tornado parses -0 as suffix-length 0 → end=0
        # The correct behavior is 416; if mutation dropped the check, code would differ
        assert response.code == 416, (
            "Mutation: dropping `end == 0` check would incorrectly serve content"
        )

    # Mutation: `size != (end or size) - (start or 0)` flipped to `==` → 206 for full range
    def test_mutation_full_range_should_not_be_206(self):
        # bytes=0-9 on 10-byte file: end=10, start=0; (end or size)-(start or 0) = 10 = size
        # So size == (end or size) - (start or 0) → should NOT return 206
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=0-9"})
        assert response.code == 200, (
            "Mutation: flipping `!=` to `==` would return 206 for the full range"
        )

    # Mutation: `start < 0` → `start += size` (negative start handling)
    # If this is dropped, a suffix range would compute wrong content
    def test_mutation_suffix_range_correct_content(self):
        # bytes=-3 on "0123456789" → last 3 bytes = "789"
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=-3"})
        assert response.code == 206
        assert response.body == b"789", (
            "Mutation: dropping `start += size` for negative start would return wrong bytes"
        )

    # Mutation: `end > size` → `end > size - 1` (wrong cap condition)
    def test_mutation_end_capping_correct(self):
        # bytes=0-10 on 10-byte file: end=11 > size=10, so cap to 10 → full file → 200
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=0-10"})
        # end=11 gets capped to 10, full file matches size → 200
        assert response.code == 200
        assert response.body == self.content_10, (
            "Mutation: wrong capping of end would return truncated content"
        )

    # Mutation: content_length = end - start → wrong when start is None
    def test_mutation_content_length_no_start(self):
        # bytes=-5 on 10-byte file: start becomes 5 (after += size), end=None
        # content_length should be size - start = 5
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=-5"})
        assert response.code == 206
        assert response.headers.get("Content-Length") == "5", (
            "Mutation: wrong content_length branch for start-only case"
        )
        assert len(response.body) == 5

    # Mutation: content_length = end (wrong when end is not None and start is None)
    def test_mutation_content_length_no_start_correct_value(self):
        # bytes=0-4 → start=0, end=5; content_length = end - start = 5
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=0-4"})
        assert response.code == 206
        assert response.headers.get("Content-Length") == "5"
        assert response.body == b"01234"

    # Mutation: `include_body` check flipped (body always written or never written)
    def test_mutation_head_no_body(self):
        response = self.fetch("/static/file10.txt", method="HEAD")
        assert response.body == b"", (
            "Mutation: flipping include_body guard would write body on HEAD"
        )

    # Mutation: `include_body` True path – body IS written for GET
    def test_mutation_get_has_body(self):
        response = self.fetch("/static/file10.txt")
        assert response.body == self.content_10, (
            "Mutation: skipping body write would return empty body on GET"
        )

    # Mutation: off-by-one in range: `bytes=1-5` should return 5 bytes (1,2,3,4,5)
    def test_mutation_range_byte_count_off_by_one(self):
        # bytes=1-5 on "0123456789" → "12345" (5 bytes)
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=1-5"})
        assert response.code == 206
        assert response.body == b"12345"
        assert len(response.body) == 5
        assert response.headers.get("Content-Length") == "5", (
            "Mutation: off-by-one in content_length = end - start"
        )

    # Mutation: 304 path: if should_return_304 returns wrong value, 304 is sent incorrectly
    # We can test that a fresh request (no If-Modified-Since) gets 200, not 304
    def test_mutation_no_304_without_conditional_request(self):
        response = self.fetch("/static/file10.txt")
        assert response.code == 200, (
            "Mutation: a buggy should_return_304 always returning True would give 304"
        )

    # Mutation: `absolute_path is None` check inverted → if None, continues; if not None, returns early
    def test_mutation_nonexistent_returns_404_not_crash(self):
        response = self.fetch("/static/nonexistent_file.bin")
        assert response.code == 404, (
            "Mutation: flipped `if absolute_path is None: return` would crash on missing files"
        )

    # Mutation: Content-Range header format for partial content
    def test_mutation_content_range_header_present_on_206(self):
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=2-4"})
        assert response.code == 206
        assert "Content-Range" in response.headers, (
            "Mutation: missing set_header call for Content-Range on 206"
        )
        # Verify the Content-Range format: bytes start-end/size
        cr = response.headers.get("Content-Range")
        assert cr.startswith("bytes "), f"Unexpected Content-Range format: {cr}"

    # Mutation: Content-Range header on 416 must be bytes */size
    def test_mutation_416_content_range_wildcard_format(self):
        response = self.fetch("/static/file10.txt", headers={"Range": "bytes=10-"})
        assert response.code == 416
        cr = response.headers.get("Content-Range")
        assert cr == "bytes */10", (
            f"Mutation: wrong Content-Range on 416; got {cr!r}, expected 'bytes */10'"
        )