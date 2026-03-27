from python_programs.flatten import flatten

# catches: "yield flatten(x)" instead of "yield x" for non-list leaf values
def test_flat_list_single_element():
    result = list(flatten([1]))
    assert result == [1]

# catches: "yield flatten(x)" instead of "yield x" — ensures leaf values are not wrapped
def test_flat_list_multiple_elements():
    result = list(flatten([1, 2, 3]))
    assert result == [1, 2, 3]

# catches: missing recursive branch — "for y in flatten(x): yield y" mutated to just "yield x"
def test_nested_list_one_level():
    result = list(flatten([[1, 2], [3, 4]]))
    assert result == [1, 2, 3, 4]

# catches: isinstance check mutated (e.g., "not isinstance" or wrong type)
def test_nested_list_triggers_recursion():
    result = list(flatten([[1]]))
    assert result == [1]

# catches: recursion depth issue — only one level of nesting flattened
def test_deeply_nested_list():
    result = list(flatten([[1, [2, [3]]]]))
    assert result == [1, 2, 3]

# catches: "yield x" swapped for "yield flatten(x)" on non-list items
def test_string_leaf_not_recursed():
    result = list(flatten(["a", "b"]))
    assert result == ["a", "b"]

# catches: isinstance(x, list) mutated to isinstance(x, (list, str)) or similar
def test_string_not_treated_as_list():
    result = list(flatten(["hello"]))
    assert result == ["hello"]

# catches: wrong variable in yield — "yield y" mutated to "yield x"
def test_nested_yields_inner_values_not_outer():
    result = list(flatten([[10, 20]]))
    assert result == [10, 20]
    assert 10 in result
    assert 20 in result
    assert len(result) == 2

# catches: early termination — loop body only processes first element
def test_multiple_nested_lists():
    result = list(flatten([[1, 2], [3, 4], [5, 6]]))
    assert result == [1, 2, 3, 4, 5, 6]

# catches: empty list handling — generator yields nothing for empty input
def test_empty_list():
    result = list(flatten([]))
    assert result == []

# catches: empty nested list yields no items
def test_nested_empty_list():
    result = list(flatten([[]]))
    assert result == []

# catches: mixed nested and flat elements
def test_mixed_nested_and_flat():
    result = list(flatten([1, [2, 3], 4]))
    assert result == [1, 2, 3, 4]

# catches: "yield y" mutated to "yield flatten(y)" — double-wrapping generators
def test_no_generator_objects_in_output():
    import types
    result = list(flatten([1, [2, 3]]))
    for item in result:
        assert not isinstance(item, types.GeneratorType)

# catches: wrong branch taken — list items incorrectly going to else branch
def test_inner_list_not_yielded_as_object():
    result = list(flatten([[1, 2]]))
    for item in result:
        assert not isinstance(item, list)

# catches: off-by-one or wrong variable — order of elements preserved
def test_order_preserved():
    result = list(flatten([[3, 1], [4, 1], [5, 9]]))
    assert result == [3, 1, 4, 1, 5, 9]