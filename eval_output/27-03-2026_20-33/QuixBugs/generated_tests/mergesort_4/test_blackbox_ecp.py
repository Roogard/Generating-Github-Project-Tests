import pytest
from python_programs.mergesort import mergesort

# Valid equivalence class: single-element array (already sorted, trivial)
def test_single_element():
    result = mergesort([42])
    assert result == [42]
    assert len(result) == 1

# Valid equivalence class: already sorted array
def test_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert all(not isinstance(x, list) for x in result)

# Valid equivalence class: reverse sorted array
def test_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: array with duplicate elements
def test_with_duplicates():
    arr = [3, 1, 2, 3, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: array with all identical elements
def test_all_identical():
    arr = [7, 7, 7, 7]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: array with negative numbers
def test_negative_numbers():
    arr = [-3, -1, -7, -2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: array with mixed positive and negative numbers
def test_mixed_positive_negative():
    arr = [3, -1, 0, -5, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: array with two elements (smallest non-trivial merge)
def test_two_elements():
    arr = [2, 1]
    result = mergesort(arr)
    assert result == [1, 2]
    assert len(result) == 2

# Valid equivalence class: empty array
def test_empty_array():
    result = mergesort([])
    assert result == []
    assert len(result) == 0

# Valid equivalence class: array with floating point numbers
def test_float_elements():
    arr = [3.14, 1.41, 2.71, 0.57]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: large array (stress test for recursion correctness)
def test_large_array():
    import random
    random.seed(0)
    arr = random.sample(range(1000), 100)
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    # Verify no elements dropped or added
    assert sorted(result) == sorted(arr)