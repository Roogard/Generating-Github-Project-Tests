from more_itertools.recipes import iter_except
from itertools import islice

# condition: exception raised by func: False (first iteration), exception raised by func: True (stop iteration)
def test_iter_except_no_exception_first_none():
    # func never raises exception, first is None
    # exception raised by func: False (loop continues indefinitely)
    # We'll limit with islice to avoid infinite loop
    result = list(islice(iter_except(lambda: 1, ValueError), 3))
    assert result == [1, 1, 1]

# condition: exception raised by func: False (first iteration), exception raised by func: True (stop iteration)
def test_iter_except_with_exception_first_none():
    # func raises exception immediately
    # exception raised by func: True (loop stops)
    calls = []
    def func():
        calls.append(1)
        raise IndexError
    result = list(iter_except(func, IndexError))
    assert result == []
    # The function is called once because iter_except tries to call func() in the first iteration
    # The suppress context manager catches the exception and stops iteration
    assert calls == [1]

# condition: first is not None: True, exception raised by first: False, exception raised by func: False (first iteration), exception raised by func: True (stop iteration)
def test_iter_except_with_first_no_exception():
    # first yields a value, func yields values until exception
    # first is not None: True, exception raised by first: False, exception raised by func: False initially, then True
    pop_list = [1, 2, 3]
    def first():
        return pop_list.pop() + 10
    result = list(iter_except(pop_list.pop, IndexError, first=first))
    # first yields 13, then pop yields 2, 1, then stops
    assert result == [13, 2, 1]
    assert pop_list == []

# condition: first is not None: True, exception raised by first: True
def test_iter_except_first_raises_exception():
    # first raises the specified exception, so nothing is yielded
    # first is not None: True, exception raised by first: True
    def first():
        raise ValueError
    result = list(iter_except(lambda: 1, ValueError, first=first))
    assert result == []

# condition: first is not None: False
def test_iter_except_first_is_none():
    # first is None, so only func is called
    # first is not None: False
    pop_list = [1, 2]
    result = list(iter_except(pop_list.pop, IndexError, first=None))
    assert result == [2, 1]
    assert pop_list == []

# condition: exception raised by func: False (multiple iterations), exception raised by func: True (stop iteration)
def test_iter_except_multiple_exceptions():
    # func raises one of multiple exceptions after some calls
    # exception raised by func: False initially, then True
    l = [1, 2, 'a', 3]
    def func():
        val = l.pop()
        if isinstance(val, str):
            raise TypeError
        return val
    result = list(iter_except(func, (IndexError, TypeError)))
    # pops 3, then 'a' raises TypeError and stops
    assert result == [3]
    assert l == [1, 2]