from python_programs.flatten import flatten
import types
import pytest

# condition: isinstance(x, list) = False for all x in [1,2,3]
def test_flatten_atomic_list_false():
    output = list(flatten([1, 2, 3]))
    assert len(output) == 3
    for elem in output:
        # each yielded element is a generator from flatten(x)
        assert isinstance(elem, types.GeneratorType)

# condition: isinstance(x, list) = True for x = [], yields no items
def test_flatten_nested_empty_list_true():
    output = list(flatten([[]]))
    assert output == []

# condition: mixed x values: x=1 -> False, x=[2,3] -> True, x=4 -> False
def test_flatten_mixed_list_true_and_false():
    mixed = [1, [2, 3], 4]
    output = list(flatten(mixed))
    # Expect one generator for 1, two generators for 2 and 3, one for 4
    assert len(output) == 4
    for elem in output:
        assert isinstance(elem, types.GeneratorType)

# calling flatten on a non-list arr raises TypeError when iterating
def test_flatten_non_list_raises_type_error_on_iteration():
    gen = flatten(1)
    with pytest.raises(TypeError):
        next(gen)