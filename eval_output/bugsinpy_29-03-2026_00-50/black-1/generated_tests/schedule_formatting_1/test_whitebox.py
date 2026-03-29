import asyncio
import signal
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch, call
import pytest

from black import schedule_formatting

# ---------------------------------------------------------------------------
# Helpers / Stubs
# ---------------------------------------------------------------------------

def _make_future(loop, result=None, exception=None, cancelled=False):
    """Return a real asyncio.Future pre-resolved in the given way."""
    fut = loop.create_future()
    if cancelled:
        fut.cancel()
    elif exception is not None:
        fut.set_exception(exception)
    else:
        fut.set_result(result)
    return fut


def _make_report():
    report = MagicMock()
    report.done = MagicMock()
    report.failed = MagicMock()
    return report


def _make_mode():
    """Return a minimal Mode-like object."""
    mode = MagicMock()
    mode.__hash__ = lambda self: 0
    return mode


# We need to import the real enums/types used inside schedule_formatting.
# Guard the import so the test module is still importable even when black is
# partially available.
try:
    from black import WriteBack, Changed, Mode, read_cache, filter_cached, write_cache
    from black import format_file_in_place
    _BLACK_AVAILABLE = True
except ImportError:
    _BLACK_AVAILABLE = False

pytestmark = pytest.mark.skipif(not _BLACK_AVAILABLE,
                                reason="black not fully importable")


# ---------------------------------------------------------------------------
# Shared fixture: a real event loop
# ---------------------------------------------------------------------------

@pytest.fixture
def loop():
    lp = asyncio.new_event_loop()
    yield lp
    lp.close()


def run(coro, lp):
    return lp.run_until_complete(coro)


# ---------------------------------------------------------------------------
# Statement Coverage
# ---------------------------------------------------------------------------
# Goal: reach every executable statement at least once.

class TestStatementCoverage:

    # --- helpers shared by this class ---

    def _patch_base(self, sources_result=None, cached_result=None):
        """Return a context-manager stack of standard patches."""
        sources_result = sources_result if sources_result is not None else set()
        cached_result = cached_result if cached_result is not None else set()
        return sources_result, cached_result

    # ST-1: write_back != DIFF  →  read_cache / filter_cached called;
    #        sources becomes empty after filtering  →  early return hit.
    def test_early_return_when_no_sources_after_cache_filter(self, loop):
        """A correct impl SHOULD return immediately when all sources are cached."""
        src = Path("/tmp/a.py")
        report = _make_report()
        mode = _make_mode()

        with patch("black.read_cache", return_value={}) as rc, \
             patch("black.filter_cached", return_value=(set(), {src})) as fc, \
             patch("black.write_cache") as wc:

            run(
                schedule_formatting(
                    sources={src},
                    fast=False,
                    write_back=WriteBack.YES,
                    mode=mode,
                    report=report,
                    loop=loop,
                    executor=MagicMock(),
                ),
                loop,
            )

        rc.assert_called_once()
        fc.assert_called_once()
        # report.done called for the cached file
        report.done.assert_called_once_with(src, Changed.CACHED)
        # write_cache should NOT be called (no sources_to_cache, early return)
        wc.assert_not_called()

    # ST-2: write_back == DIFF  →  manager / lock created; tasks run.
    def test_diff_mode_creates_lock(self, loop):
        """In DIFF mode a lock MUST be created for output serialisation."""
        src = Path("/tmp/b.py")
        report = _make_report()
        mode = _make_mode()

        fake_future = _make_future(loop, result=False)

        with patch("black.Manager") as MockManager, \
             patch("asyncio.ensure_future", return_value=fake_future), \
             patch.object(loop, "run_in_executor",
                          return_value=_make_future(loop, result=False)), \
             patch.object(loop, "add_signal_handler", side_effect=NotImplementedError):

            mock_mgr_instance = MagicMock()
            MockManager.return_value.__enter__ = MagicMock(return_value=mock_mgr_instance)
            MockManager.return_value.__exit__ = MagicMock(return_value=False)
            MockManager.return_value = mock_mgr_instance
            mock_lock = MagicMock()
            mock_mgr_instance.Lock.return_value = mock_lock

            # We need asyncio.wait to actually complete.
            async def fake_wait(fs, return_when):
                return set(fs), set()

            with patch("asyncio.wait", side_effect=fake_wait):
                run(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.DIFF,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=MagicMock(),
                    ),
                    loop,
                )

        MockManager.assert_called_once()
        mock_mgr_instance.Lock.assert_called_once()

    # ST-3: task.cancelled() path
    def test_cancelled_task_appended(self, loop):
        """A cancelled task MUST NOT trigger report.done or report.failed."""
        src = Path("/tmp/c.py")
        report = _make_report()
        mode = _make_mode()

        cancelled_fut = loop.create_future()
        cancelled_fut.cancel()

        with patch("black.read_cache", return_value={}), \
             patch("black.filter_cached", return_value=({src}, set())), \
             patch("asyncio.ensure_future", return_value=cancelled_fut), \
             patch.object(loop, "add_signal_handler", side_effect=NotImplementedError):

            async def fake_wait(fs, return_when):
                return {cancelled_fut}, set()

            with patch("asyncio.wait", side_effect=fake_wait), \
                 patch("asyncio.gather", new_callable=lambda: lambda *a, **kw: asyncio.coroutine(lambda: None)()):

                async def fake_gather(*args, **kwargs):
                    pass

                with patch("asyncio.gather", side_effect=fake_gather):
                    run(
                        schedule_formatting(
                            sources={src},
                            fast=False,
                            write_back=WriteBack.YES,
                            mode=mode,
                            report=report,
                            loop=loop,
                            executor=MagicMock(),
                        ),
                        loop,
                    )

        report.failed.assert_not_called()

    # ST-4: task.exception() path  →  report.failed called
    def test_exception_task_calls_report_failed(self, loop):
        """A task that raises MUST result in report.failed being called."""
        src = Path("/tmp/d.py")
        report = _make_report()
        mode = _make_mode()

        exc_fut = loop.create_future()
        exc_fut.set_exception(ValueError("parse error"))

        with patch("black.read_cache", return_value={}), \
             patch("black.filter_cached", return_value=({src}, set())), \
             patch("asyncio.ensure_future", return_value=exc_fut), \
             patch.object(loop, "add_signal_handler", side_effect=NotImplementedError):

            async def fake_wait(fs, return_when):
                return {exc_fut}, set()

            with patch("asyncio.wait", side_effect=fake_wait):
                run(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.YES,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=MagicMock(),
                    ),
                    loop,
                )

        report.failed.assert_called_once()
        args = report.failed.call_args[0]
        assert args[0] == src
        assert "parse error" in args[1]

    # ST-5: successful task  →  report.done called with Changed.YES/NO
    def test_successful_task_changed_yes(self, loop):
        """task.result() == True MUST map to Changed.YES."""
        src = Path("/tmp/e.py")
        report = _make_report()
        mode = _make_mode()

        ok_fut = loop.create_future()
        ok_fut.set_result(True)  # file was changed

        with patch("black.read_cache", return_value={}), \
             patch("black.filter_cached", return_value=({src}, set())), \
             patch("asyncio.ensure_future", return_value=ok_fut), \
             patch.object(loop, "add_signal_handler", side_effect=NotImplementedError), \
             patch("black.write_cache"):

            async def fake_wait(fs, return_when):
                return {ok_fut}, set()

            with patch("asyncio.wait", side_effect=fake_wait):
                run(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.NO,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=MagicMock(),
                    ),
                    loop,
                )

        report.done.assert_called_once_with(src, Changed.YES)

    # ST-6: write_cache called when sources_to_cache is non-empty
    def test_write_cache_called_on_write_back_yes(self, loop):
        """write_cache MUST be called when write_back is YES and task succeeded."""
        src = Path("/tmp/f.py")
        report = _make_report()
        mode = _make_mode()

        ok_fut = loop.create_future()
        ok_fut.set_result(True)

        with patch("black.read_cache", return_value={}) as rc, \
             patch("black.filter_cached", return_value=({src}, set())), \
             patch("asyncio.ensure_future", return_value=ok_fut), \
             patch.object(loop, "add_signal_handler", side_effect=NotImplementedError), \
             patch("black.write_cache") as wc:

            async def fake_wait(fs, return_when):
                return {ok_fut}, set()

            with patch("asyncio.wait", side_effect=fake_wait):
                run(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.YES,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=MagicMock(),
                    ),
                    loop,
                )

        wc.assert_called_once()
        call_args = wc.call_args[0]
        assert src in call_args[1]


# ---------------------------------------------------------------------------
# Block Coverage
# ---------------------------------------------------------------------------
# Goal: every basic block (including else/except/finally) is entered.

class TestBlockCoverage:

    # BL-1: NotImplementedError from add_signal_handler  →  except block
    def test_signal_handler_not_implemented_is_swallowed(self, loop):
        """The NotImplementedError block (Windows) MUST be silently swallowed."""
        src = Path("/tmp/g.py")
        report = _make_report()
        mode = _make_mode()

        ok_fut = loop.create_future()
        ok_fut.set_result(False)

        with patch("black.read_cache", return_value={}), \
             patch("black.filter_cached", return_value=({src}, set())), \
             patch("asyncio.ensure_future", return_value=ok_fut), \
             patch.object(loop, "add_signal_handler", side_effect=NotImplementedError), \
             patch("black.write_cache"):

            async def fake_wait(fs, return_when):
                return {ok_fut}, set()

            with patch("asyncio.wait", side_effect=fake_wait):
                # MUST NOT raise
                run(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.YES,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=MagicMock(),
                    ),
                    loop,
                )
        # If we reach here, the except block was executed and swallowed correctly.

    # BL-2: signal handler successfully registered (non-NotImplementedError path)
    def test_signal_handler_registered_successfully(self, loop):
        """When add_signal_handler does not raise, the except block is NOT entered."""
        src = Path("/tmp/h.py")
        report = _make_report()
        mode = _make_mode()

        ok_fut = loop.create_future()
        ok_fut.set_result(False)

        registered_signals = []

        def fake_add_signal_handler(sig, *args, **kwargs):
            registered_signals.append(sig)

        with patch("black.read_cache", return_value={}), \
             patch("black.filter_cached", return_value=({src}, set())), \
             patch("asyncio.ensure_future", return_value=ok_fut), \
             patch.object(loop, "add_signal_handler", side_effect=fake_add_signal_handler), \
             patch("black.write_cache"):

            async def fake_wait(fs, return_when):
                return {ok_fut}, set()

            with patch("asyncio.wait", side_effect=fake_wait):
                run(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.YES,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=MagicMock(),
                    ),
                    loop,
                )

        assert signal.SIGINT in registered_signals
        assert signal.SIGTERM in registered_signals

    # BL-3: cancelled block + asyncio.gather called
    def test_cancelled_block_triggers_gather(self, loop):
        """asyncio.gather MUST be awaited when cancelled tasks exist."""
        src = Path("/tmp/i.py")
        report = _make_report()
        mode = _make_mode()

        cancelled_fut = loop.create_future()
        cancelled_fut.cancel()

        gather_called = []

        async def fake_gather(*args, **kwargs):
            gather_called.extend(args)

        with patch("black.read_cache", return_value={}), \
             patch("black.filter_cached", return_value=({src}, set())), \
             patch("asyncio.ensure_future", return_value=cancelled_fut), \
             patch.object(loop, "add_signal_handler", side_effect=NotImplementedError), \
             patch("asyncio.gather", side_effect=fake_gather):

            async def fake_wait(fs, return_when):
                return {cancelled_fut}, set()

            with patch("asyncio.wait", side_effect=fake_wait):
                run(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.YES,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=MagicMock(),
                    ),
                    loop,
                )

        # gather must have been invoked with the cancelled future
        assert cancelled_fut in gather_called

    # BL-4: write_back == CHECK and changed == NO  →  sources_to_cache appended
    def test_check_mode_unchanged_file_cached(self, loop):
        """In CHECK mode, an already-correct file (result=False) MUST be cached."""
        src = Path("/tmp/j.py")
        report = _make_report()
        mode = _make_mode()

        ok_fut = loop.create_future()
        ok_fut.set_result(False)  # not changed → Changed.NO

        with patch("black.read_cache", return_value={}), \
             patch("black.filter_cached", return_value=({src}, set())), \
             patch("asyncio.ensure_future", return_value=ok_fut), \
             patch.object(loop, "add_signal_handler", side_effect=NotImplementedError), \
             patch("black.write_cache") as wc:

            async def fake_wait(fs, return_when):
                return {ok_fut}, set()

            with patch("asyncio.wait", side_effect=fake_wait):
                run(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.CHECK,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=MagicMock(),
                    ),
                    loop,
                )

        wc.assert_called_once()
        assert src in wc.call_args[0][1]

    # BL-5: write_back == CHECK and changed == YES  →  NOT cached
    def test_check_mode_changed_file_not_cached(self, loop):
        """In CHECK mode, a changed file MUST NOT be written to the cache."""
        src = Path("/tmp/k.py")
        report = _make_report()
        mode = _make_mode()

        ok_fut = loop.create_future()
        ok_fut.set_result(True)  # changed → Changed.YES

        with patch("black.read_cache", return_value={}), \
             patch("black.filter_cached", return_value=({src}, set())), \
             patch("asyncio.ensure_future", return_value=ok_fut), \
             patch.object(loop, "add_signal_handler", side_effect=NotImplementedError), \
             patch("black.write_cache") as wc:

            async def fake_wait(fs, return_when):
                return {ok_fut}, set()

            with patch("asyncio.wait", side_effect=fake_wait):
                run(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.CHECK,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=MagicMock(),
                    ),
                    loop,
                )

        wc.assert_not_called()


# ---------------------------------------------------------------------------
# Condition Coverage
# ---------------------------------------------------------------------------
# Every boolean sub-expression must be True in some test and False in another.

class TestConditionCoverage:

    # Condition: write_back != WriteBack.DIFF
    # CC-1a: write_back == WriteBack.YES  →  condition True  →  cache read
    def test_cond_write_back_not_diff_true(self, loop):
        # write_back != DIFF: True
        src = Path("/tmp/l.py")
        report = _make_report()
        mode = _make_mode()

        with patch("black.read_cache", return_value={}) as rc, \
             patch("black.filter_cached", return_value=(set(), {src})):
            run(
                schedule_formatting(
                    sources={src},
                    fast=False,
                    write_back=WriteBack.YES,  # != DIFF → True
                    mode=mode,
                    report=report,
                    loop=loop,
                    executor=MagicMock(),
                ),
                loop,
            )
        rc.assert_called_once()

    # CC-1b: write_back == WriteBack.DIFF  →  condition False  →  cache NOT read
    def test_cond_write_back_not_diff_false(self, loop):
        # write_back != DIFF: False
        src = Path("/tmp/m.py")
        report = _make_report()
        mode = _make_mode()

        cancelled_fut = loop.create_future()
        cancelled_fut.cancel()

        with patch("black.read_cache", return_value={}) as rc, \
             patch("black.Manager") as MockManager, \
             patch("asyncio.ensure_future", return_value=cancelled_fut), \
             patch.object(loop, "add_signal_handler", side_effect=NotImplementedError):

            mgr = MagicMock()
            MockManager.return_value = mgr
            mgr.Lock.return_value = MagicMock()

            async def fake_wait(fs, return_when):
                return {cancelled_fut}, set()

            async def fake_gather(*a, **k):
                pass

            with patch("asyncio.wait", side_effect=fake_wait), \
                 patch("asyncio.gather", side_effect=fake_gather):
                run(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.DIFF,  # == DIFF → condition False
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=MagicMock(),
                    ),
                    loop,
                )

        rc.assert_not_called()

    # Condition: not sources  (after filtering)
    # CC-2a: sources empty after filter  →  not sources True  →  early return
    # (covered by ST-1; cross-reference only)

    # CC-2b: sources non-empty after filter  →  not sources False  →  continues
    def test_cond_sources_non_empty(self, loop):
        # not sources: False (sources has content)
        src = Path("/tmp/n.py")
        report = _make_report()
        mode = _make_mode()

        ok_fut = loop.create_future()
        ok_fut.set_result(False)

        with patch("black.read_cache", return_value={}), \
             patch("black.filter_cached", return_value=({src}, set())), \
             patch("asyncio.ensure_future", return_value=ok_fut), \
             patch.object(loop, "add_signal_handler", side_effect=NotImplementedError), \
             patch("black.write_cache"):

            async def fake_wait(fs, return_when):
                return {ok_fut}, set()

            with patch("asyncio.wait", side_effect=fake_wait):
                run(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.YES,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=MagicMock(),
                    ),
                    loop,
                )
        # If we reach here, the early return was NOT taken  →  not sources: False
        report.done.assert_called_once()

    # Condition: task.cancelled()
    # CC-3a: True  →  (covered by ST-3)
    # CC-3b: False  →  (covered by ST-4 / ST-5)

    # Condition: task.exception()
    # CC-4a: True  →  (covered by ST-4)
    # CC-4b: False  →  (covered by ST-5)

    # Condition: write_back is WriteBack.YES  (sub-expression A)
    # CC-5a: A=True  →  sources_to_cache appended (covered by ST-6)
    # CC-5b: A=False, B (write_back is CHECK and changed is NO) needs separate tests

    # Condition: write_back is WriteBack.CHECK and changed is Changed.NO
    # sub-expressions: (write_back is CHECK) and (changed is Changed.NO)
    # CC-6: write_back=CHECK, changed=NO  →  both True  →  cache written (BL-4)
    # CC-7: write_back=CHECK, changed=YES →  A=True, B=False  →  cache NOT written (BL-5)

    # CC-8: write_back=NO →  A=False, whole condition False  →  cache NOT written
    def test_cond_write_back_no_not_cached(self, loop):
        # write_back is YES: False; write_back is CHECK: False → condition False
        src = Path("/tmp/o.py")
        report = _make_report()
        mode = _make_mode()

        ok_fut = loop.create_future()
        ok_fut.set_result(True)

        with patch("black.read_cache", return_value={}), \
             patch("black.filter_cached", return_value=({src}, set())), \
             patch("asyncio.ensure_future", return_value=ok_fut), \
             patch.object(loop, "add_signal_handler", side_effect=NotImplementedError), \
             patch("black.write_cache") as wc:

            async def fake_wait(fs, return_when):
                return {ok_fut}, set()

            with patch("asyncio.wait", side_effect=fake_wait):
                run(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.NO,  # neither YES nor CHECK
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=MagicMock(),
                    ),
                    loop,
                )

        wc.assert_not_called()

    # Condition: if cancelled  (after the while loop)
    # CC-9a: cancelled non-empty  →  True  →  (BL-3)
    # CC-9b: cancelled empty  →  False
    def test_cond_no_cancelled(self, loop):
        # if cancelled: False
        src = Path("/tmp/p.py")
        report = _make_report()
        mode = _make_mode()

        ok_fut = loop.create_future()
        ok_fut.set_result(False)

        gather_called = []

        async def fake_gather(*a, **k):
            gather_called.extend(a)

        with patch("black.read_cache", return_value={}), \
             patch("black.filter_cached", return_value=({src}, set())), \
             patch("asyncio.ensure_future", return_value=ok_fut), \
             patch.object(loop, "add_signal_handler", side_effect=NotImplementedError), \
             patch("asyncio.gather", side_effect=fake_gather), \
             patch("black.write_cache"):

            async def fake_wait(fs, return_when):
                return {ok_fut}, set()

            with patch("asyncio.wait", side_effect=fake_wait):
                run(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.YES,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=MagicMock(),
                    ),
                    loop,
                )

        # gather must NOT have been called (no cancelled tasks)
        assert len(gather_called) == 0

    # Condition: if sources_to_cache
    # CC-10a: True  →  write_cache called (ST-6)
    # CC-10b: False →  write_cache NOT called (CC-8)


# ---------------------------------------------------------------------------
# Path Coverage
# ---------------------------------------------------------------------------
# Distinct entry-to-exit routes.

class TestPathCoverage:

    # PATH-1: write_back != DIFF → filter cache → all cached → early return
    # path: cache-branch(True) → filter → cached-loop → early-return
    def test_path_all_sources_cached_early_return(self, loop):
        # path: write_back!=DIFF → read_cache → filter → not sources(True) → return
        src1 = Path("/tmp/q1.py")
        src2 = Path("/tmp/q2.py")
        report = _make_report()
        mode = _make_mode()

        with patch("black.read_cache", return_value={}), \
             patch("black.filter_cached", return_value=(set(), {src1, src2})), \
             patch("black.write_cache") as wc:

            run(
                schedule_formatting(
                    sources={src1, src2},
                    fast=False,
                    write_back=WriteBack.YES,
                    mode=mode,
                    report=report,
                    loop=loop,
                    executor=MagicMock(),
                ),
                loop,
            )

        wc.assert_not_called()
        assert report.done.call_count == 2
        called_with = {c[0][0] for c in report.done.call_args_list}
        assert called_with == {src1, src2}

    # PATH-2: write_back == DIFF → lock created → task ok (no cache, no lock
    #          in caching condition) → while loop 1 iter → no cancelled → no cache
    # path: DIFF-branch → lock → tasks → while(1 iter) → task-ok → no-cache
    #        → no-cancelled → no-sources_to_cache
    def test_path_diff_mode_single_task_ok(self, loop):
        # path: write_back==DIFF → manager/lock → task(result=True) →
        #        while(1iter) → changed=YES → not cached → no gather → no write_cache
        src = Path("/tmp/r.py")
        report = _make_report()
        mode = _make_mode()

        ok_fut = loop.create_future()
        ok_fut.set_result(True)

        with patch("black.Manager") as MockManager, \
             patch("asyncio.ensure_future", return_value=ok_fut), \
             patch.object(loop, "add_signal_handler", side_effect=NotImplementedError), \
             patch("black.write_cache") as wc:

            mgr = MagicMock()
            MockManager.return_value = mgr
            mgr.Lock.return_value = MagicMock()

            async def fake_wait(fs, return_when):
                return {ok_fut}, set()

            with patch("asyncio.wait", side_effect=fake_wait):
                run(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.DIFF,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=MagicMock(),
                    ),
                    loop,
                )

        wc.assert_not_called()
        report.done.assert_called_once_with(src, Changed.YES)

    # PATH-3: multiple sources, multiple iterations of the while loop
    # path: cache-branch(True) → filter → non-empty → while(multi-iter) →
    #        tasks complete one by one → write_cache
    def test_path_multiple_sources_multiple_iterations(self, loop):
        # path: write_back=YES → read_cache → filter → while(2 iters) →
        #        both tasks ok → write_cache
        src1 = Path("/tmp/s1.py")
        src2 = Path("/tmp/s2.py")
        report = _make_report()
        mode = _make_mode()

        fut1 = loop.create_future()
        fut1.set_result(True)
        fut2 = loop.create_future()
        fut2.set_result(False)

        futures = [fut1, fut2]
        call_count = [0]

        async def fake_wait(fs, return_when):
            # Return one future per call to simulate two while-loop iterations.
            f = futures[call_count[0]]
            call_count[0] += 1
            return {f}, set()

        src_to_fut = {src1: fut1, src2: fut2}

        def fake_ensure_future(coro):
            # We need a stable mapping; just return futs in order.
            return futures[len(futures) - len(futures)]  # always fut1 first — use side_effect instead

        ensure_future_calls = [0]

        def make_ensure_future():
            calls = [0]

            def _eff(coro):
                result = futures[calls[0] % len(futures)]
                calls[0] += 1
                return result

            return _eff

        with patch("black.read_cache", return_value={}), \
             patch("black.filter_cached", return_value=({src1, src2}, set())), \
             patch("asyncio.ensure_future", side_effect=make_ensure_future()), \
             patch.object(loop, "add_signal_handler", side_effect=NotImplementedError), \
             patch("black.write_cache") as wc, \
             patch("asyncio.wait", side_effect=fake_wait):

            run(
                schedule_formatting(
                    sources={src1, src2},
                    fast=False,
                    write_back=WriteBack.YES,
                    mode=mode,
                    report=report,
                    loop=loop,
                    executor=MagicMock(),
                ),
                loop,
            )

        # Both tasks completed → report.done called twice
        assert report.done.call_count == 2
        # write_cache MUST be called (sources_to_cache non-empty)
        wc.assert_called_once()

    # PATH-4: task exception path  →  report.failed, no cache write
    # path: cache-branch(True) → filter → non-empty → while(1 iter) →
    #        task-exception → failed → no-cache
    def test_path_exception_task_no_cache(self, loop):
        # path: write_back=YES → read_cache → filter → task raises →
        #        report.failed → while-done → no cancelled → no write_cache
        src = Path("/tmp/t.py")
        report = _make_report()
        mode = _make_mode()

        exc_fut = loop.create_future()
        exc_fut.set_exception(RuntimeError("boom"))

        with patch("black.read_cache", return_value={}), \
             patch("black.filter_cached", return_value=({src}, set())), \
             patch("asyncio.ensure_future", return_value=exc_fut), \
             patch.object(loop, "add_signal_handler", side_effect=NotImplementedError), \
             patch("black.write_cache") as wc:

            async def fake_wait(fs, return_when):
                return {exc_fut}, set()

            with patch("asyncio.wait", side_effect=fake_wait):
                run(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.YES,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=MagicMock(),
                    ),
                    loop,
                )

        report.failed.assert_called_once()
        wc.assert_not_called()

    # PATH-5: cancelled task path  →  asyncio.gather awaited
    # path: cache → filter → non-empty → while(1 iter) → task-cancelled →
    #        gather(cancelled) → no write_cache
    def test_path_cancelled_task_gather_no_cache(self, loop):
        # path: write_back=YES → task cancelled → gather → no write_cache
        src = Path("/tmp/u.py")
        report = _make_report()
        mode = _make_mode()

        cancelled_fut = loop.create_future()
        cancelled_fut.cancel()

        gathered = []

        async def fake_gather(*args, **kwargs):
            gathered.extend(args)

        with patch("black.read_cache", return_value={}), \
             patch("black.filter_cached", return_value=({src}, set())), \
             patch("asyncio.ensure_future", return_value=cancelled_fut), \
             patch.object(loop, "add_signal_handler", side_effect=NotImplementedError), \
             patch("asyncio.gather", side_effect=fake_gather), \
             patch("black.write_cache") as wc:

            async def fake_wait(fs, return_when):
                return {cancelled_fut}, set()

            with patch("asyncio.wait", side_effect=fake_wait):
                run(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.YES,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=MagicMock(),
                    ),
                    loop,
                )

        assert cancelled_fut in gathered
        wc.assert_not_called()

    # PATH-6: zero iterations of the while loop (sources empty after non-DIFF filter)
    # path: cache-branch(True) → filter → sources empty → early-return (zero while iters)
    # (Covered by PATH-1; noting here for completeness.)

    # PATH-7: write_back=CHECK, file unchanged → cached
    # path: cache → filter → task(result=False) → changed=NO →
    #        CHECK+NO → write_cache
    def test_path_check_unchanged_file_written_to_cache(self, loop):
        # path: write_back=CHECK → task result=False → changed=NO → cache written
        src = Path("/tmp/v.py")
        report = _make_report()
        mode = _make_mode()

        ok_fut = loop.create_future()
        ok_fut.set_result(False)

        with patch("black.read_cache", return_value={}), \
             patch("black.filter_cached", return_value=({src}, set())), \
             patch("asyncio.ensure_future", return_value=ok_fut), \
             patch.object(loop, "add_signal_handler", side_effect=NotImplementedError), \
             patch("black.write_cache") as wc:

            async def fake_wait(fs, return_when):
                return {ok_fut}, set()

            with patch("asyncio.wait", side_effect=fake_wait):
                run(
                    schedule_formatting(
                        sources={src},
                        fast=False,
                        write_back=WriteBack.CHECK,
                        mode=mode,
                        report=report,
                        loop=loop,
                        executor=MagicMock(),
                    ),
                    loop,
                )

        wc.assert_called_once()
        report.done.assert_called_once_with(src, Changed.NO)