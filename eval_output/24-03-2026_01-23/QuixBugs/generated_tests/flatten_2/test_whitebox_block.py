from python_programs.flatten import flatten
import types
import pytest

# covers: block1 only (entry and loop over arr), no iterations
def test_empty_list():
    assert list(flatten([])) == []

# covers: block1 and block3 (else branch when x is not a list)
def test_non_list_element():
    result = list(flatten([1]))
    # Should yield one item, which is the generator returned by flatten(1)
    assert len(result) == 1
    assert isinstance(result[0], types.GeneratorType)

# covers: block1, block2 (when x is a list), and inner block3 for non-list inside nested list
def test_nested_list_generator_and_inner_error():
    result = list(flatten([[1]]))
    assert len(result) == 1
    inner_gen = result[0]
    # The inner generator comes from flatten(1); iterating it should raise a TypeError
    with pytest.raises(TypeError):
        next(inner_gen)