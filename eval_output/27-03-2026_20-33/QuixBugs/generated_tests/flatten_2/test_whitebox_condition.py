from python_programs.flatten import flatten

# Helper to fully consume the generator
def consume(gen):
    return list(gen)

# condition: isinstance(x, list): True → recurse into nested list
def test_flatten_nested_list_single_level():
    # x is a list: isinstance(x, list) = True
    result = consume(flatten([[1, 2, 3]]))
    # A correct flatten should yield all non-list elements
    assert all(not isinstance(item, list) for item in result)
    assert len(result) == 3

# condition: isinstance(x, list): False → yield the element directly
def test_flatten_flat_list():
    # x is not a list: isinstance(x, list) = False for each element
    result = consume(flatten([1, 2, 3]))
    assert all(not isinstance(item, list) for item in result)
    assert len(result) == 3

# condition: isinstance(x, list): True (deeply nested) and False (leaf elements)
def test_flatten_deeply_nested():
    # isinstance(x, list): True for inner lists, False for integers
    result = consume(flatten([[[1], 2], [3, [4, 5]]]))
    assert all(not isinstance(item, list) for item in result)
    assert len(result) == 5

# condition: isinstance(x, list): True for mixed nesting
def test_flatten_mixed_nesting():
    # isinstance(x, list): True for inner list, False for non-list items
    result = consume(flatten([1, [2, 3], 4, [5, [6]]]))
    assert all(not isinstance(item, list) for item in result)
    assert len(result) == 6

# condition: isinstance(x, list): False → empty outer list (no iterations)
def test_flatten_empty_list():
    # arr is empty, loop body never executes
    result = consume(flatten([]))
    assert result == []
    assert len(result) == 0

# condition: isinstance(x, list): True → empty inner list
def test_flatten_empty_inner_list():
    # x is a list (isinstance True), but inner list is empty so yields nothing
    result = consume(flatten([[], []]))
    assert result == []
    assert all(not isinstance(item, list) for item in result)

# condition: isinstance(x, list): True and False in same input
def test_flatten_single_element_nested():
    # isinstance(x, list): True for [42], False for 42
    result = consume(flatten([[42]]))
    assert all(not isinstance(item, list) for item in result)
    assert len(result) == 1

# condition: isinstance(x, list): False for string (non-list element)
def test_flatten_non_list_element_string():
    # isinstance(x, list): False for string elements
    result = consume(flatten(["hello", "world"]))
    assert all(not isinstance(item, list) for item in result)
    assert len(result) == 2

# condition: isinstance(x, list): True (outer list contains list) and False (integers)
def test_flatten_multiple_levels_integers():
    # ensures both True and False branches are hit across elements
    result = consume(flatten([1, [2, [3, [4]]]]))
    assert all(not isinstance(item, list) for item in result)
    assert len(result) == 4

# condition: isinstance(x, list): True for each of multiple nested lists
def test_flatten_multiple_nested_lists_no_atoms():
    # all elements are lists: isinstance(x, list) always True until leaf
    result = consume(flatten([[1], [2], [3]]))
    assert all(not isinstance(item, list) for item in result)
    assert len(result) == 3