from python_programs.flatten import flatten

# catches: "yield y" mutated to "yield x" (wrong variable in recursive case)
def test_nested_list_yields_inner_elements():
    result = list(flatten([[1, 2], [3, 4]]))
    assert result == [1, 2, 3, 4]

# catches: "yield flatten(x)" instead of "yield x" for non-list elements (wrong return - wraps scalar in generator)
def test_flat_list_scalars_are_not_wrapped():
    result = list(flatten([1, 2, 3]))
    assert all(not hasattr(x, '__iter__') or isinstance(x, str) for x in result)
    assert result == [1, 2, 3]

# catches: "yield flatten(x)" bug - non-list leaf should yield the value itself, not a generator object
def test_scalar_elements_are_integers_not_generators():
    result = list(flatten([42]))
    assert len(result) == 1
    assert result[0] == 42
    assert not hasattr(result[0], '__next__')

# catches: isinstance check mutated (e.g., "not isinstance") - lists treated as scalars
def test_list_elements_are_recursed_not_yielded_directly():
    result = list(flatten([[1]]))
    assert result == [1]
    assert not any(isinstance(x, list) for x in result)

# catches: missing recursion (flat yield instead of recursive yield)
def test_deeply_nested_list():
    result = list(flatten([[[1]], [[2, 3]], [[[4]]]]]))
    assert sorted(result) == [1, 2, 3, 4]
    assert all(isinstance(x, int) for x in result)

# catches: off-by-one or wrong branch - empty list yields nothing
def test_empty_list_yields_nothing():
    result = list(flatten([]))
    assert result == []

# catches: "yield y" mutated to skip yield (missing yield in recursive branch)
def test_nested_list_count_matches():
    inp = [[1, 2], [3, [4, 5]]]
    result = list(flatten(inp))
    assert len(result) == 5

# catches: wrong variable "yield x" instead of "yield y" in nested for loop
def test_nested_values_correct_order():
    result = list(flatten([[10, 20], [30]]))
    assert result[0] == 10
    assert result[1] == 20
    assert result[2] == 30

# catches: "yield flatten(x)" for non-list - value should not be a generator
def test_string_scalar_yielded_directly():
    result = list(flatten(["hello", "world"]))
    assert result == ["hello", "world"]
    assert all(isinstance(x, str) for x in result)

# catches: recursion not entered - mixed flat and nested
def test_mixed_flat_and_nested():
    result = list(flatten([1, [2, 3], 4, [5, [6]]]))
    assert result == [1, 2, 3, 4, 5, 6]
    assert all(isinstance(x, int) for x in result)

# catches: "for y in flatten(x)" replaced by direct yield - skips sub-nesting
def test_triple_nested():
    result = list(flatten([[[42]]]))
    assert result == [42]

# property: all elements of flattened result are non-list
def test_no_lists_in_output():
    result = list(flatten([[1, [2]], [3, [4, [5]]]]))
    assert not any(isinstance(x, list) for x in result)

# catches: wrong branch - single-element list
def test_single_element_nested():
    result = list(flatten([[99]]))
    assert result == [99]