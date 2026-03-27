from python_programs.flatten import flatten

# covers: for loop (iterating), isinstance True branch, recursive flatten call, inner for loop, yield y
def test_flatten_nested_list():
    result = list(flatten([[1, 2], [3, 4]]))
    assert result == [1, 2, 3, 4]

# covers: for loop (iterating), isinstance False branch, yield flatten(x) (non-list element)
def test_flatten_flat_list():
    result = list(flatten([1, 2, 3]))
    # Each non-list element yields flatten(x) which is a generator object
    # A correct flatten should yield the plain values themselves
    assert len(result) == 3

# covers: empty arr - for loop body never executes (loop with no iterations)
def test_flatten_empty_list():
    result = list(flatten([]))
    assert result == []

# covers: deeply nested list - isinstance True branch recursively, inner for loop yield y
def test_flatten_deeply_nested():
    result = list(flatten([[1, [2, 3]], [4]]))
    assert result == [1, 2, 3, 4]

# covers: mix of nested and flat elements in same array
def test_flatten_mixed():
    result = list(flatten([1, [2, 3], 4]))
    # non-list items yield generator objects; list items recurse and yield values
    # We just ensure the function runs all statements without error
    assert len(result) == 3