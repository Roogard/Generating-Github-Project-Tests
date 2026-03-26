from python_programs.flatten import flatten
import pytest
from types import GeneratorType

# covers: block1 (empty array exit)
def test_empty_list():
    assert list(flatten([])) == []

# covers: block1, block4 (else branch for non-list elements)
def test_non_list_elements_yield_generator():
    result = list(flatten([1, 2, 3]))
    assert len(result) == 3
    for item in result:
        assert isinstance(item, GeneratorType)

# covers: block1, block2, block3 (nested list yields inner items)
def test_nested_list_flatten_generators():
    nested = [[1, 2], [3]]
    result = list(flatten(nested))
    # flatten([1,2]) yields 2 generators, flatten([3]) yields 1
    assert len(result) == 3
    assert all(isinstance(gen, GeneratorType) for gen in result)

# covers: block1, block2 (empty inner list), block3, block4 mixed behavior
def test_mixed_list():
    mixed = [[], [1], 2]
    result = list(flatten(mixed))
    # [] -> 0, [1] -> 1, 2 -> 1
    assert len(result) == 2
    assert isinstance(result[0], GeneratorType)
    assert isinstance(result[1], GeneratorType)

# covers: block1, loop entry exception on non-iterable arr
def test_invalid_input_non_iterable():
    with pytest.raises(TypeError):
        # consuming the generator to trigger the TypeError
        next(flatten(42))