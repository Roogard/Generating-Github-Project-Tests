from python_programs.flatten import flatten
import pytest
import types

def test_flatten_single_non_list():
    # isinstance(x,list): False
    result = list(flatten([1]))
    assert len(result) == 1
    # The implementation yields a generator for non-list x
    assert isinstance(result[0], types.GeneratorType)
    # Trying to consume the inner generator should raise TypeError (flatten(1) on int)
    with pytest.raises(TypeError):
        list(result[0])

def test_flatten_nested_list():
    # isinstance(x,list): True for the outer elements, and False for inner ints
    result = list(flatten([[1, 2], [3]]))
    # Expect one generator per integer in nested lists
    assert len(result) == 3
    for gen in result:
        assert isinstance(gen, types.GeneratorType)
    # Confirm inner generator errors when iterated (flatten on non-iterable)
    with pytest.raises(TypeError):
        list(result[0])