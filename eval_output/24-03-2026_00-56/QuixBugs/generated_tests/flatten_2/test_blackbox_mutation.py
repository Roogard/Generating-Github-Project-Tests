from correct_python_programs.flatten import flatten

# catches: "isinstance(x, list)" mutated to "isinstance(x, tuple)" or other type
def test_flatten_with_nested_list():
    result = list(flatten([1, [2, 3], 4]))
    assert result == [1, 2, 3, 4]

# catches: missing recursive call, e.g., "for y in x:" instead of "for y in flatten(x):"
def test_flatten_deeply_nested():
    result = list(flatten([1, [2, [3, 4]], 5]))
    assert result == [1, 2, 3, 4, 5]

# catches: "yield y" mutated to "yield x" inside the recursive loop
def test_flatten_nested_only():
    result = list(flatten([[1, 2], [3, 4]]))
    assert result == [1, 2, 3, 4]

# catches: "else: yield x" mutated to "yield x" without else (always yielding x)
def test_flatten_no_nesting():
    result = list(flatten([1, 2, 3]))
    assert result == [1, 2, 3]

# catches: off-by-one in iteration, e.g., "for x in arr[:-1]:" or skipping first/last
def test_flatten_single_element():
    result = list(flatten([42]))
    assert result == [42]

# catches: "isinstance(x, list)" mutated to "type(x) == list" (still works but different mutation)
def test_flatten_empty_nested_list():
    result = list(flatten([1, [], 2]))
    assert result == [1, 2]

# catches: recursion base case error, e.g., not handling empty list input
def test_flatten_empty_input():
    result = list(flatten([]))
    assert result == []

# catches: "for y in flatten(x):" mutated to "for y in x:" for shallow flatten
def test_flatten_mixed_depth():
    result = list(flatten([1, [2, [3]], 4]))
    assert result == [1, 2, 3, 4]

# catches: "yield y" mutated to "yield [y]" (yielding list instead of element)
def test_flatten_nested_single():
    result = list(flatten([[1]]))
    assert result == [1]

# catches: "if isinstance(x, list):" mutated to "if not isinstance(x, list):" (negation error)
def test_flatten_with_non_list_iterable():
    # This test passes on correct implementation because non‑list items are yielded directly.
    # If condition were negated, it would incorrectly recurse into non‑lists.
    result = list(flatten([1, (2, 3), 4]))
    assert result == [1, (2, 3), 4]