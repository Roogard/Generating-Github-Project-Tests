from python_programs.flatten import flatten

# covers: for loop body (x is a list), recursive flatten call, inner for loop, yield y
def test_flatten_nested_list():
    result = list(flatten([[1, 2], [3, 4]]))
    # A correct flatten should yield all non-list leaf values
    assert len(result) == 4
    assert all(not isinstance(x, list) for x in result)
    # The values should be the integers 1,2,3,4 in order
    assert result == [1, 2, 3, 4]

# covers: for loop body (x is not a list), yield flatten(x) branch
def test_flatten_flat_list():
    result = list(flatten([1, 2, 3]))
    # A correct flatten of a flat list should yield the elements themselves
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)
    assert result == [1, 2, 3]

# covers: for loop body with deeply nested list, recursive calls, inner for loop
def test_flatten_deeply_nested():
    result = list(flatten([[[1]], [2, [3]]]))
    # A correct flatten should produce [1, 2, 3]
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)
    assert result == [1, 2, 3]

# covers: for loop not entered (empty arr), generator yields nothing
def test_flatten_empty_list():
    result = list(flatten([]))
    assert result == []
    assert len(result) == 0

# covers: single-element non-list, else branch (yield flatten(x))
def test_flatten_single_element():
    result = list(flatten([42]))
    assert len(result) == 1
    assert all(not isinstance(x, list) for x in result)
    assert result == [42]

# covers: mixed nesting levels
def test_flatten_mixed():
    result = list(flatten([1, [2, 3], [4, [5, 6]]]))
    assert len(result) == 6
    assert all(not isinstance(x, list) for x in result)
    assert result == [1, 2, 3, 4, 5, 6]