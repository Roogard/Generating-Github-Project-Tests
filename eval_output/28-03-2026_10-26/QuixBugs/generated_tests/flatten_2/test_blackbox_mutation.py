from python_programs.flatten import flatten

# Helper to materialize the generator
def to_list(gen):
    return list(gen)

# catches: "yield flatten(x)" instead of "yield x" for non-list elements (wrong return/yield for base case)
def test_flat_list_integers():
    result = to_list(flatten([1, 2, 3]))
    assert result == [1, 2, 3]

# catches: "yield flatten(x)" instead of "yield x" — a correct flatten SHOULD yield the scalar, not a generator object
def test_single_element():
    result = to_list(flatten([42]))
    assert result == [42]

# catches: "yield flatten(x)" instead of "yield x" — elements must be scalars, not generators
def test_all_elements_are_not_lists():
    result = to_list(flatten([1, 2, 3]))
    assert all(not isinstance(x, list) for x in result)

# catches: missing recursive yield (e.g., not yielding from nested flatten)
def test_nested_one_level():
    result = to_list(flatten([[1, 2], [3, 4]]))
    assert result == [1, 2, 3, 4]

# catches: wrong variable yielded (x vs y in recursive branch)
def test_nested_two_levels():
    result = to_list(flatten([[1, [2, 3]], [4]]))
    assert result == [1, 2, 3, 4]

# catches: isinstance check inverted (not isinstance) — lists would be yielded as-is
def test_deeply_nested():
    result = to_list(flatten([[[1]], [[2, [3]]]]))
    assert result == [1, 2, 3]

# catches: "yield flatten(x)" instead of "yield x" — non-list scalars should not be generator objects
def test_element_types_are_scalars():
    result = to_list(flatten([[1, 2], 3, [4, [5]]]))
    for elem in result:
        assert not hasattr(elem, '__next__'), "Elements must be scalars, not generators"

# catches: len/count correctness — a correct flatten preserves ALL elements
def test_element_count_preserved():
    inp = [1, [2, 3], [4, [5, 6]]]
    result = to_list(flatten(inp))
    assert len(result) == 6

# catches: isinstance check uses wrong type (e.g., tuple instead of list)
def test_non_list_iterable_yielded_as_scalar():
    # tuples are NOT lists; a correct flatten should yield them as scalars
    result = to_list(flatten([(1, 2), (3,)]))
    assert result == [(1, 2), (3,)]

# catches: off-by-one or early termination — empty nested lists should produce no output
def test_empty_nested_list():
    result = to_list(flatten([[], []]))
    assert result == []

# catches: empty input — correct flatten of empty list should yield nothing
def test_empty_list():
    result = to_list(flatten([]))
    assert result == []

# catches: "yield flatten(x)" instead of "yield x" — string scalars must come through unchanged
def test_string_elements():
    result = to_list(flatten(["a", "b", "c"]))
    assert result == ["a", "b", "c"]

# catches: recursive case yielding wrong variable (y vs x confusion)
def test_mixed_flat_and_nested():
    result = to_list(flatten([1, [2, 3], 4]))
    assert result == [1, 2, 3, 4]

# catches: multiset preservation — a correct flatten keeps all duplicates
def test_duplicates_preserved():
    result = to_list(flatten([[1, 1], [2, 2]]))
    assert result == [1, 1, 2, 2]

# catches: order preservation — a correct flatten must maintain original order
def test_order_preserved():
    result = to_list(flatten([[3, 1], [4, 1, 5]]))
    assert result == [3, 1, 4, 1, 5]