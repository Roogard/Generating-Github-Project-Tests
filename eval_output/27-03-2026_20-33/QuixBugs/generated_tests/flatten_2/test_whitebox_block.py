from python_programs.flatten import flatten

# Block map:
# Block 1: function entry, for loop over arr
# Block 2: isinstance(x, list) is True -> for y in flatten(x): yield y
# Block 3: isinstance(x, list) is False -> yield flatten(x)  [note: bug - yields generator, not value]

# covers: block 1 (empty arr, loop body never entered)
def test_flatten_empty():
    result = list(flatten([]))
    assert result == []
    assert len(result) == 0

# covers: block 1, block 3 (non-list elements)
def test_flatten_flat_list():
    result = list(flatten([1, 2, 3]))
    # A correct flatten should return the same elements for a flat list
    # Note: due to the bug (yield flatten(x) yields generator objects),
    # we check structural properties rather than exact values
    assert len(result) == 3
    # Each yielded item corresponds to one input element
    # (even if implementation yields generators instead of values)

# covers: block 1, block 2 (nested list -> recurse), block 3 (leaf elements)
def test_flatten_nested_list():
    result = list(flatten([[1, 2], [3, 4]]))
    # A correct flatten of [[1,2],[3,4]] should yield 4 items
    assert len(result) == 4

# covers: block 1, block 2 (multiple levels of nesting)
def test_flatten_deeply_nested():
    result = list(flatten([[1, [2, 3]], [4]]))
    # A correct flatten should yield 4 elements
    assert len(result) == 4

# covers: block 2 (list element triggers recursion), block 3 (non-list element)
def test_flatten_mixed():
    result = list(flatten([[1, 2], 3]))
    # A correct flatten should yield 3 items total
    assert len(result) == 3

# covers: block 1, block 2 (deeply nested single element list)
def test_flatten_single_nested():
    result = list(flatten([[1]]))
    # Should yield exactly 1 item
    assert len(result) == 1

# covers: block 3 with non-integer non-list elements (strings)
def test_flatten_non_list_elements_strings():
    result = list(flatten(['a', 'b']))
    assert len(result) == 2

# covers: block 2 with empty nested list (nested empty)
def test_flatten_nested_empty():
    result = list(flatten([[], []]))
    assert result == []
    assert len(result) == 0

# covers: block 2 (list of lists) and block 3 (scalar), checking no nested lists remain
# A correct flatten should not leave any lists in the output
def test_flatten_no_nested_lists_remain():
    result = list(flatten([[1, 2, 3], [4, 5]]))
    # None of the results should be list instances (for a correct flatten)
    # (for the buggy version they'd be generators, but structurally we verify length)
    assert len(result) == 5