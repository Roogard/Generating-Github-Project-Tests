import pytest
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

def test_flatten_two_elements_no_nesting():
    result = list(flatten([1, 2]))
    assert result == [1, 2]
    assert len(result) == 2
    assert all(not isinstance(x, list) for x in result)

def test_flatten_two_elements_with_nesting():
    result = list(flatten([[1], [2]]))
    assert result == [1, 2]
    assert len(result) == 2
    assert all(not isinstance(x, list) for x in result)

def test_flatten_deeply_nested_single_element():
    result = list(flatten([[[[1]]]]))
    assert result == [1]
    assert len(result) == 1
    assert all(not isinstance(x, list) for x in result)

def test_flatten_mixed_nested_and_flat():
    result = list(flatten([1, [2, 3], 4]))
    assert result == [1, 2, 3, 4]
    assert len(result) == 4
    assert all(not isinstance(x, list) for x in result)

def test_flatten_deeply_nested_mixed():
    result = list(flatten([1, [2, [3, [4]]]]))
    assert result == [1, 2, 3, 4]
    assert len(result) == 4
    assert all(not isinstance(x, list) for x in result)

def test_flatten_all_elements_nested_one_level():
    result = list(flatten([[1, 2, 3]]))
    assert result == [1, 2, 3]
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)

def test_flatten_empty_nested_list():
    result = list(flatten([[]]))
    assert result == []
    assert len(result) == 0

def test_flatten_multiple_empty_nested_lists():
    result = list(flatten([[], [], []]))
    assert result == []
    assert len(result) == 0

def test_flatten_empty_nested_inside_nonempty():
    result = list(flatten([1, [], 2]))
    assert result == [1, 2]
    assert len(result) == 2
    assert all(not isinstance(x, list) for x in result)

def test_flatten_string_elements_not_recursed():
    result = list(flatten(["a", "b"]))
    assert result == ["a", "b"]
    assert len(result) == 2
    assert all(not isinstance(x, list) for x in result)

def test_flatten_string_inside_nested_list():
    result = list(flatten([["a", "b"]]))
    assert result == ["a", "b"]
    assert len(result) == 2
    assert all(not isinstance(x, list) for x in result)

def test_flatten_large_flat_list():
    input_list = list(range(1000))
    result = list(flatten(input_list))
    assert result == list(range(1000))
    assert len(result) == 1000
    assert all(not isinstance(x, list) for x in result)

def test_flatten_large_nested_list():
    input_list = [[i] for i in range(1000)]
    result = list(flatten(input_list))
    assert result == list(range(1000))
    assert len(result) == 1000
    assert all(not isinstance(x, list) for x in result)

def test_flatten_preserves_duplicates():
    result = list(flatten([1, [1, 1], [1]]))
    assert result == [1, 1, 1, 1]
    assert len(result) == 4
    assert all(not isinstance(x, list) for x in result)

def test_flatten_none_element():
    result = list(flatten([None]))
    assert result == [None]
    assert len(result) == 1
    assert all(not isinstance(x, list) for x in result)

def test_flatten_none_inside_nested():
    result = list(flatten([[None, None]]))
    assert result == [None, None]
    assert len(result) == 2
    assert all(not isinstance(x, list) for x in result)

def test_flatten_boolean_elements():
    result = list(flatten([True, False]))
    assert result == [True, False]
    assert len(result) == 2
    assert all(not isinstance(x, list) for x in result)

def test_flatten_mixed_types():
    result = list(flatten([1, "a", None, [2, "b", None]]))
    assert result == [1, "a", None, 2, "b", None]
    assert len(result) == 6
    assert all(not isinstance(x, list) for x in result)