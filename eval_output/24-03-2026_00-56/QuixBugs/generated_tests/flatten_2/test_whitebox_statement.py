from correct_python_programs.flatten import flatten

# covers: for x in arr, isinstance(x, list) False, yield x
def test_flatten_single_level():
    result = list(flatten([1, 2, 3]))
    assert result == [1, 2, 3]

# covers: isinstance(x, list) True, for y in flatten(x): yield y
def test_flatten_nested():
    result = list(flatten([1, [2, 3], 4]))
    assert result == [1, 2, 3, 4]

# covers: deeper nesting, recursive flatten calls
def test_flatten_deep_nesting():
    result = list(flatten([1, [2, [3, 4]], 5]))
    assert result == [1, 2, 3, 4, 5]