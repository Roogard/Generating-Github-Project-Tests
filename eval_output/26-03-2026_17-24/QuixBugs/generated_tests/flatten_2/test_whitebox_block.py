from python_programs.flatten import flatten

# Basic blocks in flatten:
# Block 1: function entry, for-loop iteration over arr
# Block 2: isinstance(x, list) is True -> for y in flatten(x): yield y
# Block 3: isinstance(x, list) is False -> yield flatten(x) (else branch)
# Block 4: loop exit / generator exhaustion

# covers: block 1, block 3, block 4 (flat list of non-list elements)
def test_flatten_flat_list():
    result = list(flatten([1, 2, 3]))
    assert result == [1, 2, 3]

# covers: block 1, block 2, block 3, block 4 (nested list triggers recursion)
def test_flatten_nested_list():
    result = list(flatten([[1, 2], [3, 4]]))
    assert result == [1, 2, 3, 4]

# covers: block 1, block 2, block 3, block 4 (deeply nested list)
def test_flatten_deeply_nested():
    result = list(flatten([[1, [2, [3]]]]))
    assert result == [1, 2, 3]

# covers: block 1, block 4 (empty list - loop body never executes)
def test_flatten_empty_list():
    result = list(flatten([]))
    assert result == []

# covers: block 1, block 2, block 3, block 4 (mixed flat and nested)
def test_flatten_mixed():
    result = list(flatten([1, [2, 3], 4]))
    assert result == [1, 2, 3, 4]

# covers: block 1, block 2, block 4 (list containing only nested lists)
def test_flatten_only_nested():
    result = list(flatten([[1], [2], [3]]))
    assert result == [1, 2, 3]

# covers: block 1, block 2, block 3, block 4 (mixed types: strings and ints)
def test_flatten_mixed_types():
    result = list(flatten([1, ['a', 'b'], 2]))
    assert result == [1, 'a', 'b', 2]

# covers: block 1, block 2, block 4 (list with empty nested lists)
def test_flatten_empty_nested():
    result = list(flatten([[], [], []]))
    assert result == []

# covers: block 1, block 3, block 4 (single non-list element)
def test_flatten_single_element():
    result = list(flatten([42]))
    assert result == [42]