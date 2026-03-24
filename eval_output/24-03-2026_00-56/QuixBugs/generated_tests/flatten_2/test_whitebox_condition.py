from correct_python_programs.flatten import flatten

# condition: isinstance(x, list): True
def test_flatten_nested_list():
    result = list(flatten([[1, 2], [3, 4]]))
    assert result == [1, 2, 3, 4]

# condition: isinstance(x, list): False
def test_flatten_flat_list():
    result = list(flatten([1, 2, 3]))
    assert result == [1, 2, 3]

# condition: isinstance(x, list): True (deep nesting)
def test_flatten_deeply_nested():
    result = list(flatten([1, [2, [3, 4]], 5]))
    assert result == [1, 2, 3, 4, 5]

# condition: isinstance(x, list): False (empty list case)
def test_flatten_empty_list():
    result = list(flatten([]))
    assert result == []

# condition: isinstance(x, list): True (empty nested list)
def test_flatten_nested_empty_list():
    result = list(flatten([[], 1, []]))
    assert result == [1]