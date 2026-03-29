import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock, call
from typing import Set

import pytest

from black import reformat_many, WriteBack, Mode, Report

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_report() -> MagicMock:
    """Return a minimal mock that satisfies Report's interface."""
    report = MagicMock(spec=Report)
    return report


def _make_mode() -> Mode:
    return Mode()


# A coroutine that immediately returns so schedule_formatting doesn't block.
async def _noop_schedule_formatting(**kwargs):
    return None


# ---------------------------------------------------------------------------
# --- ECP ---
# Equivalence Class Partitioning
# ---------------------------------------------------------------------------

class TestECPEmptySourceSet:
    """ECP valid class: empty source set — no files to reformat."""

    def test_empty_sources_no_exception(self, tmp_path):
        sources: Set[Path] = set()
        report = _make_report()
        mode = _make_mode()

        with patch("black.schedule_formatting", return_value=_noop_schedule_formatting()):
            with patch("black.shutdown") as mock_shutdown:
                # Should complete without raising even if there are no sources.
                reformat_many(
                    sources=sources,
                    fast=False,
                    write_back=WriteBack.NO,
                    mode=mode,
                    report=report,
                )
                mock_shutdown.assert_called_once()


class TestECPSingleSource:
    """ECP valid class: single file in sources."""

    def test_single_source_calls_schedule_formatting(self, tmp_path):
        src = tmp_path / "a.py"
        src.write_text("x = 1\n")
        sources = {src}
        report = _make_report()
        mode = _make_mode()

        captured_kwargs = {}

        async def capture_schedule(**kwargs):
            captured_kwargs.update(kwargs)

        with patch("black.schedule_formatting", side_effect=capture_schedule):
            with patch("black.shutdown"):
                reformat_many(
                    sources=sources,
                    fast=True,
                    write_back=WriteBack.YES,
                    mode=mode,
                    report=report,
                )

        assert captured_kwargs["sources"] == sources
        assert captured_kwargs["fast"] is True
        assert captured_kwargs["write_back"] == WriteBack.YES
        assert captured_kwargs["mode"] is mode
        assert captured_kwargs["report"] is report


class TestECPMultipleSources:
    """ECP valid class: multiple files in sources."""

    def test_multiple_sources_forwarded_correctly(self, tmp_path):
        sources = {tmp_path / f"file{i}.py" for i in range(5)}
        report = _make_report()
        mode = _make_mode()

        captured_kwargs = {}

        async def capture_schedule(**kwargs):
            captured_kwargs.update(kwargs)

        with patch("black.schedule_formatting", side_effect=capture_schedule):
            with patch("black.shutdown"):
                reformat_many(
                    sources=sources,
                    fast=False,
                    write_back=WriteBack.DIFF,
                    mode=mode,
                    report=report,
                )

        assert captured_kwargs["sources"] == sources


class TestECPWriteBackVariants:
    """ECP: different WriteBack enum values are all forwarded unchanged."""

    @pytest.mark.parametrize("wb", list(WriteBack))
    def test_write_back_forwarded(self, tmp_path, wb):
        src = tmp_path / "x.py"
        src.write_text("pass\n")
        sources = {src}
        report = _make_report()
        mode = _make_mode()

        captured_kwargs = {}

        async def capture_schedule(**kwargs):
            captured_kwargs.update(kwargs)

        with patch("black.schedule_formatting", side_effect=capture_schedule):
            with patch("black.shutdown"):
                reformat_many(
                    sources=sources,
                    fast=False,
                    write_back=wb,
                    mode=mode,
                    report=report,
                )

        assert captured_kwargs["write_back"] is wb


# ---------------------------------------------------------------------------
# --- BVA ---
# Boundary Value Analysis
# ---------------------------------------------------------------------------

class TestBVAWorkerCountNonWindows:
    """BVA: on non-Windows, worker_count == os.cpu_count(), no clamping."""

    def test_cpu_count_used_as_max_workers(self, tmp_path):
        """A correct implementation should pass cpu_count() as max_workers on non-win32."""
        sources = {tmp_path / "f.py"}
        report = _make_report()
        mode = _make_mode()

        cpu_count = 8
        created_executor = None

        class CapturingExecutor:
            def __init__(self, max_workers):
                nonlocal created_executor
                self.max_workers = max_workers
                created_executor = self

            def shutdown(self, *args, **kwargs):
                pass

        async def noop(**kwargs):
            pass

        with patch("black.schedule_formatting", side_effect=noop):
            with patch("black.shutdown"):
                with patch("os.cpu_count", return_value=cpu_count):
                    with patch("sys.platform", "linux"):
                        with patch("black.ProcessPoolExecutor", CapturingExecutor):
                            reformat_many(
                                sources=sources,
                                fast=False,
                                write_back=WriteBack.NO,
                                mode=mode,
                                report=report,
                            )

        # A correct implementation should use cpu_count() directly on non-Windows.
        assert created_executor is not None
        assert created_executor.max_workers == cpu_count


class TestBVAWorkerCountWindows61Cap:
    """BVA: on Windows, worker_count is capped at 61 (boundary value)."""

    def test_worker_count_capped_at_61_on_windows(self, tmp_path):
        """
        BVA boundary: cpu_count() > 61 on Windows must produce max_workers == 61.
        A correct implementation caps at 61 per the win32 ProcessPoolExecutor limit.
        """
        sources = {tmp_path / "f.py"}
        report = _make_report()
        mode = _make_mode()

        cpu_count = 128  # well above the 61 cap
        created_executor = None

        class CapturingExecutor:
            def __init__(self, max_workers):
                nonlocal created_executor
                self.max_workers = max_workers
                created_executor = self

            def shutdown(self, *args, **kwargs):
                pass

        async def noop(**kwargs):
            pass

        with patch("black.schedule_formatting", side_effect=noop):
            with patch("black.shutdown"):
                with patch("os.cpu_count", return_value=cpu_count):
                    with patch("sys.platform", "win32"):
                        with patch("black.ProcessPoolExecutor", CapturingExecutor):
                            reformat_many(
                                sources=sources,
                                fast=False,
                                write_back=WriteBack.NO,
                                mode=mode,
                                report=report,
                            )

        assert created_executor is not None
        # A correct implementation must not exceed 61 on win32.
        assert created_executor.max_workers <= 61
        assert created_executor.max_workers == 61


class TestBVAWorkerCountWindowsExactly61:
    """BVA boundary: cpu_count() == 61 on Windows — no clamping needed."""

    def test_worker_count_exactly_61_unchanged(self, tmp_path):
        sources = {tmp_path / "f.py"}
        report = _make_report()
        mode = _make_mode()

        cpu_count = 61
        created_executor = None

        class CapturingExecutor:
            def __init__(self, max_workers):
                nonlocal created_executor
                self.max_workers = max_workers
                created_executor = self

            def shutdown(self, *args, **kwargs):
                pass

        async def noop(**kwargs):
            pass

        with patch("black.schedule_formatting", side_effect=noop):
            with patch("black.shutdown"):
                with patch("os.cpu_count", return_value=cpu_count):
                    with patch("sys.platform", "win32"):
                        with patch("black.ProcessPoolExecutor", CapturingExecutor):
                            reformat_many(
                                sources=sources,
                                fast=False,
                                write_back=WriteBack.NO,
                                mode=mode,
                                report=report,
                            )

        assert created_executor is not None
        # min(61, 61) == 61
        assert created_executor.max_workers == 61


class TestBVAWorkerCountWindows62:
    """BVA boundary: cpu_count() == 62 on Windows — must be clamped to 61."""

    def test_worker_count_62_clamped_to_61(self, tmp_path):
        sources = {tmp_path / "f.py"}
        report = _make_report()
        mode = _make_mode()

        cpu_count = 62  # one above the cap
        created_executor = None

        class CapturingExecutor:
            def __init__(self, max_workers):
                nonlocal created_executor
                self.max_workers = max_workers
                created_executor = self

            def shutdown(self, *args, **kwargs):
                pass

        async def noop(**kwargs):
            pass

        with patch("black.schedule_formatting", side_effect=noop):
            with patch("black.shutdown"):
                with patch("os.cpu_count", return_value=cpu_count):
                    with patch("sys.platform", "win32"):
                        with patch("black.ProcessPoolExecutor", CapturingExecutor):
                            reformat_many(
                                sources=sources,
                                fast=False,
                                write_back=WriteBack.NO,
                                mode=mode,
                                report=report,
                            )

        assert created_executor is not None
        # min(62, 61) == 61 — must be clamped
        assert created_executor.max_workers == 61


class TestBVAWorkerCountWindowsBelow61:
    """BVA boundary: cpu_count() == 1 on Windows — no clamping needed."""

    def test_worker_count_1_not_clamped(self, tmp_path):
        sources = {tmp_path / "f.py"}
        report = _make_report()
        mode = _make_mode()

        cpu_count = 1
        created_executor = None

        class CapturingExecutor:
            def __init__(self, max_workers):
                nonlocal created_executor
                self.max_workers = max_workers
                created_executor = self

            def shutdown(self, *args, **kwargs):
                pass

        async def noop(**kwargs):
            pass

        with patch("black.schedule_formatting", side_effect=noop):
            with patch("black.shutdown"):
                with patch("os.cpu_count", return_value=cpu_count):
                    with patch("sys.platform", "win32"):
                        with patch("black.ProcessPoolExecutor", CapturingExecutor):
                            reformat_many(
                                sources=sources,
                                fast=False,
                                write_back=WriteBack.NO,
                                mode=mode,
                                report=report,
                            )

        assert created_executor is not None
        # min(1, 61) == 1
        assert created_executor.max_workers == 1


# ---------------------------------------------------------------------------
# --- Mutation Detection ---
# ---------------------------------------------------------------------------

class TestMutationShutdownAlwaysCalled:
    """
    Mutation: removing `shutdown(loop)` from the `finally` block.
    A correct implementation MUST call shutdown(loop) even when
    schedule_formatting raises an exception.
    """

    def test_shutdown_called_even_on_exception(self, tmp_path):
        sources = {tmp_path / "f.py"}
        report = _make_report()
        mode = _make_mode()

        async def failing_schedule(**kwargs):
            raise RuntimeError("simulated failure")

        with patch("black.schedule_formatting", side_effect=failing_schedule):
            with patch("black.shutdown") as mock_shutdown:
                # Must propagate the exception from schedule_formatting.
                with pytest.raises(RuntimeError, match="simulated failure"):
                    reformat_many(
                        sources=sources,
                        fast=False,
                        write_back=WriteBack.NO,
                        mode=mode,
                        report=report,
                    )
                # A correct implementation calls shutdown in the finally block.
                mock_shutdown.assert_called_once()


class TestMutationExecutorShutdownAlwaysCalled:
    """
    Mutation: removing `executor.shutdown()` from the `finally` block.
    A correct implementation MUST shut down the executor in all code paths.
    """

    def test_executor_shutdown_called_on_success(self, tmp_path):
        sources = {tmp_path / "f.py"}
        report = _make_report()
        mode = _make_mode()

        executor_instance = MagicMock()
        executor_instance.shutdown = MagicMock()

        async def noop(**kwargs):
            pass

        with patch("black.schedule_formatting", side_effect=noop):
            with patch("black.shutdown"):
                with patch("black.ProcessPoolExecutor", return_value=executor_instance):
                    reformat_many(
                        sources=sources,
                        fast=False,
                        write_back=WriteBack.NO,
                        mode=mode,
                        report=report,
                    )

        executor_instance.shutdown.assert_called_once()

    def test_executor_shutdown_called_on_failure(self, tmp_path):
        sources = {tmp_path / "f.py"}
        report = _make_report()
        mode = _make_mode()

        executor_instance = MagicMock()
        executor_instance.shutdown = MagicMock()

        async def failing_schedule(**kwargs):
            raise RuntimeError("failure")

        with patch("black.schedule_formatting", side_effect=failing_schedule):
            with patch("black.shutdown"):
                with patch("black.ProcessPoolExecutor", return_value=executor_instance):
                    with pytest.raises(RuntimeError):
                        reformat_many(
                            sources=sources,
                            fast=False,
                            write_back=WriteBack.NO,
                            mode=mode,
                            report=report,
                        )

        # A correct implementation shuts down the executor regardless of exception.
        executor_instance.shutdown.assert_called_once()


class TestMutationWindowsCapOffByOne:
    """
    Mutation: using `max_workers=62` instead of 61 as the Windows cap,
    or using `<` vs `<=`.
    BVA boundary cpu_count=62 distinguishes min(62,61)=61 vs min(62,62)=62.
    """

    def test_cap_is_exactly_61_not_62(self, tmp_path):
        sources = {tmp_path / "f.py"}
        report = _make_report()
        mode = _make_mode()

        cpu_count = 62
        created_executor = None

        class CapturingExecutor:
            def __init__(self, max_workers):
                nonlocal created_executor
                self.max_workers = max_workers
                created_executor = self

            def shutdown(self, *args, **kwargs):
                pass

        async def noop(**kwargs):
            pass

        with patch("black.schedule_formatting", side_effect=noop):
            with patch("black.shutdown"):
                with patch("os.cpu_count", return_value=cpu_count):
                    with patch("sys.platform", "win32"):
                        with patch("black.ProcessPoolExecutor", CapturingExecutor):
                            reformat_many(
                                sources=sources,
                                fast=False,
                                write_back=WriteBack.NO,
                                mode=mode,
                                report=report,
                            )

        # Detects mutation: wrong constant 62 instead of 61
        assert created_executor.max_workers == 61
        assert created_executor.max_workers != 62


class TestMutationNonWindowsNotCapped:
    """
    Mutation: applying the Windows cap unconditionally (missing platform check).
    On Linux with cpu_count > 61, a correct implementation should NOT cap.
    """

    def test_non_windows_high_cpu_count_not_capped(self, tmp_path):
        """Detects mutation: win32 branch applied on non-win32 platforms."""
        sources = {tmp_path / "f.py"}
        report = _make_report()
        mode = _make_mode()

        cpu_count = 128
        created_executor = None

        class CapturingExecutor:
            def __init__(self, max_workers):
                nonlocal created_executor
                self.max_workers = max_workers
                created_executor = self

            def shutdown(self, *args, **kwargs):
                pass

        async def noop(**kwargs):
            pass

        with patch("black.schedule_formatting", side_effect=noop):
            with patch("black.shutdown"):
                with patch("os.cpu_count", return_value=cpu_count):
                    with patch("sys.platform", "linux"):
                        with patch("black.ProcessPoolExecutor", CapturingExecutor):
                            reformat_many(
                                sources=sources,
                                fast=False,
                                write_back=WriteBack.NO,
                                mode=mode,
                                report=report,
                            )

        # On non-win32, a correct implementation uses the full cpu_count.
        assert created_executor is not None
        assert created_executor.max_workers == cpu_count  # 128, not 61


class TestMutationFastFlagForwarded:
    """
    Mutation: `fast` parameter hardcoded to False (wrong variable / constant).
    A correct implementation must forward the caller's `fast` value unchanged.
    """

    @pytest.mark.parametrize("fast_value", [True, False])
    def test_fast_forwarded_as_given(self, tmp_path, fast_value):
        sources = {tmp_path / "f.py"}
        report = _make_report()
        mode = _make_mode()

        captured_kwargs = {}

        async def capture_schedule(**kwargs):
            captured_kwargs.update(kwargs)

        with patch("black.schedule_formatting", side_effect=capture_schedule):
            with patch("black.shutdown"):
                reformat_many(
                    sources=sources,
                    fast=fast_value,
                    write_back=WriteBack.NO,
                    mode=mode,
                    report=report,
                )

        # Detects mutation: `fast` hardcoded to True or False
        assert captured_kwargs["fast"] is fast_value


class TestMutationLoopPassedToSchedule:
    """
    Mutation: `loop` argument omitted or wrong variable passed to schedule_formatting.
    A correct implementation should pass the loop obtained from get_event_loop().
    """

    def test_loop_passed_to_schedule_formatting(self, tmp_path):
        sources = {tmp_path / "f.py"}
        report = _make_report()
        mode = _make_mode()

        captured_kwargs = {}
        sentinel_loop = asyncio.new_event_loop()

        async def capture_schedule(**kwargs):
            captured_kwargs.update(kwargs)

        try:
            with patch("black.schedule_formatting", side_effect=capture_schedule):
                with patch("black.shutdown"):
                    with patch("asyncio.get_event_loop", return_value=sentinel_loop):
                        with patch.object(sentinel_loop, "run_until_complete",
                                          wraps=sentinel_loop.run_until_complete):
                            reformat_many(
                                sources=sources,
                                fast=False,
                                write_back=WriteBack.NO,
                                mode=mode,
                                report=report,
                            )
        finally:
            sentinel_loop.close()

        # A correct implementation must pass the loop it obtained.
        assert captured_kwargs.get("loop") is sentinel_loop


class TestMutationExecutorPassedToSchedule:
    """
    Mutation: `executor` argument omitted or wrong object passed.
    A correct implementation should pass the created executor to schedule_formatting.
    """

    def test_executor_passed_to_schedule_formatting(self, tmp_path):
        sources = {tmp_path / "f.py"}
        report = _make_report()
        mode = _make_mode()

        captured_kwargs = {}
        executor_instance = MagicMock()
        executor_instance.shutdown = MagicMock()

        async def capture_schedule(**kwargs):
            captured_kwargs.update(kwargs)

        with patch("black.schedule_formatting", side_effect=capture_schedule):
            with patch("black.shutdown"):
                with patch("black.ProcessPoolExecutor", return_value=executor_instance):
                    reformat_many(
                        sources=sources,
                        fast=False,
                        write_back=WriteBack.NO,
                        mode=mode,
                        report=report,
                    )

        # A correct implementation must pass the executor it created.
        assert captured_kwargs.get("executor") is executor_instance