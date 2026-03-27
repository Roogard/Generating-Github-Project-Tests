import pytest
from python_programs.flatten import flatten


def test_flatten_empty_list():
    result = list(flatten([]))
    assert result == []


def test_flatten_single_non_list_element():
    result = list(flatten([1]))
    assert result == [1]


def test_flatten_single_nested_list():
    result = list(flatten([[1]]))
    assert result == [1]


def test_flatten_two_elements_flat():
    result = list(flatten([1, 2]))
    assert result == [1, 2]


def test_flatten_two_elements_nested():
    result = list(flatten([[1, 2]]))
    assert result == [1, 2]


def test_flatten_deeply_nested_single_element():
    result = list(flatten([[[[1]]]]))
    assert result == [1]


def test_flatten_mixed_flat_and_nested():
    result = list(flatten([1, [2, 3], 4]))
    assert result == [1, 2, 3, 4]


def test_flatten_all_nested():
    result = list(flatten([[1], [2], [3]]))
    assert result == [1, 2, 3]


def test_flatten_nested_empty_list():
    result = list(flatten([[]]))
    assert result == []


def test_flatten_nested_multiple_empty_lists():
    result = list(flatten([[], [], []]))
    assert result == []


def test_flatten_deeply_nested_multiple_elements():
    result = list(flatten([[1, [2, [3, [4]]]]]))
    assert result == [1, 2, 3, 4]


def test_flatten_single_string_element():
    result = list(flatten(["a"]))
    assert result == ["a"]


def test_flatten_string_and_int_mixed():
    result = list(flatten([1, "a", [2, "b"]]))
    assert result == [1, "a", 2, "b"]


def test_flatten_large_flat_list():
    large = list(range(1000))
    result = list(flatten(large))
    assert result == large


def test_flatten_large_nested_list():
    large = [[i] for i in range(1000)]
    result = list(flatten(large))
    assert result == list(range(1000))


def test_flatten_none_as_element():
    result = list(flatten([None]))
    assert result == [None]


def test_flatten_none_mixed_with_list():
    result = list(flatten([None, [1, None], 2]))
    assert result == [None, 1, None, 2]


def test_flatten_single_level_multiple_elements():
    result = list(flatten([1, 2, 3, 4, 5]))
    assert result == [1, 2, 3, 4, 5]


def test_flatten_two_level_deep():
    result = list(flatten([[1, 2], [3, 4]]))
    assert result == [1, 2, 3, 4]


def test_flatten_three_level_deep():
    result = list(flatten([[[1, 2]], [[3, 4]]]))
    assert result == [1, 2, 3, 4]