from python_programs.flatten import flatten

def test_flatten_empty_list():
    result = list(flatten([]))
    assert result == []
    assert len(result) == 0

def test_flatten_single_non_list_element():
    result = list(flatten([42]))
    assert result == [42]
    assert len(result) == 1
    assert all(not isinstance(x, list) for x in result)

def test_flatten_single_nested_list():
    result = list(flatten([[1]]))
    assert result == [1]
    assert len(result) == 1
    assert all(not isinstance(x, list) for x in result)

def test_flatten_two_non_list_elements():
    result = list(flatten([1, 2]))
    assert result == [1, 2]
    assert len(result) == 2
    assert all(not isinstance(x, list) for x in result)

def test_flatten_flat_list_multiple_elements():
    inp = [1, 2, 3, 4, 5]
    result = list(flatten(inp))
    assert result == [1, 2, 3, 4, 5]
    assert len(result) == len(inp)
    assert all(not isinstance(x, list) for x in result)

def test_flatten_one_level_of_nesting():
    inp = [[1, 2], [3, 4]]
    result = list(flatten(inp))
    assert sorted(result) == sorted([1, 2, 3, 4])
    assert len(result) == 4
    assert all(not isinstance(x, list) for x in result)

def test_flatten_deeply_nested_single_element():
    inp = [[[[[42]]]]]
    result = list(flatten(inp))
    assert result == [42]
    assert len(result) == 1
    assert all(not isinstance(x, list) for x in result)

def test_flatten_mixed_flat_and_nested():
    inp = [1, [2, 3], 4]
    result = list(flatten(inp))
    assert sorted(result) == sorted([1, 2, 3, 4])
    assert len(result) == 4
    assert all(not isinstance(x, list) for x in result)

def test_flatten_nested_empty_list():
    inp = [[]]
    result = list(flatten(inp))
    assert result == []
    assert all(not isinstance(x, list) for x in result)

def test_flatten_nested_empty_lists_among_elements():
    inp = [[], [1], [], [2, 3]]
    result = list(flatten(inp))
    assert sorted(result) == sorted([1, 2, 3])
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)

def test_flatten_two_levels_deep():
    inp = [[1, [2, 3]], [4, [5, 6]]]
    result = list(flatten(inp))
    assert sorted(result) == sorted([1, 2, 3, 4, 5, 6])
    assert len(result) == 6
    assert all(not isinstance(x, list) for x in result)

def test_flatten_string_elements_are_not_lists():
    inp = ["a", "b", "c"]
    result = list(flatten(inp))
    assert result == ["a", "b", "c"]
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)

def test_flatten_string_mixed_with_list():
    inp = ["a", [1, 2], "b"]
    result = list(flatten(inp))
    assert len(result) == 4
    assert all(not isinstance(x, list) for x in result)

def test_flatten_none_element():
    inp = [None]
    result = list(flatten(inp))
    assert result == [None]
    assert len(result) == 1
    assert all(not isinstance(x, list) for x in result)

def test_flatten_none_mixed_with_nested():
    inp = [None, [1, None], 2]
    result = list(flatten(inp))
    assert len(result) == 4
    assert all(not isinstance(x, list) for x in result)
    assert sorted([x for x in result if x is not None]) == [1, 2]

def test_flatten_large_flat_list():
    inp = list(range(1000))
    result = list(flatten(inp))
    assert result == list(range(1000))
    assert len(result) == 1000
    assert all(not isinstance(x, list) for x in result)

def test_flatten_large_nested_list():
    inp = [[i] for i in range(100)]
    result = list(flatten(inp))
    assert sorted(result) == list(range(100))
    assert len(result) == 100
    assert all(not isinstance(x, list) for x in result)

def test_flatten_boolean_elements():
    inp = [True, False, [True]]
    result = list(flatten(inp))
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)

def test_flatten_zero_integer():
    inp = [0]
    result = list(flatten(inp))
    assert result == [0]
    assert len(result) == 1
    assert all(not isinstance(x, list) for x in result)

def test_flatten_negative_numbers():
    inp = [-1, [-2, -3]]
    result = list(flatten(inp))
    assert sorted(result) == sorted([-1, -2, -3])
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)