from python_programs.flatten import flatten
import types

# covers: iteration over arr, else branch yield flatten(x)
def test_flatten_single_non_list():
    result = list(flatten([1]))
    assert len(result) == 1
    # the single item should be a generator returned by flatten(1)
    assert isinstance(result[0], types.GeneratorType)

# covers: iteration over arr, True branch, recursive call flatten(x), nested for y, yield y
def test_flatten_nested_list():
    nested = [ [10, 20] ]
    result = list(flatten(nested))
    # should yield two items, each a generator from flatten on non-lists 10 and 20
    assert len(result) == 2
    assert all(isinstance(item, types.GeneratorType) for item in result)