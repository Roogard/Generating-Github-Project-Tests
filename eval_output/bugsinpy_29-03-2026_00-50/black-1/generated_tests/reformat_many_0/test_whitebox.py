import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from black import reformat_many, WriteBack, Mode

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mode():
    return Mode()

def _make_report():
    report = MagicMock()
    return report

# A coroutine that does nothing, used to replace schedule_formatting
async def _noop_coroutine(*args, **kwargs):
    return None


# ---------------------------------------------------------------------------
# Statement Coverage
# ---------------------------------------------------------------------------
# Tests ensure every executable statement is reached at least once.

@patch("black.shutdown")
@patch("black.ProcessPoolExecutor")
@patch("black.schedule_formatting", return_value=_noop_coroutine())
@patch("asyncio.get_event_loop")
def test_statement_non_win32(mock_get_loop, mock_schedule, mock_executor_cls, mock_shutdown):
    """All statements execute on a non-win32 platform (no worker_count clamp)."""
    # path: win32 branch NOT taken
    mock_loop = MagicMock()
    mock_loop.run_until_complete = MagicMock(return_value=None)
    mock_get_loop.return_value = mock_loop

    mock_executor = MagicMock()
    mock_executor_cls.return_value = mock_executor

    sources = {Path("/tmp/a.py")}
    mode = _make_mode()
    report = _make_report()

    with patch.object(sys, "platform", "linux"):
        reformat_many(sources, fast=True, write_back=WriteBack.NO, mode=mode, report=report)

    # Executor was created
    mock_executor_cls.assert_called_once()
    # loop.run_until_complete was called
    mock_loop.run_until_complete.assert_called_once()
    # shutdown was called in finally
    mock_shutdown.assert_called_once_with(mock_loop)
    # executor.shutdown was called in finally
    mock_executor.shutdown.assert_called_once()


@patch("black.shutdown")
@patch("black.ProcessPoolExecutor")
@patch("black.schedule_formatting", return_value=_noop_coroutine())
@patch("asyncio.get_event_loop")
def test_statement_win32_clamp(mock_get_loop, mock_schedule, mock_executor_cls, mock_shutdown):
    """On win32, worker_count is clamped to min(cpu_count, 61). All statements execute."""
    mock_loop = MagicMock()
    mock_loop.run_until_complete = MagicMock(return_value=None)
    mock_get_loop.return_value = mock_loop

    mock_executor = MagicMock()
    mock_executor_cls.return_value = mock_executor

    sources = {Path("/tmp/b.py")}
    mode = _make_mode()
    report = _make_report()

    with patch.object(sys, "platform", "win32"), \
         patch("os.cpu_count", return_value=100):
        reformat_many(sources, fast=False, write_back=WriteBack.NO, mode=mode, report=report)

    # On win32 with cpu_count=100, worker_count should be min(100, 61) = 61
    call_kwargs = mock_executor_cls.call_args
    assert call_kwargs is not None
    actual_workers = call_kwargs[1].get("max_workers", call_kwargs[0][0] if call_kwargs[0] else None)
    assert actual_workers == 61

    mock_shutdown.assert_called_once_with(mock_loop)
    mock_executor.shutdown.assert_called_once()


# ---------------------------------------------------------------------------
# Block Coverage
# ---------------------------------------------------------------------------
# Every basic block: function entry, win32 branch (true/false),
# try body, finally block.

@patch("black.shutdown")
@patch("black.ProcessPoolExecutor")
@patch("black.schedule_formatting", return_value=_noop_coroutine())
@patch("asyncio.get_event_loop")
def test_block_win32_branch_taken(mock_get_loop, mock_schedule, mock_executor_cls, mock_shutdown):
    """Block: win32 branch IS taken (sys.platform == 'win32').
    # sys.platform=='win32': True
    """
    mock_loop = MagicMock()
    mock_loop.run_until_complete = MagicMock(return_value=None)
    mock_get_loop.return_value = mock_loop
    mock_executor_cls.return_value = MagicMock()

    with patch.object(sys, "platform", "win32"), \
         patch("os.cpu_count", return_value=10):
        reformat_many({Path("/tmp/c.py")}, fast=True, write_back=WriteBack.NO,
                      mode=_make_mode(), report=_make_report())

    # worker_count should be min(10, 61) = 10
    actual = mock_executor_cls.call_args[1].get(
        "max_workers",
        mock_executor_cls.call_args[0][0] if mock_executor_cls.call_args[0] else None
    )
    assert actual == 10


@patch("black.shutdown")
@patch("black.ProcessPoolExecutor")
@patch("black.schedule_formatting", return_value=_noop_coroutine())
@patch("asyncio.get_event_loop")
def test_block_win32_branch_not_taken(mock_get_loop, mock_schedule, mock_executor_cls, mock_shutdown):
    """Block: win32 branch is NOT taken (sys.platform != 'win32').
    # sys.platform=='win32': False
    """
    mock_loop = MagicMock()
    mock_loop.run_until_complete = MagicMock(return_value=None)
    mock_get_loop.return_value = mock_loop
    mock_executor_cls.return_value = MagicMock()

    with patch.object(sys, "platform", "darwin"), \
         patch("os.cpu_count", return_value=8):
        reformat_many({Path("/tmp/d.py")}, fast=True, write_back=WriteBack.NO,
                      mode=_make_mode(), report=_make_report())

    # worker_count should be 8 (not clamped)
    actual = mock_executor_cls.call_args[1].get(
        "max_workers",
        mock_executor_cls.call_args[0][0] if mock_executor_cls.call_args[0] else None
    )
    assert actual == 8


@patch("black.shutdown")
@patch("black.ProcessPoolExecutor")
@patch("black.schedule_formatting", side_effect=RuntimeError("test error"))
@patch("asyncio.get_event_loop")
def test_block_finally_runs_on_exception(mock_get_loop, mock_schedule, mock_executor_cls, mock_shutdown):
    """Block: finally block executes even when run_until_complete raises."""
    mock_loop = MagicMock()
    mock_loop.run_until_complete = MagicMock(side_effect=RuntimeError("boom"))
    mock_get_loop.return_value = mock_loop

    mock_executor = MagicMock()
    mock_executor_cls.return_value = mock_executor

    with patch.object(sys, "platform", "linux"):
        with pytest.raises(RuntimeError, match="boom"):
            reformat_many({Path("/tmp/e.py")}, fast=True, write_back=WriteBack.NO,
                          mode=_make_mode(), report=_make_report())

    # Finally block must still run
    mock_shutdown.assert_called_once_with(mock_loop)
    mock_executor.shutdown.assert_called_once()


@patch("black.shutdown")
@patch("black.ProcessPoolExecutor")
@patch("black.schedule_formatting", return_value=_noop_coroutine())
@patch("asyncio.get_event_loop")
def test_block_try_body_executes(mock_get_loop, mock_schedule, mock_executor_cls, mock_shutdown):
    """Block: try body (run_until_complete) executes normally."""
    mock_loop = MagicMock()
    mock_loop.run_until_complete = MagicMock(return_value=None)
    mock_get_loop.return_value = mock_loop
    mock_executor_cls.return_value = MagicMock()

    with patch.object(sys, "platform", "linux"):
        reformat_many({Path("/tmp/f.py")}, fast=True, write_back=WriteBack.NO,
                      mode=_make_mode(), report=_make_report())

    mock_loop.run_until_complete.assert_called_once()


# ---------------------------------------------------------------------------
# Condition Coverage
# ---------------------------------------------------------------------------
# The only condition is `if sys.platform == "win32"`.
# Sub-expression: (sys.platform == "win32")

@patch("black.shutdown")
@patch("black.ProcessPoolExecutor")
@patch("black.schedule_formatting", return_value=_noop_coroutine())
@patch("asyncio.get_event_loop")
def test_condition_platform_win32_true_cpu_above_61(
    mock_get_loop, mock_schedule, mock_executor_cls, mock_shutdown
):
    """Condition: (sys.platform == 'win32') = True, cpu_count > 61 → clamp to 61.
    # sys.platform=='win32': True
    """
    mock_loop = MagicMock()
    mock_loop.run_until_complete = MagicMock(return_value=None)
    mock_get_loop.return_value = mock_loop
    mock_executor_cls.return_value = MagicMock()

    with patch.object(sys, "platform", "win32"), \
         patch("os.cpu_count", return_value=200):
        reformat_many({Path("/tmp/g.py")}, fast=True, write_back=WriteBack.NO,
                      mode=_make_mode(), report=_make_report())

    actual = mock_executor_cls.call_args[1].get(
        "max_workers",
        mock_executor_cls.call_args[0][0] if mock_executor_cls.call_args[0] else None
    )
    # A correct implementation must clamp to 61 on win32 when cpu_count > 61
    assert actual == 61


@patch("black.shutdown")
@patch("black.ProcessPoolExecutor")
@patch("black.schedule_formatting", return_value=_noop_coroutine())
@patch("asyncio.get_event_loop")
def test_condition_platform_win32_true_cpu_below_61(
    mock_get_loop, mock_schedule, mock_executor_cls, mock_shutdown
):
    """Condition: (sys.platform == 'win32') = True, cpu_count < 61 → no clamp.
    # sys.platform=='win32': True
    """
    mock_loop = MagicMock()
    mock_loop.run_until_complete = MagicMock(return_value=None)
    mock_get_loop.return_value = mock_loop
    mock_executor_cls.return_value = MagicMock()

    with patch.object(sys, "platform", "win32"), \
         patch("os.cpu_count", return_value=4):
        reformat_many({Path("/tmp/h.py")}, fast=True, write_back=WriteBack.NO,
                      mode=_make_mode(), report=_make_report())

    actual = mock_executor_cls.call_args[1].get(
        "max_workers",
        mock_executor_cls.call_args[0][0] if mock_executor_cls.call_args[0] else None
    )
    # min(4, 61) == 4
    assert actual == 4


@patch("black.shutdown")
@patch("black.ProcessPoolExecutor")
@patch("black.schedule_formatting", return_value=_noop_coroutine())
@patch("asyncio.get_event_loop")
def test_condition_platform_win32_false(
    mock_get_loop, mock_schedule, mock_executor_cls, mock_shutdown
):
    """Condition: (sys.platform == 'win32') = False → worker_count not clamped.
    # sys.platform=='win32': False
    """
    mock_loop = MagicMock()
    mock_loop.run_until_complete = MagicMock(return_value=None)
    mock_get_loop.return_value = mock_loop
    mock_executor_cls.return_value = MagicMock()

    with patch.object(sys, "platform", "linux"), \
         patch("os.cpu_count", return_value=128):
        reformat_many({Path("/tmp/i.py")}, fast=True, write_back=WriteBack.NO,
                      mode=_make_mode(), report=_make_report())

    actual = mock_executor_cls.call_args[1].get(
        "max_workers",
        mock_executor_cls.call_args[0][0] if mock_executor_cls.call_args[0] else None
    )
    # On non-win32, worker_count is cpu_count unchanged
    assert actual == 128


# ---------------------------------------------------------------------------
# Path Coverage
# ---------------------------------------------------------------------------
# Paths through reformat_many:
#   Path A: non-win32 → try succeeds → finally
#   Path B: win32 (cpu > 61) → try succeeds → finally
#   Path C: win32 (cpu <= 61) → try succeeds → finally
#   Path D: non-win32 → try raises → finally (exception propagates)
#   Path E: win32 → try raises → finally (exception propagates)

@patch("black.shutdown")
@patch("black.ProcessPoolExecutor")
@patch("black.schedule_formatting", return_value=_noop_coroutine())
@patch("asyncio.get_event_loop")
def test_path_A_non_win32_success(mock_get_loop, mock_schedule, mock_executor_cls, mock_shutdown):
    """Path A: non-win32 → try body succeeds → finally.
    # path: platform!=win32 → run_until_complete OK → finally
    """
    mock_loop = MagicMock()
    mock_loop.run_until_complete = MagicMock(return_value=None)
    mock_get_loop.return_value = mock_loop
    mock_executor = MagicMock()
    mock_executor_cls.return_value = mock_executor

    with patch.object(sys, "platform", "linux"), \
         patch("os.cpu_count", return_value=4):
        reformat_many({Path("/tmp/j.py")}, fast=True, write_back=WriteBack.NO,
                      mode=_make_mode(), report=_make_report())

    mock_loop.run_until_complete.assert_called_once()
    mock_shutdown.assert_called_once_with(mock_loop)
    mock_executor.shutdown.assert_called_once()


@patch("black.shutdown")
@patch("black.ProcessPoolExecutor")
@patch("black.schedule_formatting", return_value=_noop_coroutine())
@patch("asyncio.get_event_loop")
def test_path_B_win32_cpu_above_61_success(mock_get_loop, mock_schedule, mock_executor_cls, mock_shutdown):
    """Path B: win32 + cpu>61 → clamp → try succeeds → finally.
    # path: platform==win32, cpu_count>61 → min clamp → run_until_complete OK → finally
    """
    mock_loop = MagicMock()
    mock_loop.run_until_complete = MagicMock(return_value=None)
    mock_get_loop.return_value = mock_loop
    mock_executor = MagicMock()
    mock_executor_cls.return_value = mock_executor

    with patch.object(sys, "platform", "win32"), \
         patch("os.cpu_count", return_value=999):
        reformat_many({Path("/tmp/k.py")}, fast=False, write_back=WriteBack.NO,
                      mode=_make_mode(), report=_make_report())

    actual = mock_executor_cls.call_args[1].get(
        "max_workers",
        mock_executor_cls.call_args[0][0] if mock_executor_cls.call_args[0] else None
    )
    assert actual == 61
    mock_shutdown.assert_called_once_with(mock_loop)
    mock_executor.shutdown.assert_called_once()


@patch("black.shutdown")
@patch("black.ProcessPoolExecutor")
@patch("black.schedule_formatting", return_value=_noop_coroutine())
@patch("asyncio.get_event_loop")
def test_path_C_win32_cpu_below_61_success(mock_get_loop, mock_schedule, mock_executor_cls, mock_shutdown):
    """Path C: win32 + cpu<=61 → no clamp → try succeeds → finally.
    # path: platform==win32, cpu_count<=61 → worker_count=cpu_count → run_until_complete OK → finally
    """
    mock_loop = MagicMock()
    mock_loop.run_until_complete = MagicMock(return_value=None)
    mock_get_loop.return_value = mock_loop
    mock_executor = MagicMock()
    mock_executor_cls.return_value = mock_executor

    with patch.object(sys, "platform", "win32"), \
         patch("os.cpu_count", return_value=61):
        reformat_many({Path("/tmp/l.py")}, fast=False, write_back=WriteBack.NO,
                      mode=_make_mode(), report=_make_report())

    actual = mock_executor_cls.call_args[1].get(
        "max_workers",
        mock_executor_cls.call_args[0][0] if mock_executor_cls.call_args[0] else None
    )
    assert actual == 61  # min(61, 61) == 61
    mock_shutdown.assert_called_once_with(mock_loop)
    mock_executor.shutdown.assert_called_once()


@patch("black.shutdown")
@patch("black.ProcessPoolExecutor")
@patch("black.schedule_formatting", return_value=_noop_coroutine())
@patch("asyncio.get_event_loop")
def test_path_D_non_win32_try_raises(mock_get_loop, mock_schedule, mock_executor_cls, mock_shutdown):
    """Path D: non-win32 → try body raises → finally still executes → exception propagates.
    # path: platform!=win32 → run_until_complete raises → finally
    """
    mock_loop = MagicMock()
    mock_loop.run_until_complete = MagicMock(side_effect=KeyboardInterrupt("interrupted"))
    mock_get_loop.return_value = mock_loop
    mock_executor = MagicMock()
    mock_executor_cls.return_value = mock_executor

    with patch.object(sys, "platform", "linux"):
        with pytest.raises(KeyboardInterrupt):
            reformat_many({Path("/tmp/m.py")}, fast=True, write_back=WriteBack.NO,
                          mode=_make_mode(), report=_make_report())

    # finally must have run
    mock_shutdown.assert_called_once_with(mock_loop)
    mock_executor.shutdown.assert_called_once()


@patch("black.shutdown")
@patch("black.ProcessPoolExecutor")
@patch("black.schedule_formatting", return_value=_noop_coroutine())
@patch("asyncio.get_event_loop")
def test_path_E_win32_try_raises(mock_get_loop, mock_schedule, mock_executor_cls, mock_shutdown):
    """Path E: win32 → clamp → try body raises → finally still executes → exception propagates.
    # path: platform==win32 → clamp → run_until_complete raises → finally
    """
    mock_loop = MagicMock()
    mock_loop.run_until_complete = MagicMock(side_effect=ValueError("fail"))
    mock_get_loop.return_value = mock_loop
    mock_executor = MagicMock()
    mock_executor_cls.return_value = mock_executor

    with patch.object(sys, "platform", "win32"), \
         patch("os.cpu_count", return_value=80):
        with pytest.raises(ValueError, match="fail"):
            reformat_many({Path("/tmp/n.py")}, fast=True, write_back=WriteBack.NO,
                          mode=_make_mode(), report=_make_report())

    mock_shutdown.assert_called_once_with(mock_loop)
    mock_executor.shutdown.assert_called_once()


# ---------------------------------------------------------------------------
# Additional property assertions
# ---------------------------------------------------------------------------

@patch("black.shutdown")
@patch("black.ProcessPoolExecutor")
@patch("black.schedule_formatting", return_value=_noop_coroutine())
@patch("asyncio.get_event_loop")
def test_schedule_formatting_called_with_correct_args(
    mock_get_loop, mock_schedule, mock_executor_cls, mock_shutdown
):
    """schedule_formatting must be called with the provided sources, fast, write_back, mode, report."""
    mock_loop = MagicMock()
    mock_loop.run_until_complete = MagicMock(return_value=None)
    mock_get_loop.return_value = mock_loop
    mock_executor = MagicMock()
    mock_executor_cls.return_value = mock_executor

    sources = {Path("/tmp/o.py"), Path("/tmp/p.py")}
    mode = _make_mode()
    report = _make_report()
    write_back = WriteBack.YES

    with patch.object(sys, "platform", "linux"):
        reformat_many(sources, fast=True, write_back=write_back, mode=mode, report=report)

    mock_schedule.assert_called_once()
    call_kwargs = mock_schedule.call_args[1]
    assert call_kwargs["sources"] == sources
    assert call_kwargs["fast"] is True
    assert call_kwargs["write_back"] == write_back
    assert call_kwargs["mode"] == mode
    assert call_kwargs["report"] == report
    assert call_kwargs["loop"] == mock_loop
    assert call_kwargs["executor"] == mock_executor


@patch("black.shutdown")
@patch("black.ProcessPoolExecutor")
@patch("black.schedule_formatting", return_value=_noop_coroutine())
@patch("asyncio.get_event_loop")
def test_returns_none(mock_get_loop, mock_schedule, mock_executor_cls, mock_shutdown):
    """reformat_many must return None (it is typed -> None)."""
    mock_loop = MagicMock()
    mock_loop.run_until_complete = MagicMock(return_value=None)
    mock_get_loop.return_value = mock_loop
    mock_executor_cls.return_value = MagicMock()

    with patch.object(sys, "platform", "linux"):
        result = reformat_many({Path("/tmp/q.py")}, fast=True, write_back=WriteBack.NO,
                                mode=_make_mode(), report=_make_report())

    assert result is None


@patch("black.shutdown")
@patch("black.ProcessPoolExecutor")
@patch("black.schedule_formatting", return_value=_noop_coroutine())
@patch("asyncio.get_event_loop")
def test_executor_max_workers_uses_cpu_count_on_non_win32(
    mock_get_loop, mock_schedule, mock_executor_cls, mock_shutdown
):
    """On non-win32 platforms, ProcessPoolExecutor must be created with max_workers=os.cpu_count()."""
    mock_loop = MagicMock()
    mock_loop.run_until_complete = MagicMock(return_value=None)
    mock_get_loop.return_value = mock_loop
    mock_executor_cls.return_value = MagicMock()

    cpu_count = 16
    with patch.object(sys, "platform", "linux"), \
         patch("os.cpu_count", return_value=cpu_count):
        reformat_many({Path("/tmp/r.py")}, fast=True, write_back=WriteBack.NO,
                      mode=_make_mode(), report=_make_report())

    actual = mock_executor_cls.call_args[1].get(
        "max_workers",
        mock_executor_cls.call_args[0][0] if mock_executor_cls.call_args[0] else None
    )
    assert actual == cpu_count