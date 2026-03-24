from python_programs.flatten import flatten
import pytest
import types

# covers: stmt1 (no iterations)
def test_flatten_empty():
    assert list(flatten([])) == []

# covers: stmt1 (iteration), stmt2 False branch, stmt5
def test_flatten_non_list_element():
    result = list(flatten([42]))
    assert len(result) == 1
    gen = result[0]
    assert isinstance(gen, types.GeneratorType)
    # the yielded generator should raise when iterated
    with pytest.raises(TypeError):
        list(gen)

# covers: stmt1, stmt2 True branch, stmt3, stmt4
def test_flatten_single_list_element():
    result = list(flatten([[99]]))
    assert len(result) == 1
    gen = result[0]
    assert isinstance(gen, types.GeneratorType)
    # inner generator also errors on non-iterable
    with pytest.raises(TypeError):
        list(gen)

# covers: stmt1 entry, raises on non-iterable arr
def test_flatten_non_iterable_arr_raises():
    with pytest.raises(TypeError):
        list(flatten(123))