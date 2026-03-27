from python_programs.flatten import flatten

# isinstance(x, list): True → recurse into nested list
def test_flatten_nested_list():
    # A nested list should be flattened to its scalar elements
    result = list(flatten([1, [2, 3], 4]))
    assert result == [1, 2, 3, 4]

# isinstance(x, list): False → yield non-list element directly
def test_flatten_flat_list():
    # A flat list of integers should remain in the same order
    result = list(flatten([1, 2, 3]))
    assert result == [1, 2, 3]

# isinstance(x, list): True (deeply nested), False (scalars mixed)
def test_flatten_deeply_nested():
    # Deeply nested lists should all be flattened
    result = list(flatten([[1, [2]], [3, [4, [5]]]]]))
    assert result == [1, 2, 3, 4, 5]

# isinstance(x, list): False → single-element list
def test_flatten_single_element():
    result = list(flatten([42]))
    assert result == [42]

# isinstance(x, list): True → list containing only lists
def test_flatten_only_nested_lists():
    result = list(flatten([[1, 2], [3, 4]]))
    assert result == [1, 2, 3, 4]

# isinstance(x, list): False → strings are not lists
def test_flatten_strings():
    result = list(flatten(["a", "b", "c"]))
    assert result == ["a", "b", "c"]

# isinstance(x, list): True (inner list) and False (scalar alongside it)
def test_flatten_mixed_types():
    result = list(flatten([1, [2, "three"], 4.0]))
    assert result == [1, 2, "three", 4.0]

# isinstance(x, list): True → empty inner list contributes nothing
def test_flatten_empty_inner_list():
    result = list(flatten([1, [], 2]))
    assert result == [1, 2]

# isinstance(x, list): True → entirely empty list
def test_flatten_empty_list():
    result = list(flatten([]))
    assert result == []

# isinstance(x, list): True (outer list has list element), False (scalar elements)
def test_flatten_list_of_one_nested():
    result = list(flatten([[7]]))
    assert result == [7]