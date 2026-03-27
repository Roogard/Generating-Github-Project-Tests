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


def test_flatten_empty_nested_list():
    result = list(flatten([[]]))
    assert result == []


def test_flatten_empty_deeply_nested():
    result = list(flatten([[[], []]]))
    assert result == []


def test_flatten_multiple_levels_of_nesting():
    result = list(flatten([1, [2, [3, [4]]]]))
    assert result == [1, 2, 3, 4]


def test_flatten_string_element_single():
    result = list(flatten(["a"]))
    assert result == ["a"]


def test_flatten_string_elements_mixed():
    result = list(flatten(["a", ["b", "c"]]))
    assert result == ["a", "b", "c"]


def test_flatten_large_flat_list():
    large = list(range(1000))
    result = list(flatten(large))
    assert result == large


def test_flatten_large_nested_list():
    large_nested = [[i] for i in range(1000)]
    result = list(flatten(large_nested))
    assert result == list(range(1000))


def test_flatten_none_element():
    result = list(flatten([None]))
    assert result == [None]


def test_flatten_none_mixed_with_list():
    result = list(flatten([None, [1, 2]]))
    assert result == [None, 1, 2]


def test_flatten_boolean_elements():
    result = list(flatten([True, False]))
    assert result == [True, False]


def test_flatten_nested_boolean_elements():
    result = list(flatten([[True], [False]]))
    assert result == [True, False]


def test_flatten_zero_value_element():
    result = list(flatten([0]))
    assert result == [0]


def test_flatten_negative_values():
    result = list(flatten([-1, [-2, -3]]))
    assert result == [-1, -2, -3]


def test_flatten_two_level_empty_and_nonempty():
    result = list(flatten([[], [1]]))
    assert result == [1]