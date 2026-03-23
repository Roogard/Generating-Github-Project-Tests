import pytest
from more_itertools.recipes import iter_except
from itertools import islice, count

# Valid equivalence class: func raises specified exception, first is None
def test_iter_except_valid_func_raises_exception():
    l = [0, 1, 2]
    result = list(iter_except(l.pop, IndexError))
    assert result == [2, 1, 0]

# Valid equivalence class: func raises specified exception, first is provided
def test_iter_except_valid_with_first():
    l = [0, 1, 2]
    result = list(iter_except(l.pop, IndexError, first=lambda: -1))
    assert result == [-1, 2, 1, 0]

# Valid equivalence class: multiple exceptions specified
def test_iter_except_valid_multiple_exceptions():
    l = [1, 2, 3, '...', 4, 5, 6]
    result = list(iter_except(lambda: 1 + l.pop(), (IndexError, TypeError)))
    assert result == [7, 6, 5]

# Valid equivalence class: func never raises exception (infinite iterator, limited by islice)
def test_iter_except_valid_no_exception():
    counter = count(0)
    result = list(islice(iter_except(lambda: next(counter), ValueError), 5))
    assert result == [0, 1, 2, 3, 4]

# Invalid equivalence class: func is not callable
def test_iter_except_invalid_func_not_callable():
    with pytest.raises(TypeError):
        list(iter_except(123, IndexError))

# Invalid equivalence class: exception is not an exception class or tuple
def test_iter_except_invalid_exception_not_exception():
    with pytest.raises(TypeError):
        list(iter_except(lambda: 1, "not an exception"))

# Invalid equivalence class: first is provided but not callable
def test_iter_except_invalid_first_not_callable():
    with pytest.raises(TypeError):
        list(iter_except(lambda: 1, IndexError, first=123))

# Valid equivalence class: first raises the specified exception immediately
def test_iter_except_valid_first_raises_exception():
    l = []
    result = list(iter_except(l.pop, IndexError, first=lambda: l.pop()))
    assert result == []

# Valid equivalence class: exception is a tuple with multiple exception classes
def test_iter_except_valid_exception_tuple():
    class CustomError1(Exception):
        pass
    class CustomError2(Exception):
        pass
    def func():
        raise CustomError1()
    result = list(iter_except(func, (CustomError1, CustomError2)))
    assert result == []

# Invalid equivalence class: empty exception tuple
def test_iter_except_invalid_empty_exception_tuple():
    with pytest.raises(ValueError):
        list(iter_except(lambda: 1, ()))