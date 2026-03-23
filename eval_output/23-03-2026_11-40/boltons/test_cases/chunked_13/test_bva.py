import pytest
from boltons.iterutils import flatten

def test_flatten_empty_iterable():
    assert flatten([]) == []

def test_flatten_single_level_list():
    assert flatten([1, 2, 3]) == [1, 2, 3]

def test_flatten_nested_empty_lists():
    assert flatten([[], []]) == []

def test_flatten_deeply_nested_single_element():
    assert flatten([[[[1]]]]) == [1]

def test_flatten_mixed_nesting():
    assert flatten([[1, 2], [[3], [4, 5]]]) == [1, 2, 3, 4, 5]

def test_flatten_with_strings_as_non_iterable():
    assert flatten(['ab', 'cd']) == ['ab', 'cd']

def test_flatten_with_mixed_types():
    assert flatten([1, [2, 3], 4]) == [1, 2, 3, 4]

def test_flatten_single_element():
    assert flatten([42]) == [42]

def test_flatten_large_nested_structure():
    nested = [[i for i in range(10)] for _ in range(10)]
    expected = list(range(10)) * 10
    assert flatten(nested) == expected