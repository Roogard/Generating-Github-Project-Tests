from python_programs.flatten import flatten

# isinstance(x, list): True (x is a list, recurse into it)
def test_flatten_nested_list():
    result = list(flatten([[1, 2], [3, 4]]))
    assert result == [1, 2, 3, 4]

# isinstance(x, list): False (x is an integer, yield directly)
def test_flatten_flat_list():
    result = list(flatten([1, 2, 3]))
    assert result == [1, 2, 3]

# isinstance(x, list): True for outer, False for inner elements
def test_flatten_mixed_nested():
    result = list(flatten([1, [2, 3], 4]))
    assert result == [1, 2, 3, 4]

# isinstance(x, list): True multiple levels deep (deeply nested)
def test_flatten_deeply_nested():
    result = list(flatten([[1, [2, [3]]]]))
    assert result == [1, 2, 3]

# isinstance(x, list): True (empty list inside)
def test_flatten_empty_inner_list():
    result = list(flatten([[], 1, 2]))
    assert result == [1, 2]

# isinstance(x, list): never True (empty outer list, loop never executes)
def test_flatten_empty_list():
    result = list(flatten([]))
    assert result == []

# isinstance(x, list): False for string elements
def test_flatten_strings():
    result = list(flatten(['a', 'b', 'c']))
    assert result == ['a', 'b', 'c']

# isinstance(x, list): True (list containing only lists)
def test_flatten_list_of_lists():
    result = list(flatten([[1], [2], [3]]))
    assert result == [1, 2, 3]

# isinstance(x, list): True and False in same call (mixed types)
def test_flatten_mixed_types():
    result = list(flatten([1, [2, 3], 'hello', [4]]))
    assert result == [1, 2, 3, 'hello', 4]

# isinstance(x, list): True for multiply nested, False for leaf integers
def test_flatten_triple_nested():
    result = list(flatten([[[1, 2], 3], [4, [5]]]))
    assert result == [1, 2, 3, 4, 5]