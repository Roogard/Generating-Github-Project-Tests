import pytest
import types
from python_programs.flatten import flatten

# path: outer loop zero iterations → exit immediately
def test_flatten_empty():
    assert list(flatten([])) == []

# path: entry with non-iterable arr → TypeError on iteration
def test_flatten_non_iterable():
    with pytest.raises(TypeError):
        list(flatten(1))

# path: outer one iteration → x not list → else branch → yield flatten(x)
def test_flatten_single_non_list():
    result = list(flatten([42]))
    assert len(result) == 1
    assert isinstance(result[0], types.GeneratorType)

# path: outer one iteration → x is list → if-true → inner loop zero iterations
def test_flatten_single_empty_list():
    assert list(flatten([[]])) == []

# path: outer one iteration → x is list → if-true → inner loop one iteration
def test_flatten_single_list_one_item():
    result = list(flatten([[99]]))
    assert len(result) == 1
    assert isinstance(result[0], types.GeneratorType)

# path: outer one iteration → x is list → if-true → inner loop multiple iterations
def test_flatten_single_list_multiple_items():
    result = list(flatten([[1, 2, 3]]))
    assert len(result) == 3
    for g in result:
        assert isinstance(g, types.GeneratorType)

# path: outer multiple iterations → mix else/if branches (1st else, 2nd if with one inner, 3rd else)
def test_flatten_mixed_branches():
    data = [10, [20], 30]
    result = list(flatten(data))
    assert len(result) == 3
    for g in result:
        assert isinstance(g, types.GeneratorType)