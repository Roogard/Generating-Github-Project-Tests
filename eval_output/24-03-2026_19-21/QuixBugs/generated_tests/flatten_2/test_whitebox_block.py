from python_programs.flatten import flatten
import pytest

# covers: block1 (empty loop, no iterations)
def test_empty_list():
    assert list(flatten([])) == []

# covers: block1, block4 (else branch yield of flatten(x))
def test_nonlist_elements_yield_generators():
    arr = [1, 2]
    gens = list(flatten(arr))
    assert len(gens) == 2
    for g in gens:
        assert isinstance(g, type(flatten([])))

# covers: block4 (yield of flatten(x)), and inner flatten block1 error on non-iterable arr
def test_inner_generator_raises_type_error():
    gen = flatten([1])
    inner = next(gen)
    with pytest.raises(TypeError):
        next(inner)

# covers: block2 and block3 (recursion into list, yielding values)
def test_flatten_pure_nested_lists():
    data = [[1], [2, 3]]
    assert list(flatten(data)) == [1, 2, 3]

# covers: block2 with empty sublist (loop over flatten(x) that yields nothing)
def test_flatten_nested_empty_lists():
    assert list(flatten([[[]]])) == []