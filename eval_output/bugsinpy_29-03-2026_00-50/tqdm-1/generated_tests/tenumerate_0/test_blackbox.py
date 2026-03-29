import pytest
import numpy as np
from tqdm.contrib import tenumerate
from tqdm import tqdm
from tqdm.auto import tqdm as tqdm_auto

# Helper: consume the iterator and return list of (index, value) pairs
def consume(it):
    return list(it)

# --- BVA ---

def test_bva_empty_list():
    # Boundary: empty collection — a correct enumerate should yield nothing
    result = consume(tenumerate([], disable=True))
    assert result == []

def test_bva_single_element_list():
    # Boundary: single-element list
    result = consume(tenumerate([42], disable=True))
    assert result == [(0, 42)]

def test_bva_two_element_list():
    # Boundary: min+1
    result = consume(tenumerate([10, 20], disable=True))
    assert result == [(0, 10), (1, 20)]

def test_bva_start_zero():
    # Boundary: start at exactly 0 (default)
    result = consume(tenumerate(['a', 'b', 'c'], start=0, disable=True))
    assert result == [(0, 'a'), (1, 'b'), (2, 'c')]

def test_bva_start_one():
    # Boundary: start=1
    result = consume(tenumerate(['a', 'b', 'c'], start=1, disable=True))
    assert result == [(1, 'a'), (2, 'b'), (3, 'c')]

def test_bva_start_negative():
    # Boundary: negative start value
    result = consume(tenumerate(['x', 'y'], start=-1, disable=True))
    assert result == [(-1, 'x'), (0, 'y')]

def test_bva_start_large():
    # Boundary: large start value
    result = consume(tenumerate(['a'], start=10**6, disable=True))
    assert result == [(10**6, 'a')]

def test_bva_numpy_empty_array():
    # Boundary: empty numpy array — should use ndenumerate path
    arr = np.array([])
    result = consume(tenumerate(arr, disable=True))
    assert result == []

def test_bva_numpy_single_element():
    # Boundary: single-element numpy array
    arr = np.array([7])
    result = consume(tenumerate(arr, disable=True))
    assert len(result) == 1
    idx, val = result[0]
    assert idx == (0,)
    assert val == 7

def test_bva_numpy_two_elements():
    # Boundary: two-element numpy array
    arr = np.array([3, 4])
    result = consume(tenumerate(arr, disable=True))
    assert len(result) == 2
    assert result[0] == ((0,), 3)
    assert result[1] == ((1,), 4)

def test_bva_large_list():
    # Boundary: large collection
    data = list(range(1000))
    result = consume(tenumerate(data, disable=True))
    assert len(result) == 1000
    assert all(idx == val for idx, val in result)

# --- ECP ---

def test_ecp_valid_plain_list():
    # Valid class: plain Python list (non-numpy) uses enumerate path
    data = [10, 20, 30]
    result = consume(tenumerate(data, disable=True))
    expected = list(enumerate(data))
    assert result == expected

def test_ecp_valid_tuple():
    # Valid class: tuple iterable
    data = (1, 2, 3)
    result = consume(tenumerate(data, disable=True))
    expected = list(enumerate(data))
    assert result == expected

def test_ecp_valid_string():
    # Valid class: string iterable
    data = "abc"
    result = consume(tenumerate(data, disable=True))
    expected = list(enumerate(data))
    assert result == expected

def test_ecp_valid_generator():
    # Valid class: generator (no len) — should still enumerate correctly
    data = (x for x in [1, 2, 3])
    result = consume(tenumerate(data, disable=True))
    assert result == [(0, 1), (1, 2), (2, 3)]

def test_ecp_valid_numpy_1d():
    # Valid class: 1D numpy array — uses ndenumerate path, indices are tuples
    arr = np.array([5, 6, 7])
    result = consume(tenumerate(arr, disable=True))
    expected = list(np.ndenumerate(arr))
    assert result == expected

def test_ecp_valid_numpy_2d():
    # Valid class: 2D numpy array — uses ndenumerate path
    arr = np.array([[1, 2], [3, 4]])
    result = consume(tenumerate(arr, disable=True))
    expected = list(np.ndenumerate(arr))
    assert result == expected

def test_ecp_valid_numpy_3d():
    # Valid class: 3D numpy array
    arr = np.arange(8).reshape(2, 2, 2)
    result = consume(tenumerate(arr, disable=True))
    expected = list(np.ndenumerate(arr))
    assert result == expected

def test_ecp_valid_custom_start():
    # Valid class: non-zero start with list
    data = ['a', 'b', 'c']
    result = consume(tenumerate(data, start=5, disable=True))
    expected = list(enumerate(data, start=5))
    assert result == expected

def test_ecp_valid_total_hint():
    # Valid class: total parameter provided (mainly for tqdm display, not output)
    data = [1, 2, 3]
    result = consume(tenumerate(data, total=3, disable=True))
    expected = list(enumerate(data))
    assert result == expected

def test_ecp_valid_numpy_with_total():
    # Valid class: numpy array with explicit total
    arr = np.array([1, 2, 3])
    result = consume(tenumerate(arr, total=3, disable=True))
    expected = list(np.ndenumerate(arr))
    assert result == expected

def test_ecp_valid_custom_tqdm_class():
    # Valid class: custom tqdm_class (tqdm instead of tqdm_auto)
    data = [1, 2, 3]
    result = consume(tenumerate(data, tqdm_class=tqdm, disable=True))
    expected = list(enumerate(data))
    assert result == expected

def test_ecp_numpy_indices_are_tuples():
    # ECP: numpy path yields tuple indices, list path yields int indices
    arr = np.array([10, 20, 30])
    result = consume(tenumerate(arr, disable=True))
    for idx, _ in result:
        assert isinstance(idx, tuple), "A correct tenumerate on ndarray SHOULD yield tuple indices (ndenumerate behavior)"

def test_ecp_list_indices_are_integers():
    # ECP: list path yields integer indices
    data = [10, 20, 30]
    result = consume(tenumerate(data, disable=True))
    for idx, _ in result:
        assert isinstance(idx, int), "A correct tenumerate on list SHOULD yield integer indices (enumerate behavior)"

# --- Mutation Detection ---

def test_mutation_start_off_by_one():
    # Detects: `start+1` instead of `start`, or wrong initial index
    data = ['a', 'b', 'c']
    result = consume(tenumerate(data, start=0, disable=True))
    # A correct implementation must start at 0, not 1
    assert result[0][0] == 0, "First index must equal start=0"

def test_mutation_start_nonzero_off_by_one():
    # Detects: `start-1` or `start+1` in index computation
    data = ['a', 'b', 'c']
    result = consume(tenumerate(data, start=3, disable=True))
    assert result[0][0] == 3, "First index must equal start=3"
    assert result[1][0] == 4
    assert result[2][0] == 5

def test_mutation_wrong_operator_index_increment():
    # Detects: indices not incrementing by exactly 1
    data = list(range(5))
    result = consume(tenumerate(data, disable=True))
    indices = [idx for idx, _ in result]
    for i in range(len(indices) - 1):
        assert indices[i+1] - indices[i] == 1, "Consecutive indices must differ by exactly 1"

def test_mutation_numpy_branch_condition():
    # Detects: wrong isinstance check (e.g., using list instead of np.ndarray)
    # numpy array must go through ndenumerate (tuple indices)
    arr = np.array([1, 2, 3])
    result = consume(tenumerate(arr, disable=True))
    assert isinstance(result[0][0], tuple), "numpy branch must produce tuple indices"

def test_mutation_non_numpy_avoids_ndenumerate():
    # Detects: if isinstance check is inverted (always using ndenumerate)
    data = [1, 2, 3]
    result = consume(tenumerate(data, disable=True))
    assert isinstance(result[0][0], int), "non-numpy path must produce integer indices"

def test_mutation_total_default_none_numpy():
    # Detects: `total and len(iterable)` vs `total or len(iterable)`
    # When total=None, should fall back to len(iterable) for numpy arrays
    arr = np.array([1, 2, 3])
    # Just ensure it works and produces correct number of items
    result = consume(tenumerate(arr, total=None, disable=True))
    assert len(result) == 3

def test_mutation_total_override_numpy():
    # Detects: `total or len(iterable)` — if total is provided and truthy, use it
    arr = np.array([1, 2, 3])
    # total=5 is provided but iterable only has 3 elements — result still 3 items
    result = consume(tenumerate(arr, total=5, disable=True))
    assert len(result) == 3  # actual items from ndenumerate

def test_mutation_values_preserved_list():
    # Detects: values being dropped or swapped with indices
    data = [100, 200, 300]
    result = consume(tenumerate(data, disable=True))
    values = [v for _, v in result]
    assert values == data, "Values must be preserved exactly as in input"

def test_mutation_values_preserved_numpy():
    # Detects: values being dropped or modified in numpy path
    arr = np.array([7, 8, 9])
    result = consume(tenumerate(arr, disable=True))
    values = [v for _, v in result]
    assert list(values) == [7, 8, 9], "Values must equal original array elements"

def test_mutation_length_preserved_list():
    # Detects: off-by-one in loop — consuming one too few or one too many elements
    data = list(range(10))
    result = consume(tenumerate(data, disable=True))
    assert len(result) == len(data), "Result length must equal input length"

def test_mutation_length_preserved_numpy():
    # Detects: off-by-one in numpy path
    arr = np.arange(7)
    result = consume(tenumerate(arr, disable=True))
    assert len(result) == 7

def test_mutation_start_not_applied_to_numpy():
    # numpy path uses ndenumerate which ignores start — indices are tuple-based positions
    arr = np.array([10, 20, 30])
    result = consume(tenumerate(arr, start=5, disable=True))
    # ndenumerate always starts at (0,), (1,), ... regardless of start
    assert result[0][0] == (0,), "numpy ndenumerate must use positional tuple indices, not start offset"

def test_mutation_correct_index_value_pairing():
    # Detects: index and value being swapped
    data = [99, 88, 77]
    result = consume(tenumerate(data, disable=True))
    for i, (idx, val) in enumerate(result):
        assert idx == i, f"Index at position {i} should be {i}"
        assert val == data[i], f"Value at position {i} should be {data[i]}"

def test_mutation_numpy_2d_index_tuples():
    # Detects: flattening or wrong indexing in 2D numpy arrays
    arr = np.array([[1, 2], [3, 4]])
    result = consume(tenumerate(arr, disable=True))
    expected = list(np.ndenumerate(arr))
    assert result == expected, "2D numpy array must use ndenumerate multi-index tuples"