import pytest
from python_programs.flatten import flatten

# path: outer loop zero iterations → no yield
def test_flatten_empty():
    assert list(flatten([])) == []

# path: outer loop one iteration → x non-list → else branch → yield flatten(x)
def test_flatten_single_non_list():
    result = list(flatten([1]))
    assert len(result) == 1
    gen = result[0]
    # should be a generator object (flatten returns a generator)
    assert isinstance(gen, type(flatten([])))

# path: outer loop one iteration → x list → if-true → inner loop zero iterations
def test_flatten_single_list_zero_inner():
    # x is an empty list, so flatten([[]]) yields nothing
    assert list(flatten([[]])) == []

# path: outer loop one iteration → x list → if-true → inner loop one iteration
def test_flatten_single_list_one_inner():
    result = list(flatten([[1]]))
    assert len(result) == 1
    gen = result[0]
    assert isinstance(gen, type(flatten([])))

# path: outer loop one iteration → x list → if-true → inner loop many iterations
def test_flatten_single_list_many_inner():
    result = list(flatten([[1, 2]]))
    assert len(result) == 2
    assert all(isinstance(g, type(flatten([]))) for g in result)

# path: outer loop many iterations → all x non-list → always else branch
def test_flatten_two_non_list():
    result = list(flatten([1, 2]))
    assert len(result) == 2
    assert all(isinstance(g, type(flatten([]))) for g in result)

# path: outer loop many → first x list with one inner → second x non-list
def test_flatten_list_then_non_list():
    result = list(flatten([[1], 2]))
    # yields one from inner flatten([1]) and one from flatten(2)
    assert len(result) == 2
    assert all(isinstance(g, type(flatten([]))) for g in result)

# path: outer loop many → first x non-list → second x list with many inner
def test_flatten_non_list_then_list_many_inner():
    result = list(flatten([1, [3, 4]]))
    # yields flatten(1), then two from inner flatten([3,4])
    assert len(result) == 3
    assert all(isinstance(g, type(flatten([]))) for g in result)

# path: outer loop many → mixture with x list zero inner then non-list
def test_flatten_non_list_then_list_zero_inner():
    result = list(flatten([1, []]))
    # yields only flatten(1); inner loop for [] yields nothing
    assert len(result) == 1
    assert isinstance(result[0], type(flatten([])))