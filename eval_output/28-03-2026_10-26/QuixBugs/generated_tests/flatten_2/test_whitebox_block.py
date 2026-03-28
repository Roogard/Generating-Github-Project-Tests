from python_programs.flatten import flatten

# Basic blocks in flatten:
# Block 1: function entry, for-loop over arr
# Block 2: isinstance(x, list) is True -> recurse, for y in flatten(x): yield y
# Block 3: isinstance(x, list) is False -> yield flatten(x)  [else branch]
# (also: loop exit / function return when arr is exhausted)

# A correct flatten should yield all scalar (non-list) values from a nested list structure,
# with no nested lists remaining in the output.

# covers: Block 1 (entry), Block 2 (nested list branch), loop over recursion results
def test_flatten_nested_list():
    result = list(flatten([[1, 2], [3, 4]]))
    # A correct flatten of [[1,2],[3,4]] should yield 1, 2, 3, 4
    assert result == [1, 2, 3, 4]
    assert len(result) == 4
    assert all(not isinstance(x, list) for x in result)

# covers: Block 1 (entry), Block 3 (non-list element branch), loop exit
def test_flatten_flat_list():
    result = list(flatten([1, 2, 3]))
    # A correct flatten of a flat list of scalars should yield those scalars
    assert result == [1, 2, 3]
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)

# covers: Block 1 (entry, empty arr), immediate loop exit
def test_flatten_empty_list():
    result = list(flatten([]))
    # A correct flatten of an empty list should yield nothing
    assert result == []

# covers: Block 1, Block 2 (deeply nested), Block 3 (scalar at leaf)
def test_flatten_deeply_nested():
    result = list(flatten([[[1]], [[2, 3]], [[[4]]]]]))
    # A correct flatten should extract all scalars regardless of nesting depth
    assert result == [1, 2, 3, 4]
    assert len(result) == 4
    assert all(not isinstance(x, list) for x in result)

# covers: Block 3 with non-integer scalar types (strings)
def test_flatten_with_strings():
    result = list(flatten(['a', 'b', 'c']))
    # A correct flatten of a flat list of strings should yield those strings
    assert result == ['a', 'b', 'c']
    assert len(result) == 3

# covers: Block 1, Block 2 (list branch), Block 3 (non-list branch), mixed
def test_flatten_mixed():
    result = list(flatten([1, [2, 3], 4, [5, [6]]]))
    # A correct flatten should yield scalars in order: 1, 2, 3, 4, 5, 6
    assert result == [1, 2, 3, 4, 5, 6]
    assert len(result) == 6
    assert all(not isinstance(x, list) for x in result)

# covers: Block 3 with a single non-list element
def test_flatten_single_element():
    result = list(flatten([42]))
    # A correct flatten of a single-element flat list should yield that element
    assert result == [42]
    assert len(result) == 1

# covers: Block 2 with an empty nested list (inner loop body never executes)
def test_flatten_nested_empty_list():
    result = list(flatten([[], []]))
    # A correct flatten of lists containing only empty lists should yield nothing
    assert result == []