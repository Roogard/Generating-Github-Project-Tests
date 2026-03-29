import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from tornado.websocket import WebSocketProtocol

# --- Statement Coverage ---

def test_receive_frame_loop_raises_not_implemented():
    # Statement coverage: the only executable statement is `raise NotImplementedError()`
    # A correct abstract method SHOULD raise NotImplementedError when called on the base class
    # path: enter method → raise NotImplementedError
    instance = MagicMock(spec=WebSocketProtocol)
    # Call the actual unbound method directly on the mock instance
    with pytest.raises(NotImplementedError):
        asyncio.get_event_loop().run_until_complete(
            WebSocketProtocol._receive_frame_loop(instance)
        )

# --- Block Coverage ---

def test_receive_frame_loop_single_block():
    # Block coverage: there is exactly one basic block in this function.
    # The block contains `raise NotImplementedError()`.
    # A correct abstract method body SHOULD always raise NotImplementedError.
    instance = MagicMock(spec=WebSocketProtocol)
    with pytest.raises(NotImplementedError):
        asyncio.get_event_loop().run_until_complete(
            WebSocketProtocol._receive_frame_loop(instance)
        )
    # Already covered by statement coverage test; confirmed here for block completeness.

# --- Condition Coverage ---

# There are no boolean sub-expressions or conditionals in `_receive_frame_loop`.
# The function unconditionally raises NotImplementedError.
# No additional condition coverage tests are needed beyond confirming the single path.

def test_receive_frame_loop_no_conditions():
    # Condition coverage note: no boolean sub-expressions exist in this method.
    # Property assertion: for ANY concrete subclass that does NOT override the method,
    # calling _receive_frame_loop on the base implementation SHOULD raise NotImplementedError.
    instance = MagicMock(spec=WebSocketProtocol)
    with pytest.raises(NotImplementedError):
        asyncio.get_event_loop().run_until_complete(
            WebSocketProtocol._receive_frame_loop(instance)
        )

# --- Path Coverage ---

def test_receive_frame_loop_only_path():
    # Path coverage: there is exactly one path through this function.
    # path: function entry → raise NotImplementedError → propagate exception → exit
    # A correct abstract base method SHOULD raise NotImplementedError on direct invocation.
    instance = MagicMock(spec=WebSocketProtocol)
    with pytest.raises(NotImplementedError):
        asyncio.get_event_loop().run_until_complete(
            WebSocketProtocol._receive_frame_loop(instance)
        )

def test_receive_frame_loop_is_abstract():
    # Path/property: the method is decorated with @abc.abstractmethod.
    # A correct abstract method SHOULD be registered as abstract on the class.
    assert '_receive_frame_loop' in WebSocketProtocol.__abstractmethods__

def test_receive_frame_loop_coroutine_raises():
    # Path coverage: verify that even when awaited as a coroutine, the exception propagates.
    # path: caller awaits coroutine → coroutine raises NotImplementedError → caller receives exception
    instance = MagicMock(spec=WebSocketProtocol)

    async def runner():
        await WebSocketProtocol._receive_frame_loop(instance)

    with pytest.raises(NotImplementedError):
        asyncio.get_event_loop().run_until_complete(runner())

def test_receive_frame_loop_exception_type():
    # Property assertion: the raised exception SHOULD be exactly NotImplementedError,
    # not a subclass or a different exception type.
    instance = MagicMock(spec=WebSocketProtocol)
    try:
        asyncio.get_event_loop().run_until_complete(
            WebSocketProtocol._receive_frame_loop(instance)
        )
        assert False, "Expected NotImplementedError was not raised"
    except NotImplementedError as exc:
        assert type(exc) is NotImplementedError
    except Exception as exc:
        assert False, f"Wrong exception type raised: {type(exc)}"

def test_receive_frame_loop_subclass_must_override():
    # Property assertion: a concrete subclass that does NOT override _receive_frame_loop
    # SHOULD NOT be instantiable (abc enforcement), but if bypassed, the base raises NotImplementedError.
    # We bypass abc via MagicMock to test the raw method.
    instance = MagicMock(spec=WebSocketProtocol)
    coro = WebSocketProtocol._receive_frame_loop(instance)
    assert asyncio.iscoroutine(coro), "A correct async method SHOULD return a coroutine"
    with pytest.raises(NotImplementedError):
        asyncio.get_event_loop().run_until_complete(coro)