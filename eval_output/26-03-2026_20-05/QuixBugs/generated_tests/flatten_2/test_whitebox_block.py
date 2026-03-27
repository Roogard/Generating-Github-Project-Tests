Looking at the basic blocks in `flatten`:

1. **Block 1**: Function entry, for-loop over `arr`
2. **Block 2**: `if isinstance(x, list)` is True → inner for-loop over `flatten(x)`, yield y
3. **Block 3**: `else` branch → `yield flatten(x)` (yields a generator object for non-list items)
4. **Block 4**: Loop exhausted / empty arr (no iterations)

Note: The function has a bug — for non-list items it yields `flatten(x)` (a generator) instead of `x`. Tests should reflect what the function SHOULD do (yield scalar values from a flattened list), but we need inputs that hit each block. I'll test expected correct behavior.

from python_programs.flatten import flatten

# covers: block 4 (empty arr, loop never executes)
def test_flatten_empty():
    result = list(flatten([]))
    assert result == []

# covers: block 1, block 3 (non-list elements only, else branch)
def test_flatten_flat_list():
    result = list(flatten([1, 2, 3]))
    assert result == [1, 2, 3]

# covers: block 1, block 2 (nested list, isinstance True, recursive yield)
def test_flatten_nested_list():
    result = list(flatten([[1, 2], [3, 4]]))
    assert result == [1, 2, 3, 4]

# covers: block 1, block 2, block 3 (mixed nested and scalar)
def test_flatten_mixed():
    result = list(flatten([1, [2, 3], 4]))
    assert result == [1, 2, 3, 4]

# covers: block 1, block 2 (deeply nested list)
def test_flatten_deeply_nested():
    result = list(flatten([[1, [2, [3]]]]))
    assert result == [1, 2, 3]

# covers: block 1, block 3 (single non-list element)
def test_flatten_single_element():
    result = list(flatten([42]))
    assert result == [42]

# covers: block 1, block 2 (list containing empty list)
def test_flatten_nested_empty():
    result = list(flatten([[], []]))
    assert result == []