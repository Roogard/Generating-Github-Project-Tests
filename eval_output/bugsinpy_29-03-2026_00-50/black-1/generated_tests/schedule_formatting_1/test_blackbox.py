import asyncio
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch, call
from concurrent.futures import Executor

from black import schedule_formatting, WriteBack, Mode, Changed

# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

def _make_loop():
    """Return a fresh event loop."""
    loop = asyncio.new_event_loop()
    return loop


def _make_mode():
    return Mode()


def _make_report():
    report = MagicMock()
    report.done = MagicMock()
    report.failed = MagicMock()
    return report


def _run(coro):
    loop = _make_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Shared patching context: disable read_cache / filter_cached / write_cache
# and format_file_in_place so tests are pure unit tests.
# ---------------------------------------------------------------------------

def _patch_all(
    *,
    cached_sources=None,
    format_result=False,  # return value of format_file_in_place
    format_side_effect=None,
):
    """Return a context-manager stack of patches."""
    import contextlib
    stack = contextlib.ExitStack()

    # read_cache → empty cache
    stack.enter_context(patch("black.read_cache", return_value={}))

    # filter_cached → (original_sources, cached_sources)
    if cached_sources is None:
        cached_sources = set()
    stack.enter_context(
        patch(
            "black.filter_cached",
            side_effect=lambda cache, sources: (sources, cached_sources),
        )
    )

    # write_cache → no-op
    stack.enter_context(patch("black.write_cache", return_value=None))

    # format_file_in_place → configurable
    if format_side_effect is not None:
        stack.enter_context(
            patch("black.format_file_in_place", side_effect=format_side_effect)
        )
    else:
        stack.enter_context(
            patch("black.format_file_in_place", return_value=format_result)
        )

    return stack


# ===========================================================================
# --- BVA ---
# ===========================================================================

class TestBVA:
    """Boundary Value Analysis tests."""

    def test_empty_sources_returns_immediately_no_diff(self):
        """BVA: empty set — sources == {} with WriteBack.NO should return without error."""
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with _patch_all():
            try:
                loop.run_until_complete(
                    schedule_formatting(
                        sources=set(),
                        fast=False,
                        write_back=WriteBack.NO,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=executor,
                    )
                )
            finally:
                loop.close()

        # No files → nothing should be reported as done or failed
        report.done.assert_not_called()
        report.failed.assert_not_called()

    def test_single_source_formatted_changed(self):
        """BVA: single-element set, file changed (format_file_in_place returns True)."""
        src = Path("/tmp/single.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with _patch_all(format_result=True):
            try:
                loop.run_until_complete(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.YES,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=executor,
                    )
                )
            finally:
                loop.close()

        report.done.assert_called_once_with(src, Changed.YES)

    def test_single_source_not_changed(self):
        """BVA: single-element set, file unchanged (format_file_in_place returns False)."""
        src = Path("/tmp/unchanged.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with _patch_all(format_result=False):
            try:
                loop.run_until_complete(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.YES,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=executor,
                    )
                )
            finally:
                loop.close()

        report.done.assert_called_once_with(src, Changed.NO)

    def test_all_sources_cached_no_formatting(self):
        """BVA: all sources in cache → formatting not called, all reported CACHED."""
        src1 = Path("/tmp/a.py")
        src2 = Path("/tmp/b.py")
        sources = {src1, src2}
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with _patch_all(cached_sources=sources):
            # filter_cached returns (empty, all_cached) — patch to reflect this
            with patch("black.filter_cached", return_value=(set(), sources)):
                with patch("black.read_cache", return_value={}):
                    with patch("black.write_cache", return_value=None):
                        fmt_mock = MagicMock(return_value=False)
                        with patch("black.format_file_in_place", fmt_mock):
                            try:
                                loop.run_until_complete(
                                    schedule_formatting(
                                        sources=sources,
                                        fast=False,
                                        write_back=WriteBack.YES,
                                        mode=mode,
                                        report=report,
                                        loop=loop,
                                        executor=executor,
                                    )
                                )
                            finally:
                                loop.close()

        # format_file_in_place should NOT have been called for cached files
        fmt_mock.assert_not_called()
        # Each cached file should be reported with Changed.CACHED
        calls = report.done.call_args_list
        reported_srcs = {c[0][0] for c in calls}
        reported_states = {c[0][1] for c in calls}
        assert sources == reported_srcs
        assert reported_states == {Changed.CACHED}

    def test_large_sources_all_reported(self):
        """BVA: large collection (100 sources) — all must be reported exactly once."""
        sources = {Path(f"/tmp/file_{i}.py") for i in range(100)}
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with _patch_all(format_result=False):
            try:
                loop.run_until_complete(
                    schedule_formatting(
                        sources=sources,
                        fast=False,
                        write_back=WriteBack.YES,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=executor,
                    )
                )
            finally:
                loop.close()

        assert report.done.call_count == 100
        # Every source must have been reported
        reported = {c[0][0] for c in report.done.call_args_list}
        assert reported == sources


# ===========================================================================
# --- ECP ---
# ===========================================================================

class TestECP:
    """Equivalence Class Partitioning tests."""

    # Valid class: WriteBack.YES — cache should be updated when no exception
    def test_valid_write_back_yes_caches_sources(self):
        """ECP: write_back=YES → sources_to_cache should be written after formatting."""
        src = Path("/tmp/ecp_yes.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with patch("black.read_cache", return_value={}) as _rc:
            with patch(
                "black.filter_cached",
                side_effect=lambda c, s: (s, set()),
            ):
                with patch("black.write_cache") as wc:
                    with patch("black.format_file_in_place", return_value=True):
                        try:
                            loop.run_until_complete(
                                schedule_formatting(
                                    sources={src},
                                    fast=False,
                                    write_back=WriteBack.YES,
                                    mode=mode,
                                    report=report,
                                    loop=loop,
                                    executor=executor,
                                )
                            )
                        finally:
                            loop.close()

        # A correct implementation SHOULD write cache when write_back is YES
        wc.assert_called_once()
        _args = wc.call_args[0]
        assert src in _args[1]  # sources_to_cache contains the processed file

    # Valid class: WriteBack.NO — cache must NOT be updated
    def test_valid_write_back_no_does_not_cache(self):
        """ECP: write_back=NO → cache should never be written."""
        src = Path("/tmp/ecp_no.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with patch("black.read_cache", return_value={}):
            with patch(
                "black.filter_cached",
                side_effect=lambda c, s: (s, set()),
            ):
                with patch("black.write_cache") as wc:
                    with patch("black.format_file_in_place", return_value=True):
                        try:
                            loop.run_until_complete(
                                schedule_formatting(
                                    sources={src},
                                    fast=False,
                                    write_back=WriteBack.NO,
                                    mode=mode,
                                    report=report,
                                    loop=loop,
                                    executor=executor,
                                )
                            )
                        finally:
                            loop.close()

        wc.assert_not_called()

    # Valid class: WriteBack.CHECK + file unchanged → should cache
    def test_valid_write_back_check_unchanged_caches(self):
        """ECP: write_back=CHECK + Changed.NO → file should be cached."""
        src = Path("/tmp/ecp_check_unchanged.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with patch("black.read_cache", return_value={}):
            with patch(
                "black.filter_cached",
                side_effect=lambda c, s: (s, set()),
            ):
                with patch("black.write_cache") as wc:
                    # format_file_in_place returns False → Changed.NO
                    with patch("black.format_file_in_place", return_value=False):
                        try:
                            loop.run_until_complete(
                                schedule_formatting(
                                    sources={src},
                                    fast=False,
                                    write_back=WriteBack.CHECK,
                                    mode=mode,
                                    report=report,
                                    loop=loop,
                                    executor=executor,
                                )
                            )
                        finally:
                            loop.close()

        # A correct implementation SHOULD cache CHECK+unchanged
        wc.assert_called_once()
        _args = wc.call_args[0]
        assert src in _args[1]

    # Valid class: WriteBack.CHECK + file changed → should NOT cache
    def test_valid_write_back_check_changed_does_not_cache(self):
        """ECP: write_back=CHECK + Changed.YES → file should NOT be cached."""
        src = Path("/tmp/ecp_check_changed.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with patch("black.read_cache", return_value={}):
            with patch(
                "black.filter_cached",
                side_effect=lambda c, s: (s, set()),
            ):
                with patch("black.write_cache") as wc:
                    # format_file_in_place returns True → Changed.YES
                    with patch("black.format_file_in_place", return_value=True):
                        try:
                            loop.run_until_complete(
                                schedule_formatting(
                                    sources={src},
                                    fast=False,
                                    write_back=WriteBack.CHECK,
                                    mode=mode,
                                    report=report,
                                    loop=loop,
                                    executor=executor,
                                )
                            )
                        finally:
                            loop.close()

        wc.assert_not_called()

    # Valid class: WriteBack.DIFF — should use a lock and NOT read/write cache
    def test_valid_write_back_diff_no_cache_read(self):
        """ECP: write_back=DIFF → read_cache must NOT be called."""
        src = Path("/tmp/ecp_diff.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with patch("black.read_cache") as rc:
            with patch("black.write_cache") as wc:
                with patch("black.format_file_in_place", return_value=False):
                    with patch("black.Manager") as mgr_cls:
                        mock_mgr = MagicMock()
                        mock_mgr.Lock.return_value = MagicMock()
                        mgr_cls.return_value = mock_mgr
                        try:
                            loop.run_until_complete(
                                schedule_formatting(
                                    sources={src},
                                    fast=False,
                                    write_back=WriteBack.DIFF,
                                    mode=mode,
                                    report=report,
                                    loop=loop,
                                    executor=executor,
                                )
                            )
                        finally:
                            loop.close()

        rc.assert_not_called()
        wc.assert_not_called()

    # Invalid class: task raises exception → report.failed called
    def test_invalid_task_exception_reports_failed(self):
        """ECP: task raises an exception → report.failed should be called with error message."""
        src = Path("/tmp/ecp_exception.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with _patch_all(format_side_effect=Exception("parse error")):
            try:
                loop.run_until_complete(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.YES,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=executor,
                    )
                )
            finally:
                loop.close()

        report.failed.assert_called_once()
        call_args = report.failed.call_args[0]
        assert call_args[0] == src
        assert "parse error" in call_args[1]

    # Valid class: fast=True vs fast=False — both should succeed
    def test_valid_fast_true_processes_sources(self):
        """ECP: fast=True — a correct implementation processes sources without error."""
        src = Path("/tmp/ecp_fast.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with _patch_all(format_result=False):
            try:
                loop.run_until_complete(
                    schedule_formatting(
                        sources={src},
                        fast=True,
                        write_back=WriteBack.YES,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=executor,
                    )
                )
            finally:
                loop.close()

        report.done.assert_called_once_with(src, Changed.NO)
        report.failed.assert_not_called()

    # Valid class: multiple sources, mix of changed/unchanged
    def test_valid_mixed_changed_and_unchanged(self):
        """ECP: multiple sources, some changed some not — all reported, counts correct."""
        changed_src = Path("/tmp/ecp_mixed_changed.py")
        unchanged_src = Path("/tmp/ecp_mixed_unchanged.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        def fmt_side_effect(src, fast, mode, write_back, lock):
            return src == changed_src

        with _patch_all(format_side_effect=fmt_side_effect):
            try:
                loop.run_until_complete(
                    schedule_formatting(
                        sources={changed_src, unchanged_src},
                        fast=False,
                        write_back=WriteBack.YES,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=executor,
                    )
                )
            finally:
                loop.close()

        assert report.done.call_count == 2
        reported = {c[0][0]: c[0][1] for c in report.done.call_args_list}
        assert reported[changed_src] == Changed.YES
        assert reported[unchanged_src] == Changed.NO


# ===========================================================================
# --- Mutation Detection ---
# ===========================================================================

class TestMutationDetection:
    """Tests designed to catch common mutations in schedule_formatting."""

    def test_mutation_diff_check_negated_cache_read(self):
        """Mutation: `write_back != WriteBack.DIFF` flipped to `==`.
        If mutation present, read_cache would be called for DIFF mode.
        A correct implementation must NOT call read_cache for DIFF.
        """
        src = Path("/tmp/mut_diff.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with patch("black.read_cache") as rc:
            with patch("black.write_cache"):
                with patch("black.format_file_in_place", return_value=False):
                    with patch("black.Manager") as mgr_cls:
                        mock_mgr = MagicMock()
                        mock_mgr.Lock.return_value = MagicMock()
                        mgr_cls.return_value = mock_mgr
                        try:
                            loop.run_until_complete(
                                schedule_formatting(
                                    sources={src},
                                    fast=False,
                                    write_back=WriteBack.DIFF,
                                    mode=mode,
                                    report=report,
                                    loop=loop,
                                    executor=executor,
                                )
                            )
                        finally:
                            loop.close()

        # A correct implementation MUST NOT call read_cache for DIFF
        rc.assert_not_called()

    def test_mutation_diff_check_negated_no_lock_for_non_diff(self):
        """Mutation: lock created for non-DIFF write_back modes.
        A correct implementation should only create a Manager lock for DIFF.
        """
        src = Path("/tmp/mut_no_lock.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with _patch_all(format_result=False):
            with patch("black.Manager") as mgr_cls:
                try:
                    loop.run_until_complete(
                        schedule_formatting(
                            sources={src},
                            fast=False,
                            write_back=WriteBack.YES,
                            mode=mode,
                            report=report,
                            loop=loop,
                            executor=executor,
                        )
                    )
                finally:
                    loop.close()

        # Manager should NOT be instantiated for non-DIFF modes
        mgr_cls.assert_not_called()

    def test_mutation_changed_yes_vs_no_for_result_true(self):
        """Mutation: `Changed.YES if task.result() else Changed.NO` flipped.
        A correct implementation: True result → Changed.YES.
        """
        src = Path("/tmp/mut_changed.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with _patch_all(format_result=True):
            try:
                loop.run_until_complete(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.NO,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=executor,
                    )
                )
            finally:
                loop.close()

        report.done.assert_called_once_with(src, Changed.YES)

    def test_mutation_changed_no_vs_yes_for_result_false(self):
        """Mutation: `Changed.YES if task.result() else Changed.NO` swapped constants.
        A correct implementation: False result → Changed.NO.
        """
        src = Path("/tmp/mut_no_changed.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with _patch_all(format_result=False):
            try:
                loop.run_until_complete(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.NO,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=executor,
                    )
                )
            finally:
                loop.close()

        report.done.assert_called_once_with(src, Changed.NO)

    def test_mutation_write_back_yes_vs_check_for_caching(self):
        """Mutation: `write_back is WriteBack.YES` changed to `WriteBack.NO`.
        A correct implementation caches when write_back=YES.
        """
        src = Path("/tmp/mut_cache_yes.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with patch("black.read_cache", return_value={}):
            with patch("black.filter_cached", side_effect=lambda c, s: (s, set())):
                with patch("black.write_cache") as wc:
                    with patch("black.format_file_in_place", return_value=True):
                        try:
                            loop.run_until_complete(
                                schedule_formatting(
                                    sources={src},
                                    fast=False,
                                    write_back=WriteBack.YES,
                                    mode=mode,
                                    report=report,
                                    loop=loop,
                                    executor=executor,
                                )
                            )
                        finally:
                            loop.close()

        # A correct implementation MUST call write_cache for WriteBack.YES
        wc.assert_called_once()

    def test_mutation_and_vs_or_for_check_caching_condition(self):
        """Mutation: `and` replaced by `or` in caching condition for CHECK mode.
        Condition: write_back is CHECK AND changed is NO → cache.
        If `or` used instead, CHECK+YES would also be cached — this detects that.
        """
        src = Path("/tmp/mut_and_or.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with patch("black.read_cache", return_value={}):
            with patch("black.filter_cached", side_effect=lambda c, s: (s, set())):
                with patch("black.write_cache") as wc:
                    # File was changed (True) → Changed.YES; CHECK+YES → must NOT cache
                    with patch("black.format_file_in_place", return_value=True):
                        try:
                            loop.run_until_complete(
                                schedule_formatting(
                                    sources={src},
                                    fast=False,
                                    write_back=WriteBack.CHECK,
                                    mode=mode,
                                    report=report,
                                    loop=loop,
                                    executor=executor,
                                )
                            )
                        finally:
                            loop.close()

        # A correct implementation MUST NOT cache CHECK+YES
        wc.assert_not_called()

    def test_mutation_early_return_missing_for_empty_sources(self):
        """Mutation: `if not sources: return` removed.
        Without early return, an empty sources set would still try to process tasks.
        Detecting: report.done must be 0 calls even if cached sources were present.
        """
        src = Path("/tmp/mut_early_return.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        # Patch: all sources are cached, none remain after filter
        with patch("black.read_cache", return_value={}):
            with patch("black.filter_cached", return_value=(set(), {src})):
                with patch("black.write_cache"):
                    with patch("black.format_file_in_place", return_value=False) as fmt:
                        try:
                            loop.run_until_complete(
                                schedule_formatting(
                                    sources={src},
                                    fast=False,
                                    write_back=WriteBack.YES,
                                    mode=mode,
                                    report=report,
                                    loop=loop,
                                    executor=executor,
                                )
                            )
                        finally:
                            loop.close()

        # format_file_in_place should NOT be called when sources is empty after filtering
        fmt.assert_not_called()

    def test_mutation_exception_check_not_vs_is(self):
        """Mutation: `task.exception()` check condition negated (truthy→falsy).
        A correct implementation: when exception present → report.failed; no done.
        """
        src = Path("/tmp/mut_exc.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with _patch_all(format_side_effect=RuntimeError("boom")):
            try:
                loop.run_until_complete(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.YES,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=executor,
                    )
                )
            finally:
                loop.close()

        # A correct implementation MUST report failure, not success
        report.failed.assert_called_once()
        report.done.assert_not_called()

    def test_mutation_cached_reported_with_cached_not_yes(self):
        """Mutation: report.done(src, Changed.YES) instead of Changed.CACHED for cached sources.
        A correct implementation reports cached files with Changed.CACHED.
        """
        src = Path("/tmp/mut_cache_report.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with patch("black.read_cache", return_value={}):
            with patch("black.filter_cached", return_value=(set(), {src})):
                with patch("black.write_cache"):
                    with patch("black.format_file_in_place", return_value=False):
                        try:
                            loop.run_until_complete(
                                schedule_formatting(
                                    sources={src},
                                    fast=False,
                                    write_back=WriteBack.YES,
                                    mode=mode,
                                    report=report,
                                    loop=loop,
                                    executor=executor,
                                )
                            )
                        finally:
                            loop.close()

        # The cached file must be reported as CACHED, not YES or NO
        report.done.assert_called_once_with(src, Changed.CACHED)

    def test_mutation_write_cache_not_called_when_no_sources_to_cache(self):
        """Mutation: write_cache called unconditionally vs only when sources_to_cache.
        A correct implementation only calls write_cache if sources_to_cache is non-empty.
        """
        src = Path("/tmp/mut_wc_empty.py")
        report = _make_report()
        loop = _make_loop()
        executor = MagicMock(spec=Executor)
        mode = _make_mode()

        with patch("black.read_cache", return_value={}):
            with patch("black.filter_cached", side_effect=lambda c, s: (s, set())):
                with patch("black.write_cache") as wc:
                    # write_back=NO ensures nothing is ever added to sources_to_cache
                    with patch("black.format_file_in_place", return_value=True):
                        try:
                            loop.run_until_complete(
                                schedule_formatting(
                                    sources={src},
                                    fast=False,
                                    write_back=WriteBack.NO,
                                    mode=mode,
                                    report=report,
                                    loop=loop,
                                    executor=executor,
                                )
                            )
                        finally:
                            loop.close()

        # A correct implementation MUST NOT call write_cache when sources_to_cache is empty
        wc.assert_not_called()