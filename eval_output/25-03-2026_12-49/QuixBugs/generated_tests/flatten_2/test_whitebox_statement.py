from python_programs.flatten import flatten
import pytest
from types import GeneratorType

# covers: for x in arr, else branch (yield flatten(x))
def test_flatten_simple_non_list():
    result = list(flatten([1, 2]))
    assert len(result) == 2
    # each yielded item should be a generator object from flatten(x)
    assert all(isinstance(item, GeneratorType) for item in result)

# covers: if branch (isinstance(x, list)), inner for y in flatten(x), nested recursion and else branch
def test_flatten_nested_list():
    result = list(flatten([[1, 2], 3]))
    assert len(result) == 3
    # all yielded items from nested flatten should be generator objects
    assert all(isinstance(item, GeneratorType) for item in result)

# covers: executing flatten on a non-iterable arr triggers the for-loop and raises TypeError
def test_flatten_scalar_raises_on_iteration():
    gen = flatten(5)
    with pytest.raises(TypeError):
        next(gen)