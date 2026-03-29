import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from tornado.websocket import WebSocketProtocol


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_protocol_instance():
    """Return a raw WebSocketProtocol-derived object without __init__ magic."""
    class MinimalProtocol(WebSocketProtocol):
        def write_message(self, message, binary=False):
            pass

        def write_ping(self, data):
            pass

        def _process_server_headers(self, key, headers):
            pass

        def _get_compressor_options(self, side, agreed_parameters, compression_options=None):
            pass

        def _create_compressor(self):
            pass

        def _create_decompressor(self):
            pass

        async def _receive_frame_loop(self):
            raise NotImplementedError()

        async def accept_connection(self, request):
            pass

        def close(self, code=None, reason=None):
            pass

        def is_closing(self):
            pass

        @property
        def selected_subprotocol(self):
            return None

        async def start_pinging(self):
            pass

    instance = object.__new__(MinimalProtocol)
    return instance


# ---------------------------------------------------------------------------
# Concrete minimal subclass used across all sections
# ---------------------------------------------------------------------------

class _ConcreteProtocol(WebSocketProtocol):
    """Minimal concrete subclass to instantiate WebSocketProtocol."""

    def write_message(self, message, binary=False):
        pass

    def write_ping(self, data):
        pass

    def _process_server_headers(self, key, headers):
        pass

    def _get_compressor_options(self, side, agreed_parameters, compression_options=None):
        pass

    def _create_compressor(self):
        pass

    def _create_decompressor(self):
        pass

    async def _receive_frame_loop(self):
        raise NotImplementedError()

    async def accept_connection(self, request):
        pass

    def close(self, code=None, reason=None):
        pass

    def is_closing(self):
        pass

    @property
    def selected_subprotocol(self):
        return None

    async def start_pinging(self):
        pass


# ---------------------------------------------------------------------------
# BVA — Boundary Value Analysis
# ---------------------------------------------------------------------------

class TestReceiveFrameLoopBVA:

    def test_base_class_raises_not_implemented_error(self):
        """
        BVA: The absolute minimum case – calling _receive_frame_loop on the
        base class (no subclass override) MUST raise NotImplementedError.
        A correct abstract method implementation raises NotImplementedError.
        """
        instance = object.__new__(_ConcreteProtocol)

        async def _run():
            # Call the *base class* method directly, bypassing any override.
            await WebSocketProtocol._receive_frame_loop(instance)

        with pytest.raises(NotImplementedError):
            asyncio.get_event_loop().run_until_complete(_run())

    def test_base_method_is_coroutine_function(self):
        """
        BVA: Even at the boundary of 'not implemented', the method must
        be declared as a coroutine (async def), so it returns an awaitable
        rather than raising synchronously before it is awaited.
        """
        assert asyncio.iscoroutinefunction(WebSocketProtocol._receive_frame_loop), (
            "A correct _receive_frame_loop SHOULD be a coroutine function (async def)"
        )

    def test_calling_returns_coroutine_object_before_await(self):
        """
        BVA: Before await, the call must return a coroutine object, not raise.
        Synchronous call (no await) should NOT raise immediately.
        """
        instance = object.__new__(_ConcreteProtocol)
        coro = WebSocketProtocol._receive_frame_loop(instance)
        # It must be a coroutine
        assert asyncio.iscoroutine(coro), (
            "A correct async method SHOULD return a coroutine when called"
        )
        # Clean up without awaiting to avoid ResourceWarning
        coro.close()

    def test_not_implemented_error_is_not_raised_synchronously(self):
        """
        BVA: The NotImplementedError must only surface when the coroutine is
        *awaited*, not when the method is merely *called*.  This distinguishes
        async from sync raises.
        """
        instance = object.__new__(_ConcreteProtocol)
        # This must not raise
        try:
            coro = WebSocketProtocol._receive_frame_loop(instance)
            coro.close()
        except NotImplementedError:
            pytest.fail(
                "A correct async _receive_frame_loop SHOULD NOT raise "
                "NotImplementedError before being awaited"
            )


# ---------------------------------------------------------------------------
# ECP — Equivalence Class Partitioning
# ---------------------------------------------------------------------------

class TestReceiveFrameLoopECP:

    # --- Valid class: subclass that properly overrides the method ---

    def test_valid_override_does_not_raise(self):
        """
        ECP valid class: a subclass that properly overrides _receive_frame_loop
        should be callable and awaitable without NotImplementedError.
        """
        class OverriddenProtocol(_ConcreteProtocol):
            async def _receive_frame_loop(self):
                return "ok"

        instance = object.__new__(OverriddenProtocol)

        async def _run():
            result = await OverriddenProtocol._receive_frame_loop(instance)
            return result

        result = asyncio.get_event_loop().run_until_complete(_run())
        assert result == "ok"

    # --- Invalid class: base class with no override ---

    def test_invalid_no_override_raises_not_implemented_error(self):
        """
        ECP invalid class: using the base class method directly (no override)
        MUST raise NotImplementedError when awaited.
        """
        instance = object.__new__(_ConcreteProtocol)

        async def _run():
            await WebSocketProtocol._receive_frame_loop(instance)

        with pytest.raises(NotImplementedError):
            asyncio.get_event_loop().run_until_complete(_run())

    # --- Invalid class: subclass that calls super() ---

    def test_invalid_subclass_delegates_to_super_raises(self):
        """
        ECP invalid class: a subclass that calls super()._receive_frame_loop()
        effectively delegates to the base, which must still raise.
        """
        class DelegatingProtocol(_ConcreteProtocol):
            async def _receive_frame_loop(self):
                await super()._receive_frame_loop()

        instance = object.__new__(DelegatingProtocol)

        async def _run():
            await DelegatingProtocol._receive_frame_loop(instance)

        with pytest.raises(NotImplementedError):
            asyncio.get_event_loop().run_until_complete(_run())

    # --- Valid class: coroutine nature of the method ---

    def test_method_signature_is_async(self):
        """
        ECP valid class: method must be async (coroutine function), not a
        plain function that happens to return a future or None.
        """
        assert asyncio.iscoroutinefunction(WebSocketProtocol._receive_frame_loop)

    # --- ECP: return annotation ---

    def test_return_annotation_is_none(self):
        """
        ECP: A correct _receive_frame_loop SHOULD declare -> None return type,
        indicating it runs a loop and produces no meaningful return value.
        """
        annotations = WebSocketProtocol._receive_frame_loop.__annotations__
        # 'return' key holds the return annotation when declared; the value is None (not type(None))
        assert annotations.get("return") is None, (
            "A correct _receive_frame_loop SHOULD annotate its return as None"
        )

    # --- ECP: method exists on class ---

    def test_method_exists_on_base_class(self):
        """
        ECP: _receive_frame_loop MUST exist directly on WebSocketProtocol,
        not only on subclasses.
        """
        assert "_receive_frame_loop" in WebSocketProtocol.__dict__, (
            "A correct abstract method SHOULD be defined on the base class"
        )


# ---------------------------------------------------------------------------
# Mutation Detection
# ---------------------------------------------------------------------------

class TestReceiveFrameLoopMutationDetection:

    def test_mutation_not_implemented_replaced_by_pass(self):
        """
        Mutation: `raise NotImplementedError()` replaced by `pass` (or `return`).
        A correct implementation MUST raise, not silently return None.
        """
        instance = object.__new__(_ConcreteProtocol)

        async def _run():
            return await WebSocketProtocol._receive_frame_loop(instance)

        with pytest.raises(NotImplementedError):
            asyncio.get_event_loop().run_until_complete(_run())

    def test_mutation_not_implemented_replaced_by_return_none(self):
        """
        Mutation: `raise NotImplementedError()` replaced by `return None`.
        Detect by asserting the exception IS raised (not silently None).
        """
        instance = object.__new__(_ConcreteProtocol)
        raised = False

        async def _run():
            nonlocal raised
            try:
                await WebSocketProtocol._receive_frame_loop(instance)
            except NotImplementedError:
                raised = True

        asyncio.get_event_loop().run_until_complete(_run())
        assert raised, (
            "A correct _receive_frame_loop SHOULD raise NotImplementedError, "
            "not silently return None"
        )

    def test_mutation_wrong_exception_type(self):
        """
        Mutation: `raise NotImplementedError()` replaced by
        `raise RuntimeError()` or similar.
        A correct implementation MUST raise specifically NotImplementedError.
        """
        instance = object.__new__(_ConcreteProtocol)

        async def _run():
            await WebSocketProtocol._receive_frame_loop(instance)

        with pytest.raises(NotImplementedError):
            asyncio.get_event_loop().run_until_complete(_run())
        # Ensure it is not accidentally a broader exception masking the wrong type
        # by also confirming RuntimeError is NOT what gets raised in isolation:
        try:
            asyncio.get_event_loop().run_until_complete(_run())
        except NotImplementedError:
            pass  # correct
        except RuntimeError:
            pytest.fail(
                "A correct _receive_frame_loop SHOULD raise NotImplementedError, "
                "not RuntimeError"
            )

    def test_mutation_async_removed_sync_raise(self):
        """
        Mutation: `async def` changed to `def` (sync).
        A correct implementation MUST be a coroutine function.
        Detect by checking asyncio.iscoroutinefunction.
        """
        assert asyncio.iscoroutinefunction(WebSocketProtocol._receive_frame_loop), (
            "Mutation detected: removing `async` would make this a sync function; "
            "a correct _receive_frame_loop SHOULD be async"
        )

    def test_mutation_body_entirely_deleted(self):
        """
        Mutation: entire body deleted (implicit `return None`).
        A correct implementation MUST raise NotImplementedError when awaited.
        """
        instance = object.__new__(_ConcreteProtocol)

        got_exception = None

        async def _run():
            nonlocal got_exception
            try:
                await WebSocketProtocol._receive_frame_loop(instance)
            except Exception as exc:
                got_exception = exc

        asyncio.get_event_loop().run_until_complete(_run())
        assert isinstance(got_exception, NotImplementedError), (
            "A correct _receive_frame_loop with deleted body SHOULD raise "
            f"NotImplementedError, got {type(got_exception)}"
        )

    def test_mutation_exception_instantiation_missing_parens(self):
        """
        Mutation: `raise NotImplementedError` (class) vs `raise NotImplementedError()`
        (instance). Both are valid Python, but the raised object MUST be an
        instance of NotImplementedError.
        """
        instance = object.__new__(_ConcreteProtocol)

        async def _run():
            await WebSocketProtocol._receive_frame_loop(instance)

        try:
            asyncio.get_event_loop().run_until_complete(_run())
        except NotImplementedError as exc:
            # It must be an actual instance
            assert isinstance(exc, NotImplementedError)
        else:
            pytest.fail("NotImplementedError was not raised at all")

    def test_mutation_overridden_method_not_calling_super_works_correctly(self):
        """
        Mutation: a subclass accidentally calls super() when it should not.
        Verify that a correct override without super() does NOT propagate
        NotImplementedError.
        """
        class CorrectOverride(_ConcreteProtocol):
            async def _receive_frame_loop(self):
                # correct: no super(), does its own work
                self._ran = True

        instance = object.__new__(CorrectOverride)
        instance._ran = False

        async def _run():
            await instance._receive_frame_loop()

        asyncio.get_event_loop().run_until_complete(_run())
        assert instance._ran is True, (
            "A correct subclass override SHOULD run its own logic "
            "without raising NotImplementedError"
        )