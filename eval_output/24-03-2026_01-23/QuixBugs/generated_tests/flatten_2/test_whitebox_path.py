import pytest
import types
from python_programs.flatten import flatten

# path: outer loop zero iterations
def test_flatten_empty():
    assert list(flatten([])) == []

# path: outer loop one iteration, x not list (else)
def test_flatten_single_non_list():
    result = list(flatten([1]))
    assert len(result) == 1
    gen = result[0]
    assert isinstance(gen, types.GeneratorType)
    # the inner generator will error when iterated since 1 is not iterable
    with pytest.raises(TypeError):
        next(gen)

# path: outer loop many iterations, all x not list (else repeated)
def test_flatten_multiple_non_list():
    results = list(flatten([1, 2, 3]))
    assert len(results) == 3
    for gen in results:
        assert isinstance(gen, types.GeneratorType)
        with pytest.raises(TypeError):
            next(gen)

# path: outer loop one iteration, x is list → inner flatten zero iterations
def test_flatten_single_empty_list():
    assert list(flatten([[]])) == []

# path: outer loop one iteration, x is list → inner flatten one iteration
def test_flatten_nested_single_non_list():
    results = list(flatten([[4]]))
    assert len(results) == 1
    gen = results[0]
    assert isinstance(gen, types.GeneratorType)
    with pytest.raises(TypeError):
        next(gen)

# path: outer loop one iteration, x is list → inner flatten many iterations
def test_flatten_nested_multiple_non_list():
    results = list(flatten([[5, 6]]))
    assert len(results) == 2
    for gen in results:
        assert isinstance(gen, types.GeneratorType)
        with pytest.raises(TypeError):
            next(gen)

# path: outer loop many iterations, mixed non-list then list
def test_flatten_mixed_non_list_and_list():
    arr = [7, [8, 9]]
    results = list(flatten(arr))
    # yields flatten(7), then flatten(8), flatten(9)
    assert len(results) == 3
    for gen in results:
        assert isinstance(gen, types.GeneratorType)
        with pytest.raises(TypeError):
            next(gen)