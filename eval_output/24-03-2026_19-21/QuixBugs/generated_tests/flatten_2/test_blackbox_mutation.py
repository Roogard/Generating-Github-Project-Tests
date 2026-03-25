from python_programs.flatten import flatten

# catches: else branch mis-yields flatten(x) instead of x (wrong variable/return)
def test_flatten_simple_list():
    assert list(flatten([1, 2, 3])) == [1, 2, 3]

# catches: missing recursion into one-level nested lists (recursion omission)
def test_flatten_nested_list():
    assert list(flatten([1, [2, 3], 4])) == [1, 2, 3, 4]

# catches: failing to recurse through deeper nesting levels (boundary recursion error)
def test_flatten_deeply_nested():
    data = [1, [2, [3, [4]]], 5]
    assert list(flatten(data)) == [1, 2, 3, 4, 5]

# catches: off-by-one or improper handling of empty lists (should produce no output)
def test_flatten_empty_and_nested_empty():
    assert list(flatten([[], [[], []], []])) == []

# catches: wrong type check mutation (e.g., only list types should recurse)
def test_flatten_with_non_list_iterable():
    assert list(flatten([(1, 2), [3, 4]])) == [(1, 2), 3, 4]

# catches: else branch mis-yields flatten(x) for various non-list types
def test_flatten_various_types():
    input_data = [None, [False, [0]], 'a']
    # Expected flattened: None, False, 0, 'a'
    assert list(flatten(input_data)) == [None, False, 0, 'a']