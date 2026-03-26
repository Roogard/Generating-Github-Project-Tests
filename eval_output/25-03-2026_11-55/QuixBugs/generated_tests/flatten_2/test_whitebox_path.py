import pytest
import types
from python_programs.flatten import flatten

# path: outer loop zero iterations (arr = [])
def test_flatten_empty():
    assert list(flatten([])) == []

# path: arr is non-iterable → TypeError on outer loop
def test_flatten_non_iterable():
    with pytest.raises(TypeError):
        list(flatten(1))

# path: outer loop one iteration, branch false (x not a list)
def test_flatten_single_non_list():
    gens = list(flatten([42]))
    assert len(gens) == 1
    g = gens[0]
    assert isinstance(g, types.GeneratorType)
    # iterating inner generator on non-iterable should error
    with pytest.raises(TypeError):
        list(g)

# path: outer loop one iteration, branch true, inner loop zero iterations (empty sublist)
def test_flatten_single_list_empty():
    assert list(flatten([[]])) == []

# path: outer loop one iteration, branch true, inner loop one iteration
def test_flatten_single_list_single():
    gens = list(flatten([[99]]))
    assert len(gens) == 1
    g = gens[0]
    assert isinstance(g, types.GeneratorType)
    with pytest.raises(TypeError):
        list(g)

# path: outer loop one iteration, branch true, inner loop many iterations
def test_flatten_single_list_multiple():
    gens = list(flatten([[1, 2, 3]]))
    assert len(gens) == 3
    for g in gens:
        assert isinstance(g, types.GeneratorType)
        with pytest.raises(TypeError):
            list(g)

# path: outer loop many iterations, mixed branches
def test_flatten_mixed_branches():
    data = [7, [8, 9], 10]
    gens = list(flatten(data))
    # Expect four yielded generators: 7, then 8 & 9 from the sublist, then 10
    assert len(gens) == 4
    for g in gens:
        assert isinstance(g, types.GeneratorType)
        with pytest.raises(TypeError):
            list(g)