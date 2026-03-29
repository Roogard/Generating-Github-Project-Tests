import pytest
import asyncio
from unittest.mock import MagicMock
from tornado.websocket import WebSocketProtocol


# --- Statement Coverage ---
# The only executable statement in _receive_frame_loop is `raise NotImplementedError()`.
# Every test must reach that statement.

def test_statement_raise_not_implemented():
    # A correct abstract method SHOULD raise NotImplementedError when called
    # directly on a concrete instance that has not overridden it.
    # path: function entry → raise NotImplementedError
    instance = MagicMock(spec=WebSocketProtocol)
    # Bind the real (unoverridden) method to the mock instance
    coro = WebSocketProtocol._receive_frame_loop(instance)
    with pytest.raises(NotImplementedError):
        asyncio.get_event_loop().run_until_complete(coro)


# --- Block Coverage ---
# There is only one basic block: the function body containing the single raise.
# Covered by the statement coverage test above; noted here for completeness.

# test_block_single_block: same as test_statement_raise_not_implemented (deduplicated)
# A correct abstract method has exactly one block; reaching it raises NotImplementedError.


# --- Condition Coverage ---
# There are no boolean sub-expressions in _receive_frame_loop.
# The function unconditionally raises; condition coverage adds no new tests.


# --- Path Coverage ---
# There is exactly one execution path: entry → raise NotImplementedError.
# Covered by test_statement_raise_not_implemented.

def test_path_single_path_is_coroutine():
    # path: function entry → raise NotImplementedError (via coroutine protocol)
    # A correct implementation SHOULD return a coroutine object (async def), not raise
    # synchronously before being awaited.
    instance = MagicMock(spec=WebSocketProtocol)
    result = WebSocketProtocol._receive_frame_loop(instance)
    # Property: calling an async def function must return an awaitable
    assert asyncio.iscoroutine(result), (
        "A correct async def _receive_frame_loop SHOULD return a coroutine when called"
    )
    # Clean up to avoid ResourceWarning
    result.close()


def test_path_exception_type_is_exactly_not_implemented_error():
    # path: entry → raise NotImplementedError
    # A correct abstract method SHOULD raise NotImplementedError specifically,
    # not a subclass or unrelated exception.
    instance = MagicMock(spec=WebSocketProtocol)
    coro = WebSocketProtocol._receive_frame_loop(instance)
    with pytest.raises(NotImplementedError):
        asyncio.get_event_loop().run_until_complete(coro)


def test_path_subclass_without_override_also_raises():
    # path: entry → raise NotImplementedError (via subclass that does NOT override)
    # A correct abstract base method SHOULD still raise when the subclass
    # does not provide its own implementation.
    class ConcreteNoOverride(WebSocketProtocol):
        pass  # deliberately does not override _receive_frame_loop

    instance = MagicMock(spec=ConcreteNoOverride)
    coro = WebSocketProtocol._receive_frame_loop(instance)
    with pytest.raises(NotImplementedError):
        asyncio.get_event_loop().run_until_complete(coro)


def test_path_subclass_with_override_does_not_raise():
    # path: subclass provides override → NotImplementedError is NOT raised
    # A correct override of _receive_frame_loop SHOULD suppress the base
    # NotImplementedError entirely when the subclass supplies its own body.
    class ConcreteWithOverride(WebSocketProtocol):
        async def _receive_frame_loop(self) -> None:
            return  # correct override: just return without raising

    instance = MagicMock(spec=ConcreteWithOverride)
    # The override should complete without exception
    coro = ConcreteWithOverride._receive_frame_loop(instance)
    # Property: a proper override SHOULD NOT raise NotImplementedError
    asyncio.get_event_loop().run_until_complete(coro)  # must not raise


def test_path_multiple_calls_each_raise():
    # path: entry → raise NotImplementedError (repeated; each call is independent)
    # A correct abstract method SHOULD raise on every invocation, not just the first.
    instance = MagicMock(spec=WebSocketProtocol)
    for _ in range(3):
        coro = WebSocketProtocol._receive_frame_loop(instance)
        with pytest.raises(NotImplementedError):
            asyncio.get_event_loop().run_until_complete(coro)