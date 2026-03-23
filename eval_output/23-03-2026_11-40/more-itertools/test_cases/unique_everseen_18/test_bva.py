import pytest
from more_itertools.recipes import iter_except
from itertools import count, islice

def test_iter_except_empty_list_pop_indexerror():
    l = []
    result = list(iter_except(l.pop, IndexError))
    assert result == []

def test_iter_except_single_element_list_pop_indexerror():
    l = [5]
    result = list(iter_except(l.pop, IndexError))
    assert result == [5]

def test_iter_except_two_element_list_pop_indexerror():
    l = [1, 2]
    result = list(iter_except(l.pop, IndexError))
    assert result == [2, 1]

def test_iter_except_with_first_none():
    l = [0, 1, 2]
    result = list(iter_except(l.pop, IndexError, first=None))
    assert result == [2, 1, 0]

def test_iter_except_with_first_provided():
    l = [0, 1, 2]
    result = list(iter_except(l.pop, IndexError, first=lambda: -1))
    assert result == [-1, 2, 1, 0]

def test_iter_except_with_first_provided_empty_list():
    l = []
    result = list(iter_except(l.pop, IndexError, first=lambda: -1))
    assert result == [-1]

def test_iter_except_multiple_exceptions_single():
    l = [1, 2, 3, '...', 4, 5, 6]
    result = list(iter_except(lambda: 1 + l.pop(), (IndexError, TypeError)))
    assert result == [7, 6, 5]

def test_iter_except_multiple_exceptions_tuple():
    l = [1, 2, 3, '...', 4, 5, 6]
    result = list(iter_except(lambda: 1 + l.pop(), (IndexError, TypeError)))
    assert result == [7, 6, 5]

def test_iter_except_no_exception_raised_infinite():
    counter = count()
    iterator = iter_except(lambda: next(counter), ValueError)
    result = list(islice(iterator, 5))
    assert result == [0, 1, 2, 3, 4]

def test_iter_except_func_raises_immediately():
    def raise_immediately():
        raise ValueError("immediate")
    result = list(iter_except(raise_immediately, ValueError))
    assert result == []

def test_iter_except_func_raises_after_one():
    l = [1]
    def pop_and_raise():
        if not l:
            raise ValueError
        return l.pop()
    result = list(iter_except(pop_and_raise, ValueError))
    assert result == [1]

def test_iter_except_with_first_that_raises_exception():
    def raise_immediately():
        raise IndexError
    result = list(iter_except(lambda: None, IndexError, first=raise_immediately))
    assert result == []

def test_iter_except_with_first_valid_then_func_raises():
    l = []
    result = list(iter_except(l.pop, IndexError, first=lambda: 99))
    assert result == [99]