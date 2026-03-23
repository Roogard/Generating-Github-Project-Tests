import pytest
from boltons.iterutils import split

# condition: sep is None: True, maxsplit is None: True
def test_split_sep_none_maxsplit_none():
    result = split(['hi', 'hello', None, None, 'sup', None, 'soap', None])
    assert result == [['hi', 'hello'], ['sup'], ['soap']]

# condition: sep is None: False, maxsplit is None: True
def test_split_sep_not_none_maxsplit_none():
    result = split(['a', 'sep', 'b', 'sep', 'c'], sep='sep')
    assert result == [['a'], ['b'], ['c']]

# condition: sep is None: True, maxsplit is None: False
def test_split_sep_none_maxsplit_not_none():
    result = split(['a', None, 'b', None, 'c'], maxsplit=1)
    assert result == [['a'], ['b', None, 'c']]

# condition: sep is None: False, maxsplit is None: False
def test_split_sep_not_none_maxsplit_not_none():
    result = split(['a', 'sep', 'b', 'sep', 'c'], sep='sep', maxsplit=1)
    assert result == [['a'], ['b', 'sep', 'c']]

# condition: src is empty list, sep is None: True, maxsplit is None: True
def test_split_empty_src():
    result = split([])
    assert result == []

# condition: src with no separator occurrences, sep is None: True, maxsplit is None: True
def test_split_no_separator():
    result = split(['a', 'b', 'c'])
    assert result == [['a', 'b', 'c']]

# condition: src with no separator occurrences, sep is None: False, maxsplit is None: True
def test_split_no_separator_custom_sep():
    result = split(['a', 'b', 'c'], sep='sep')
    assert result == [['a', 'b', 'c']]

# condition: maxsplit is None: False, maxsplit=0 (edge case)
def test_split_maxsplit_zero():
    result = split(['a', None, 'b', None, 'c'], maxsplit=0)
    assert result == [['a', None, 'b', None, 'c']]

# condition: maxsplit is None: False, maxsplit larger than occurrences
def test_split_maxsplit_larger_than_occurrences():
    result = split(['a', None, 'b'], maxsplit=5)
    assert result == [['a'], ['b']]

# condition: sep is None: False, sep is a callable (not None), maxsplit is None: True
def test_split_sep_callable():
    result = split([1, 2, 0, 3, 4, 0, 5], sep=lambda x: x == 0)
    assert result == [[1, 2], [3, 4], [5]]

# condition: sep is None: False, sep is a callable, maxsplit is None: False
def test_split_sep_callable_maxsplit():
    result = split([1, 2, 0, 3, 4, 0, 5], sep=lambda x: x == 0, maxsplit=1)
    assert result == [[1, 2], [3, 4, 0, 5]]