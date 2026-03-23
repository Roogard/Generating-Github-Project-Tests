import pytest
from boltons.iterutils import split

def test_split_empty_iterable():
    assert split([]) == []

def test_split_single_element_no_sep():
    assert split(['a']) == [['a']]

def test_split_all_separators():
    assert split([None, None, None], sep=None) == []

def test_split_maxsplit_zero():
    assert split(['a', None, 'b', None, 'c'], sep=None, maxsplit=0) == [['a', 'b', 'c']]

def test_split_maxsplit_one():
    result = split(['a', None, 'b', None, 'c'], sep=None, maxsplit=1)
    assert result == [['a'], ['b', 'c']]

def test_split_maxsplit_one_less_than_full():
    result = split(['a', None, 'b', None, 'c'], sep=None, maxsplit=2)
    assert result == [['a'], ['b'], ['c']]

def test_split_maxsplit_equal_to_separators():
    result = split(['a', None, 'b', None, 'c'], sep=None, maxsplit=3)
    assert result == [['a'], ['b'], ['c']]

def test_split_maxsplit_greater_than_separators():
    result = split(['a', None, 'b', None, 'c'], sep=None, maxsplit=5)
    assert result == [['a'], ['b'], ['c']]

def test_split_string_separator():
    assert split(['a', '|', 'b', '|', 'c'], sep='|') == [['a'], ['b'], ['c']]

def test_split_no_separator_present():
    assert split(['a', 'b', 'c'], sep=None) == [['a', 'b', 'c']]

def test_split_consecutive_separators():
    assert split(['a', None, None, 'b'], sep=None) == [['a'], ['b']]

def test_split_separator_at_start():
    assert split([None, 'a', 'b'], sep=None) == [['a', 'b']]

def test_split_separator_at_end():
    assert split(['a', 'b', None], sep=None) == [['a', 'b']]

def test_split_separator_at_start_and_end():
    assert split([None, 'a', 'b', None], sep=None) == [['a', 'b']]

def test_split_maxsplit_with_consecutive_separators():
    result = split(['a', None, None, 'b', None, 'c'], sep=None, maxsplit=1)
    assert result == [['a'], ['b', 'c']]

def test_split_iterable_with_falsey_non_separator():
    assert split([0, 1, 2, 0], sep=None) == [[0, 1, 2, 0]]

def test_split_with_custom_separator_falsey():
    assert split([0, 1, 2, 0], sep=0) == [[1, 2]]