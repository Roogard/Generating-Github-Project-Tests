from python_programs.flatten import flatten

# covers: for loop (iterates), isinstance True, recursive flatten call, inner for loop, yield y
def test_flatten_nested_list():
    # A correct flatten should yield all scalar values from a nested list
    result = list(flatten([1, [2, 3], [4, [5, 6]]]))
    assert result == [1, 2, 3, 4, 5, 6]
    assert len(result) == 6
    assert all(not isinstance(x, list) for x in result)

# covers: for loop (iterates), isinstance False, yield flatten(x) (else branch)
def test_flatten_flat_list():
    # A correct flatten of a flat list should yield all elements
    result = list(flatten([1, 2, 3]))
    assert len(result) == 3
    # Each yielded item should be a scalar (not a list)
    assert all(not isinstance(x, list) for x in result)

# covers: for loop body not entered (empty list)
def test_flatten_empty_list():
    # A correct flatten of an empty list should yield nothing
    result = list(flatten([]))
    assert result == []

# covers: deeply nested list — ensures recursive path is taken multiple times
def test_flatten_deeply_nested():
    # A correct flatten should handle arbitrary nesting depth
    result = list(flatten([[[[1]], [2]], [3]]]))
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)

# covers: list with single nested element
def test_flatten_single_element_nested():
    # A correct flatten of [[42]] should yield 42
    result = list(flatten([[42]]))
    assert len(result) == 1
    assert all(not isinstance(x, list) for x in result)