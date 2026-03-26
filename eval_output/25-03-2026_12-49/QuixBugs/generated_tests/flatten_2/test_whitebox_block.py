from python_programs.flatten import flatten
import types

# covers: function entry and immediate exit when arr is empty (no loop iterations)
def test_flatten_empty():
    assert list(flatten([])) == []

# covers: if-branch when arr contains an empty list, inner for has zero iterations
def test_flatten_empty_nested():
    assert list(flatten([[]])) == []

# covers: else-branch for non-list elements, yields flatten(x) as a generator
def test_flatten_non_list():
    result = list(flatten([1]))
    assert len(result) == 1
    assert isinstance(result[0], types.GeneratorType)

# covers: if-branch for single-level nested list, inner for and yield y from recursive call
def test_flatten_single_nested():
    result = list(flatten([[1]]))
    assert len(result) == 1
    # the yielded item should itself be a generator for flatten(1)
    assert isinstance(result[0], types.GeneratorType)

# covers: multiple iterations over arr, mixing non-list and list branches and multiple yields
def test_flatten_mixed():
    arr = [1, [2, 3], 4]
    result = list(flatten(arr))
    # should yield four generator objects: flatten(1), flatten(2), flatten(3), flatten(4)
    assert len(result) == 4
    for item in result:
        assert isinstance(item, types.GeneratorType)