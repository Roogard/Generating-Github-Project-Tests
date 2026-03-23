import pytest
from boltons.iterutils import split

# path: sep is None, maxsplit is None, src empty
def test_split_empty_src():
    assert split([]) == []

# path: sep is None, maxsplit is None, src non-empty, no None encountered before end
def test_split_no_sep_no_none():
    assert split([1, 2, 3]) == [[1, 2, 3]]

# path: sep is None, maxsplit is None, src non-empty, one None at start
def test_split_none_at_start():
    assert split([None, 1, 2]) == [[1, 2]]

# path: sep is None, maxsplit is None, src non-empty, one None in middle
def test_split_one_none_in_middle():
    assert split([1, None, 2]) == [[1], [2]]

# path: sep is None, maxsplit is None, src non-empty, consecutive Nones
def test_split_consecutive_nones():
    assert split([1, None, None, 2]) == [[1], [2]]

# path: sep is None, maxsplit is None, src non-empty, None at end
def test_split_none_at_end():
    assert split([1, 2, None]) == [[1, 2]]

# path: sep is not None, maxsplit is None, src empty
def test_split_custom_sep_empty_src():
    assert split([], sep=0) == []

# path: sep is not None, maxsplit is None, src non-empty, no sep encountered before end
def test_split_custom_sep_no_sep():
    assert split([1, 2, 3], sep=0) == [[1, 2, 3]]

# path: sep is not None, maxsplit is None, src non-empty, one sep at start
def test_split_custom_sep_at_start():
    assert split([0, 1, 2], sep=0) == [[1, 2]]

# path: sep is not None, maxsplit is None, src non-empty, one sep in middle
def test_split_custom_sep_in_middle():
    assert split([1, 0, 2], sep=0) == [[1], [2]]

# path: sep is not None, maxsplit is None, src non-empty, consecutive seps
def test_split_custom_sep_consecutive():
    assert split([1, 0, 0, 2], sep=0) == [[1], [2]]

# path: sep is not None, maxsplit is None, src non-empty, sep at end
def test_split_custom_sep_at_end():
    assert split([1, 2, 0], sep=0) == [[1, 2]]

# path: sep is None, maxsplit is 0, src non-empty
def test_split_maxsplit_zero():
    assert split([1, None, 2, None, 3], maxsplit=0) == [[1, None, 2, None, 3]]

# path: sep is None, maxsplit is positive, src non-empty, fewer splits than maxsplit
def test_split_maxsplit_positive_fewer_splits():
    assert split([1, None, 2, None, 3], maxsplit=3) == [[1], [2], [3]]

# path: sep is None, maxsplit is positive, src non-empty, exactly maxsplit splits
def test_split_maxsplit_positive_exact():
    assert split([1, None, 2, None, 3], maxsplit=2) == [[1], [2], [3]]

# path: sep is None, maxsplit is positive, src non-empty, more splits possible than maxsplit
def test_split_maxsplit_positive_limited():
    assert split([1, None, 2, None, 3, None, 4], maxsplit=2) == [[1], [2], [3, None, 4]]

# path: sep is not None, maxsplit is positive, src non-empty, more splits possible than maxsplit
def test_split_custom_sep_maxsplit_positive_limited():
    assert split([1, 0, 2, 0, 3, 0, 4], sep=0, maxsplit=2) == [[1], [2], [3, 0, 4]]

# path: sep is not None, maxsplit is positive, src non-empty, exactly maxsplit splits
def test_split_custom_sep_maxsplit_positive_exact():
    assert split([1, 0, 2, 0, 3], sep=0, maxsplit=2) == [[1], [2], [3]]

# path: sep is not None, maxsplit is positive, src non-empty, fewer splits than maxsplit
def test_split_custom_sep_maxsplit_positive_fewer():
    assert split([1, 0, 2], sep=0, maxsplit=3) == [[1], [2]]