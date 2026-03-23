import pytest
from more_itertools.recipes import iter_except

# path: first is None → suppress catches exception on first func() call → loop zero iterations
def test_iter_except_first_none_immediate_exception():
    l = []
    result = list(iter_except(l.pop, IndexError))
    assert result == []

# path: first is None → suppress catches exception after some yields → loop some iterations
def test_iter_except_first_none_multiple_yields():
    l = [0, 1, 2]
    result = list(iter_except(l.pop, IndexError))
    assert result == [2, 1, 0]

# path: first is not None → first() raises exception → suppress catches → loop zero iterations
def test_iter_except_first_raises_exception():
    def raise_index_error():
        raise IndexError
    result = list(iter_except(lambda: None, IndexError, first=raise_index_error))
    assert result == []

# path: first is not None → first() yields → loop zero iterations (exception on first func() call)
def test_iter_except_first_yields_then_immediate_exception():
    call_count = 0
    def func():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return 'first'
        else:
            raise IndexError
    result = list(iter_except(func, IndexError, first=lambda: 'first'))
    assert result == ['first']

# path: first is not None → first() yields → loop some iterations → exception stops
def test_iter_except_first_yields_then_multiple_yields():
    l = [0, 1, 2]
    first_called = False
    def first():
        nonlocal first_called
        first_called = True
        return 'first'
    result = list(iter_except(l.pop, IndexError, first=first))
    assert first_called is True
    assert result == ['first', 2, 1, 0]

# path: multiple exceptions specified → first is None → suppress catches exception after some yields
def test_iter_except_multiple_exceptions():
    l = [1, 2, 3, '...', 4, 5, 6]
    result = list(iter_except(lambda: 1 + l.pop(), (IndexError, TypeError)))
    assert result == [7, 6, 5]

# path: multiple exceptions specified → first is not None → first() yields → loop some iterations → exception stops
def test_iter_except_multiple_exceptions_with_first():
    l = [1, 2, 3]
    first_called = False
    def first():
        nonlocal first_called
        first_called = True
        return 99
    result = list(iter_except(lambda: 1 + l.pop(), (IndexError, TypeError), first=first))
    assert first_called is True
    assert result == [99, 4, 3, 2]