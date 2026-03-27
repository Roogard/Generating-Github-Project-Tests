from python_programs.flatten import flatten

# covers: for loop (iterating), isinstance True branch, recursive flatten call, inner for loop, yield y
def test_flatten_nested_list():
    result = list(flatten([1, [2, 3], [4, [5, 6]]]))
    assert result == [1, 2, 3, 4, 5, 6]

# covers: for loop (iterating), isinstance False branch, yield flatten(x) for non-list element
def test_flatten_flat_list():
    result = list(flatten([1, 2, 3]))
    assert result == [1, 2, 3]

# covers: for loop body not entered (empty list)
def test_flatten_empty_list():
    result = list(flatten([]))
    assert result == []

# covers: deeply nested list to ensure recursive flattening executes multiple levels
def test_flatten_deeply_nested():
    result = list(flatten([[[ 1 ]], [2]]))
    assert result == [1, 2]

# covers: single element list (non-list element), yield flatten(x)
def test_flatten_single_element():
    result = list(flatten([42]))
    assert result == [42]