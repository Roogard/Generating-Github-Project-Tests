from python_programs.flatten import flatten

# Helper to collect generator results into a list
def collect(gen):
    return list(gen)

# isinstance(x, list): True → recurse into nested list
# isinstance(x, list): False → yield scalar element
def test_flatten_single_nested_list():
    # A correct flatten of [[1, 2], 3] should yield 1, 2, 3
    result = collect(flatten([[1, 2], 3]))
    assert result == [1, 2, 3]
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)

# isinstance(x, list): False for all elements → all scalars yielded directly
def test_flatten_all_scalars():
    # A correct flatten of [1, 2, 3] should yield 1, 2, 3
    result = collect(flatten([1, 2, 3]))
    assert result == [1, 2, 3]
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)

# isinstance(x, list): True for all elements → recurse into each
def test_flatten_all_nested_lists():
    # A correct flatten of [[1], [2], [3]] should yield 1, 2, 3
    result = collect(flatten([[1], [2], [3]]))
    assert result == [1, 2, 3]
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)

# isinstance(x, list): True (deeply nested) → recursive flattening
def test_flatten_deeply_nested():
    # A correct flatten of [[[1, 2]], [3]] should yield 1, 2, 3
    result = collect(flatten([[[1, 2]], [3]]))
    assert result == [1, 2, 3]
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)

# isinstance(x, list): True and False mixed → compound nesting
def test_flatten_mixed_nesting():
    # A correct flatten of [1, [2, 3], 4, [5]] should yield 1, 2, 3, 4, 5
    result = collect(flatten([1, [2, 3], 4, [5]]))
    assert result == [1, 2, 3, 4, 5]
    assert len(result) == 5
    assert all(not isinstance(x, list) for x in result)

# isinstance(x, list): True for empty list → no elements yielded from it
def test_flatten_contains_empty_list():
    # A correct flatten of [1, [], 2] should yield 1, 2
    result = collect(flatten([1, [], 2]))
    assert result == [1, 2]
    assert len(result) == 2
    assert all(not isinstance(x, list) for x in result)

# Empty outer array → no iterations at all
def test_flatten_empty_array():
    # A correct flatten of [] should yield nothing
    result = collect(flatten([]))
    assert result == []
    assert len(result) == 0

# isinstance(x, list): False → single scalar element
def test_flatten_single_scalar():
    # A correct flatten of [42] should yield 42
    result = collect(flatten([42]))
    assert result == [42]
    assert len(result) == 1
    assert all(not isinstance(x, list) for x in result)

# isinstance(x, list): True with multiple levels and scalars at each level
def test_flatten_multi_level_mixed():
    # A correct flatten of [[1, [2, 3]], 4] should yield 1, 2, 3, 4
    result = collect(flatten([[1, [2, 3]], 4]))
    assert result == [1, 2, 3, 4]
    assert len(result) == 4
    assert all(not isinstance(x, list) for x in result)