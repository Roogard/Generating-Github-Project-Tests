import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from tornado.websocket import WebSocketProtocol


# ---------------------------------------------------------------------------
# Helper: minimal concrete subclass that does NOT override _receive_frame_loop
# ---------------------------------------------------------------------------

class IncompleteProtocol(WebSocketProtocol):
    """Subclass that intentionally leaves _receive_frame_loop abstract."""
    # Only implement the bare minimum so the object can be constructed.
    # We deliberately do NOT override _receive_frame_loop so that calling
    # the base-class version raises NotImplementedError.
    pass


class ConcreteProtocol(WebSocketProtocol):
    """Subclass that correctly overrides _receive_frame_loop."""

    async def _receive_frame_loop(self) -> None:
        # A correct override returns normally (or raises application-level
        # errors) rather than raising NotImplementedError.
        return


# ---------------------------------------------------------------------------
# Shared fixture: a mock handler that WebSocketProtocol __init__ may need.
# ---------------------------------------------------------------------------

def make_mock_handler():
    handler = MagicMock()
    handler.stream = MagicMock()
    handler.request = MagicMock()
    handler.close_code = None
    handler.close_reason = None
    return handler


# ---------------------------------------------------------------------------
# BVA — Boundary Value Analysis
# ---------------------------------------------------------------------------

class TestBVA:
    """Boundary cases around the abstract-method contract."""

    def test_base_class_raises_not_implemented(self):
        """
        BVA – absolute boundary: calling the raw abstract method on a
        properly-constructed (but non-overriding) instance must raise
        NotImplementedError.  A correct abstract _receive_frame_loop SHOULD
        always raise NotImplementedError.
        """
        handler = make_mock_handler()
        try:
            proto = object.__new__(IncompleteProtocol)
            # Bypass __init__ to avoid dependency on internal state.
            # We are testing only the abstract method boundary.
        except Exception:
            proto = MagicMock(spec=WebSocketProtocol)

        # The base implementation MUST raise NotImplementedError when invoked.
        with pytest.raises((NotImplementedError, TypeError)):
            asyncio.get_event_loop().run_until_complete(
                WebSocketProtocol._receive_frame_loop(proto)
            )

    def test_concrete_override_does_not_raise_not_implemented(self):
        """
        BVA – opposite boundary: a concrete override SHOULD complete without
        raising NotImplementedError.
        """
        handler = make_mock_handler()
        proto = object.__new__(ConcreteProtocol)

        async def run():
            await proto._receive_frame_loop()

        # Should NOT raise NotImplementedError
        asyncio.get_event_loop().run_until_complete(run())

    def test_abstract_method_is_coroutine_function(self):
        """
        BVA – interface boundary: _receive_frame_loop SHOULD be declared as
        an async (coroutine) function, not a plain function, so callers can
        always await it.
        """
        import inspect
        assert inspect.iscoroutinefunction(WebSocketProtocol._receive_frame_loop), (
            "A correct _receive_frame_loop SHOULD be a coroutine function (async def)"
        )

    def test_return_annotation_is_none(self):
        """
        BVA – type-contract boundary: the declared return annotation SHOULD
        be None (-> None), matching the interface specification.
        """
        import inspect
        sig = inspect.signature(WebSocketProtocol._receive_frame_loop)
        ann = sig.return_annotation
        # Acceptable forms: None or inspect.Parameter.empty (unannotated)
        assert ann in (None, type(None), inspect.Parameter.empty) or ann is None or str(ann) == 'None', (
            "A correct _receive_frame_loop SHOULD declare return type None"
        )


# ---------------------------------------------------------------------------
# ECP — Equivalence Class Partitioning
# ---------------------------------------------------------------------------

class TestECP:
    """Equivalence classes for the abstract-method protocol."""

    # ---- Valid class: subclass overrides _receive_frame_loop ---------------

    def test_ecp_valid_override_completes(self):
        """
        ECP – valid class: any subclass that correctly overrides
        _receive_frame_loop SHOULD be able to run the coroutine to completion.
        """
        proto = object.__new__(ConcreteProtocol)

        async def run():
            result = await proto._receive_frame_loop()
            return result

        result = asyncio.get_event_loop().run_until_complete(run())
        # A correct override returning None SHOULD yield None
        assert result is None

    # ---- Invalid class: base class invoked directly ------------------------

    def test_ecp_invalid_base_class_raises(self):
        """
        ECP – invalid class: invoking the abstract base method SHOULD raise
        NotImplementedError (or a TypeError for abstract instantiation).
        """
        proxy = MagicMock(spec=WebSocketProtocol)
        with pytest.raises((NotImplementedError, TypeError)):
            asyncio.get_event_loop().run_until_complete(
                WebSocketProtocol._receive_frame_loop(proxy)
            )

    # ---- Class: method is abstract (not concrete on base) ------------------

    def test_ecp_abstractmethod_marker(self):
        """
        ECP – class membership: _receive_frame_loop SHOULD be registered as
        an abstract method so that Python's ABC machinery prevents direct
        instantiation of unimplemented subclasses.
        """
        assert '_receive_frame_loop' in WebSocketProtocol.__abstractmethods__, (
            "A correct WebSocketProtocol SHOULD list _receive_frame_loop in __abstractmethods__"
        )

    # ---- Class: method belongs to the class (not instance-only) -----------

    def test_ecp_method_accessible_on_class(self):
        """
        ECP – accessibility class: _receive_frame_loop SHOULD exist as an
        attribute of WebSocketProtocol itself (not just on instances).
        """
        assert hasattr(WebSocketProtocol, '_receive_frame_loop'), (
            "A correct WebSocketProtocol SHOULD expose _receive_frame_loop on the class"
        )

    # ---- Class: override is polymorphic ------------------------------------

    def test_ecp_multiple_independent_overrides(self):
        """
        ECP – polymorphism class: two independent subclasses with different
        override behaviour SHOULD each run their own logic without interfering.
        """
        call_log = []

        class ProtoA(WebSocketProtocol):
            async def _receive_frame_loop(self):
                call_log.append('A')

        class ProtoB(WebSocketProtocol):
            async def _receive_frame_loop(self):
                call_log.append('B')

        a = object.__new__(ProtoA)
        b = object.__new__(ProtoB)

        async def run():
            await a._receive_frame_loop()
            await b._receive_frame_loop()

        asyncio.get_event_loop().run_until_complete(run())
        assert call_log == ['A', 'B'], (
            "Each concrete override SHOULD run its own implementation"
        )


# ---------------------------------------------------------------------------
# Mutation Detection
# ---------------------------------------------------------------------------

class TestMutationDetection:
    """Tests that catch common mutations that could be introduced into _receive_frame_loop."""

    def test_mutation_not_implemented_must_be_raised_not_returned(self):
        """
        Mutation: 'raise NotImplementedError()' mutated to 'return None'.
        A correct abstract method MUST raise, not silently return.
        Distinguishing input: call the base-class method directly.
        """
        proxy = MagicMock(spec=WebSocketProtocol)
        raised = False
        try:
            coro = WebSocketProtocol._receive_frame_loop(proxy)
            result = asyncio.get_event_loop().run_until_complete(coro)
            # If we reach here, the method returned instead of raising – mutation survived
        except (NotImplementedError, TypeError):
            raised = True

        assert raised, (
            "A correct abstract _receive_frame_loop SHOULD raise NotImplementedError, "
            "not silently return (detects 'raise' → 'return' mutation)"
        )

    def test_mutation_abstractmethod_decorator_present(self):
        """
        Mutation: '@abc.abstractmethod' decorator removed.
        Without it, subclasses are NOT forced to implement the method.
        A correct design SHOULD mark it abstract so Python enforces the contract.
        """
        assert '_receive_frame_loop' in WebSocketProtocol.__abstractmethods__, (
            "Detects mutation: removal of @abc.abstractmethod decorator. "
            "A correct _receive_frame_loop SHOULD appear in __abstractmethods__."
        )

    def test_mutation_coroutine_not_plain_function(self):
        """
        Mutation: 'async def' mutated to 'def' (removes coroutine nature).
        Callers always await _receive_frame_loop; a correct implementation
        SHOULD be a coroutine function so 'await' works uniformly.
        """
        import inspect
        assert inspect.iscoroutinefunction(WebSocketProtocol._receive_frame_loop), (
            "Detects mutation: 'async def' → 'def'. "
            "A correct _receive_frame_loop SHOULD be awaitable (async def)."
        )

    def test_mutation_wrong_exception_type(self):
        """
        Mutation: 'raise NotImplementedError()' mutated to 'raise Exception()'.
        A correct abstract method SHOULD raise specifically NotImplementedError
        (or a subclass), not a generic Exception, so callers can distinguish
        the abstract-contract violation from application errors.
        """
        proxy = MagicMock(spec=WebSocketProtocol)
        try:
            coro = WebSocketProtocol._receive_frame_loop(proxy)
            asyncio.get_event_loop().run_until_complete(coro)
        except NotImplementedError:
            pass  # correct
        except TypeError:
            pass  # acceptable – ABC machinery prevents call
        except Exception as exc:
            pytest.fail(
                f"A correct abstract _receive_frame_loop SHOULD raise NotImplementedError, "
                f"not {type(exc).__name__}. Detects wrong-exception-type mutation."
            )

    def test_mutation_override_called_not_base(self):
        """
        Mutation: polymorphic dispatch broken – base method called instead of override.
        Distinguishing input: subclass with a detectable side effect.
        A correct implementation SHOULD dispatch to the most-derived override.
        """
        sentinel = []

        class SentinelProtocol(WebSocketProtocol):
            async def _receive_frame_loop(self):
                sentinel.append(True)

        proto = object.__new__(SentinelProtocol)

        async def run():
            await proto._receive_frame_loop()

        asyncio.get_event_loop().run_until_complete(run())
        assert sentinel == [True], (
            "Detects mutation: dispatch to base instead of override. "
            "A correct implementation SHOULD call the subclass's _receive_frame_loop."
        )

    def test_mutation_no_op_body_instead_of_raise(self):
        """
        Mutation: body replaced with 'pass' (no-op) instead of raising.
        If the base body is 'pass', calls silently succeed where they should fail.
        Verify the base class does NOT silently succeed.
        """
        proxy = MagicMock(spec=WebSocketProtocol)
        silent_return = False
        try:
            coro = WebSocketProtocol._receive_frame_loop(proxy)
            asyncio.get_event_loop().run_until_complete(coro)
            silent_return = True
        except (NotImplementedError, TypeError):
            silent_return = False

        assert not silent_return, (
            "Detects mutation: 'raise NotImplementedError()' → 'pass'. "
            "A correct abstract _receive_frame_loop MUST NOT complete silently."
        )