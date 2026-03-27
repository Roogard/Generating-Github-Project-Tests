from python_programs.flatten import flatten

# catches: "isinstance(x, list)" mutated to "not isinstance(x, list)" (negation error)
def test_flat_list_of_ints():
    result = list(flatten([1, 2, 3]))
    assert result == [1, 2, 3]

# catches: "yield y" mutated to "yield x" (wrong variable)
def test_nested_list_single_level():
    result = list(flatten([[1, 2], [3, 4]]))
    assert result == [1, 2, 3, 4]

# catches: "yield flatten(x)" should be "yield x" for non-list — wrong return value for leaf
def test_non_list_element_yields_value_not_generator():
    result = list(flatten([1]))
    assert result == [1]
    assert isinstance(result[0], int)

# catches: "yield flatten(x)" instead of "yield x" for non-list scalars (wrong function call on leaf)
def test_single_integer_element():
    result = list(flatten([42]))
    assert len(result) == 1
    assert result[0] == 42

# catches: recursive call "flatten(x)" mutated to "flatten(arr)" (wrong variable in recursion)
def test_deeply_nested_list():
    result = list(flatten([[1, [2, [3]]]]))
    assert result == [1, 2, 3]

# catches: missing recursion — only one level deep processed
def test_three_levels_deep():
    result = list(flatten([[[1]], [[2]], [[3]]]))
    assert result == [1, 2, 3]

# catches: "for y in flatten(x)" mutated to "for y in x" (missing recursion)
def test_two_level_nesting_correctness():
    result = list(flatten([[1, [2, 3]], [4]]))
    assert result == [1, 2, 3, 4]

# catches: empty list handling — should yield nothing, not raise
def test_empty_list():
    result = list(flatten([]))
    assert result == []

# catches: "for x in arr" mutated to "for x in arr[1:]" (off-by-one, skipping first element)
def test_first_element_included():
    result = list(flatten([99, 1, 2]))
    assert result[0] == 99

# catches: "for x in arr" mutated to "for x in arr[:-1]" (off-by-one, skipping last element)
def test_last_element_included():
    result = list(flatten([1, 2, 88]))
    assert result[-1] == 88

# catches: mixed list with non-list scalars and nested lists
def test_mixed_flat_and_nested():
    result = list(flatten([1, [2, 3], 4, [5, [6]]]))
    assert result == [1, 2, 3, 4, 5, 6]

# catches: "yield y" in recursive branch replaced by nothing (missing yield)
def test_nested_yields_all_elements():
    result = list(flatten([[10, 20], [30, 40]]))
    assert len(result) == 4
    assert result == [10, 20, 30, 40]

# catches: "else: yield flatten(x)" — confirms non-list leaf yields itself, not a generator object
def test_leaf_type_is_correct():
    result = list(flatten([[1, 2]]))
    for item in result:
        assert not hasattr(item, '__next__'), "leaf should not be a generator"

# catches: "isinstance(x, list)" mutated to "isinstance(x, tuple)" (wrong type check)
def test_list_is_flattened_not_tuple():
    result = list(flatten([[1, 2]]))
    assert result == [1, 2]

# catches: single element nested deeply
def test_single_deeply_nested():
    result = list(flatten([[[[7]]]]))
    assert result == [7]