import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Use the correct import path as specified
from tqdm.contrib import tenumerate
from tqdm.auto import tqdm as tqdm_auto
from tqdm import tqdm as tqdm_std

# --- Statement Coverage ---

def test_statement_numpy_array_path():
    """Covers the numpy ndarray branch: isinstance check is True, returns ndenumerate wrapper."""
    arr = np.array([10, 20, 30])
    result = tenumerate(arr, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    # A correct ndenumerate over 1-D array should yield ((i,), val) pairs
    expected = list(np.ndenumerate(arr))
    assert items == expected

def test_statement_non_numpy_path():
    """Covers the non-numpy path: returns enumerate(tqdm_class(...))."""
    data = [1, 2, 3]
    result = tenumerate(data, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    expected = list(enumerate(data))
    assert items == expected

def test_statement_start_parameter_non_numpy():
    """Covers start parameter being passed through in non-numpy path."""
    data = ['a', 'b', 'c']
    result = tenumerate(data, start=5, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    expected = list(enumerate(data, start=5))
    assert items == expected

# --- Block Coverage ---

def test_block_numpy_with_total_provided():
    """
    Covers the block where total is explicitly provided (truthy total or len(iterable)).
    When total is provided, uses total directly.
    """
    arr = np.array([1, 2, 3, 4, 5])
    result = tenumerate(arr, total=5, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    expected = list(np.ndenumerate(arr))
    assert items == expected

def test_block_numpy_total_none_falls_back_to_len():
    """
    Covers the block where total=None, so total falls back to len(iterable).
    """
    arr = np.array([7, 8, 9])
    result = tenumerate(arr, total=None, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    expected = list(np.ndenumerate(arr))
    assert items == expected

def test_block_non_numpy_returns_enumerate():
    """
    Covers the final else block: non-ndarray iterable falls through to enumerate.
    Also tests that the result is an enumerate-like structure.
    """
    data = (10, 20, 30)
    result = tenumerate(data, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    # A correct enumerate should yield (index, value) pairs starting at 0
    assert items == [(0, 10), (1, 20), (2, 30)]

def test_block_string_iterable():
    """Covers non-numpy path with string iterable."""
    data = "abc"
    result = tenumerate(data, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    expected = list(enumerate("abc"))
    assert items == expected

def test_block_numpy_2d_array():
    """
    Covers numpy ndarray block for 2D array — ndenumerate yields multi-index tuples.
    Also exercises total=len(iterable) for 2D where len gives first dimension size.
    """
    arr = np.array([[1, 2], [3, 4]])
    result = tenumerate(arr, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    expected = list(np.ndenumerate(arr))
    assert items == expected

# --- Condition Coverage ---

def test_condition_isinstance_true_numpy_array():
    """
    isinstance(iterable, np.ndarray): True
    # isinstance: True
    Covers the True branch of the isinstance check.
    """
    arr = np.array([1, 2, 3])
    result = tenumerate(arr, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    expected = list(np.ndenumerate(arr))
    assert items == expected  # isinstance: True

def test_condition_isinstance_false_list():
    """
    isinstance(iterable, np.ndarray): False
    # isinstance: False
    Covers the False branch: falls through to enumerate.
    """
    data = [1, 2, 3]
    result = tenumerate(data, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    expected = list(enumerate(data))
    assert items == expected  # isinstance: False

def test_condition_total_truthy():
    """
    total or len(iterable): total is truthy (non-zero, non-None)
    # total: True (uses provided total)
    """
    arr = np.array([1, 2, 3])
    result = tenumerate(arr, total=10, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    expected = list(np.ndenumerate(arr))
    assert items == expected  # total: truthy

def test_condition_total_falsy_none():
    """
    total or len(iterable): total is None (falsy), falls back to len(iterable)
    # total: False (None), len(iterable): evaluated
    """
    arr = np.array([1, 2, 3])
    result = tenumerate(arr, total=None, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    expected = list(np.ndenumerate(arr))
    assert items == expected  # total: None (falsy), uses len

def test_condition_total_zero_falsy():
    """
    total or len(iterable): total=0 is falsy, falls back to len(iterable)
    # total: False (0), len(iterable): evaluated
    """
    arr = np.array([1, 2, 3])
    result = tenumerate(arr, total=0, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    expected = list(np.ndenumerate(arr))
    assert items == expected  # total: 0 (falsy), uses len

# --- Path Coverage ---

def test_path_numpy_import_success_ndarray_total_none():
    """
    path: try-succeeds → isinstance True → total=None → return tqdm_class(ndenumerate, total=len)
    # path: numpy imported → ndarray → total=None → ndenumerate path
    """
    arr = np.array([5, 6, 7])
    result = tenumerate(arr, total=None, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    expected = list(np.ndenumerate(arr))
    assert len(items) == len(expected)
    assert items == expected  # path: ndarray, total=None

def test_path_numpy_import_success_ndarray_total_provided():
    """
    path: try-succeeds → isinstance True → total=5 → return tqdm_class(ndenumerate, total=5)
    # path: numpy imported → ndarray → total truthy → ndenumerate path
    """
    arr = np.array([5, 6, 7])
    result = tenumerate(arr, total=5, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    expected = list(np.ndenumerate(arr))
    assert items == expected  # path: ndarray, total=5

def test_path_numpy_import_success_not_ndarray():
    """
    path: try-succeeds → isinstance False → return enumerate(tqdm_class(...))
    # path: numpy imported → not ndarray → enumerate path
    """
    data = [10, 20, 30]
    result = tenumerate(data, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    expected = list(enumerate(data))
    assert items == expected  # path: not ndarray

def test_path_numpy_import_success_not_ndarray_with_start():
    """
    path: try-succeeds → isinstance False → return enumerate(tqdm_class(iterable, start=3, ...))
    # path: numpy imported → not ndarray → enumerate with start=3
    """
    data = ['x', 'y', 'z']
    result = tenumerate(data, start=3, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    expected = list(enumerate(data, start=3))
    assert items == expected  # path: not ndarray, start=3

def test_path_numpy_unavailable_non_ndarray():
    """
    path: try-ImportError → (numpy unavailable) → return enumerate(tqdm_class(...))
    Simulates the ImportError except block by patching builtins.__import__.
    # path: ImportError → fallthrough → enumerate path
    """
    import builtins
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == 'numpy':
            raise ImportError("mocked numpy missing")
        return real_import(name, *args, **kwargs)

    data = [1, 2, 3]
    with patch('builtins.__import__', side_effect=mock_import):
        result = tenumerate(data, tqdm_class=tqdm_std, disable=True)
        items = list(result)

    expected = list(enumerate(data))
    assert items == expected  # path: ImportError → enumerate path

def test_path_empty_list():
    """
    path: try-succeeds → isinstance False → empty iterable → enumerate path, zero iterations
    # path: not ndarray → empty iterable → enumerate path
    """
    data = []
    result = tenumerate(data, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    assert items == []  # empty enumerate is unambiguously []

def test_path_empty_numpy_array():
    """
    path: try-succeeds → isinstance True → empty ndarray → ndenumerate path, zero iterations
    # path: ndarray → empty → ndenumerate path
    """
    arr = np.array([])
    result = tenumerate(arr, total=None, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    expected = list(np.ndenumerate(arr))
    assert items == expected  # path: ndarray, empty

def test_path_single_element_numpy():
    """
    path: numpy imported → ndarray (single element) → ndenumerate, one iteration
    # path: ndarray → 1 element → ndenumerate path
    """
    arr = np.array([42])
    result = tenumerate(arr, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    expected = list(np.ndenumerate(arr))
    assert items == expected
    assert len(items) == 1

def test_path_multiple_elements_non_numpy():
    """
    path: numpy imported → not ndarray → enumerate, multiple iterations
    # path: not ndarray → multiple items → enumerate path
    """
    data = range(10)
    result = tenumerate(data, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    expected = list(enumerate(range(10)))
    assert len(items) == 10
    assert items == expected

def test_default_tqdm_class_non_numpy():
    """
    Verify default tqdm_class (tqdm_auto) is used when not overridden — non-numpy path.
    """
    data = [1, 2, 3]
    result = tenumerate(data, disable=True)
    items = list(result)
    expected = list(enumerate(data))
    assert items == expected

def test_default_tqdm_class_numpy():
    """
    Verify default tqdm_class (tqdm_auto) is used when not overridden — numpy path.
    """
    arr = np.array([1, 2, 3])
    result = tenumerate(arr, disable=True)
    items = list(result)
    expected = list(np.ndenumerate(arr))
    assert items == expected

def test_property_length_preserved_non_numpy():
    """Property: enumerate of a list preserves element count."""
    data = list(range(7))
    result = tenumerate(data, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    assert len(items) == len(data)

def test_property_values_preserved_non_numpy():
    """Property: values in enumerate result must match original iterable values."""
    data = [100, 200, 300]
    result = tenumerate(data, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    values = [v for _, v in items]
    assert values == data

def test_property_indices_contiguous_non_numpy():
    """Property: indices from enumerate starting at 0 are 0,1,2,..."""
    data = ['a', 'b', 'c', 'd']
    result = tenumerate(data, start=0, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    indices = [i for i, _ in items]
    assert indices == list(range(len(data)))

def test_property_numpy_values_preserved():
    """Property: all values from ndenumerate of array equal original array values."""
    arr = np.array([3, 1, 4, 1, 5, 9])
    result = tenumerate(arr, tqdm_class=tqdm_std, disable=True)
    items = list(result)
    result_values = [v for _, v in items]
    expected_values = arr.flatten().tolist()
    assert result_values == expected_values