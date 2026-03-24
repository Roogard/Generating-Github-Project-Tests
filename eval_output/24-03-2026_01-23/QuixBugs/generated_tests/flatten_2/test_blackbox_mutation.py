from python_programs.flatten import flatten

# catches: empty list should produce no elements (boundary error)
def test_flatten_empty_list():
    assert list(flatten([])) == []

# catches: wrong base-case yield (yielding generator instead of element)
def test_flatten_single_element():
    assert list(flatten([42])) == [42]

# catches: missing recursion into sublist (detects only one-level flatten)
def test_flatten_nested_list():
    assert list(flatten([1, [2, 3], 4])) == [1, 2, 3, 4]

# catches: insufficient deep recursion (only flattens one level)
def test_flatten_deeply_nested_list():
    data = [1, [2, [3, [4]], 5], 6]
    assert list(flatten(data)) == [1, 2, 3, 4, 5, 6]

# catches: treating non-list iterables as lists (e.g., flattening tuples)
def test_flatten_tuple_preserved():
    tup = (7, 8)
    data = [1, tup, [9]]
    assert list(flatten(data)) == [1, tup, 9]

# catches: incorrect handling of multiple empty sublists
def test_flatten_multiple_empty_sublists():
    data = [[], [[], []], []]
    assert list(flatten(data)) == []