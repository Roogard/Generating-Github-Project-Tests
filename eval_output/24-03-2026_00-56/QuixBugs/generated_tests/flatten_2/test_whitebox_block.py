from correct_python_programs.flatten import flatten

# Block mapping:
# block 1: for x in arr: (loop entry)
# block 2: if isinstance(x, list): (condition check)
# block 3: for y in flatten(x): yield y (if-true branch, inner loop)
# block 4: else: yield x (if-false branch)
# block 5: implicit loop continuation (back to block 1) and function exit

# covers: block 1, block 2, block 4, block 5 (empty list case)
def test_empty_list():
    result = list(flatten([]))
    assert result == []

# covers: block 1, block 2, block 4, block 5 (no nested lists)
def test_flat_list():
    result = list(flatten([1, 2, 3]))
    assert result == [1, 2, 3]

# covers: block 1, block 2, block 3, block 5 (nested list)
def test_nested_list():
    result = list(flatten([[1, 2], [3, 4]]))
    assert result == [1, 2, 3, 4]

# covers: block 1, block 2, block 3, block 5 (deeply nested list)
def test_deeply_nested_list():
    result = list(flatten([1, [2, [3, 4], 5]]))
    assert result == [1, 2, 3, 4, 5]

# covers: block 1, block 2, block 3, block 5 (mixed nesting with empty inner list)
def test_mixed_with_empty_inner():
    result = list(flatten([1, [], 2]))
    assert result == [1, 2]