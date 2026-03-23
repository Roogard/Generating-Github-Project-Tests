import pytest
from boltons.iterutils import split

# Valid equivalence class: src is empty iterable, sep is None
def test_split_empty_src_sep_none():
    assert split([]) == []

# Valid equivalence class: src contains no sep (None) values
def test_split_no_separators_sep_none():
    assert split([1, 2, 3]) == [[1, 2, 3]]

# Valid equivalence class: src contains multiple sep (None) values
def test_split_multiple_separators_sep_none():
    assert split(['a', None, 'b', None, 'c']) == [['a'], ['b'], ['c']]

# Valid equivalence class: src starts with sep (None)
def test_split_starts_with_separator_sep_none():
    assert split([None, 'a', 'b']) == [['a', 'b']]

# Valid equivalence class: src ends with sep (None)
def test_split_ends_with_separator_sep_none():
    assert split(['a', 'b', None]) == [['a', 'b']]

# Valid equivalence class: consecutive separators (None) in src
def test_split_consecutive_separators_sep_none():
    assert split(['a', None, None, 'b']) == [['a'], ['b']]

# Valid equivalence class: custom separator (not None)
def test_split_custom_separator():
    assert split([1, 0, 2, 0, 3], sep=0) == [[1], [2], [3]]

# Valid equivalence class: maxsplit specified, fewer splits than separators
def test_split_with_maxsplit_less_than_separators():
    assert split(['a', None, 'b', None, 'c'], maxsplit=1) == [['a'], ['b', None, 'c']]

# Valid equivalence class: maxsplit specified, zero splits
def test_split_with_maxsplit_zero():
    assert split(['a', None, 'b'], maxsplit=0) == [['a', None, 'b']]

# Valid equivalence class: maxsplit specified, exactly equals number of splits
def test_split_with_maxsplit_equals_separators():
    assert split(['a', None, 'b', None, 'c'], maxsplit=2) == [['a'], ['b'], ['c']]

# Valid equivalence class: maxsplit larger than number of separators
def test_split_with_maxsplit_greater_than_separators():
    assert split(['a', None, 'b'], maxsplit=5) == [['a'], ['b']]

# Valid equivalence class: src is tuple (other iterable type)
def test_split_src_is_tuple():
    assert split(('a', None, 'b')) == [['a'], ['b']]

# Invalid equivalence class: maxsplit is negative
def test_split_maxsplit_negative():
    with pytest.raises(ValueError):
        split([1, 2, 3], maxsplit=-1)

# Invalid equivalence class: src is not iterable
def test_split_src_not_iterable():
    with pytest.raises(TypeError):
        split(123)