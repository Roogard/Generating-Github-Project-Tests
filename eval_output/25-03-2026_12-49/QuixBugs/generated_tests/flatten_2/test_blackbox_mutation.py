from python_programs.flatten import flatten

# catches: yield flatten(x) instead of yield x for non-list items (wrong variable)
def test_flatten_simple_list():
    assert list(flatten([1, 2, 3])) == [1, 2, 3]

# catches: missing recursion or negated isinstance condition (lists not flattened)
def test_flatten_one_level():
    assert list(flatten([1, [2, 3], 4])) == [1, 2, 3, 4]

# catches: shallow recursion only (off-by-one in recursion depth)
def test_flatten_deep_nesting():
    assert list(flatten([[1, [2, [3]], 4]])) == [1, 2, 3, 4]

# catches: incorrect handling of empty lists (boundary error)
def test_flatten_with_empty_lists():
    assert list(flatten([1, [], [2, [], [3]], []])) == [1, 2, 3]

# catches: wrong type check flattening non-list Iterable like tuple
def test_flatten_non_list_iterable_kept_intact():
    assert list(flatten([1, (2, 3), [4, (5, 6)], [7]])) == [1, (2, 3), 4, (5, 6), 7]

# catches: treating str as list leading to character iteration (wrong isinstance)
def test_flatten_strings_not_expanded():
    assert list(flatten(['a', ['b', 'cd'], 'ef'])) == ['a', 'b', 'cd', 'ef']