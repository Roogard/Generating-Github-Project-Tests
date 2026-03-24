import pytest
from algorithms.searching.binary_search import binary_search

# Valid equivalence class: query present in non-empty array
def test_query_present_in_non_empty():
    assert binary_search([1, 2, 3, 4, 5], 3) == 2

# Valid equivalence class: query absent in non-empty array
def test_query_absent_in_non_empty():
    assert binary_search([1, 2, 3, 4, 5], 6) == -1

# Valid equivalence class: query present at first index
def test_query_at_first_index():
    assert binary_search([1, 2, 3, 4, 5], 1) == 0

# Valid equivalence class: query present at last index
def test_query_at_last_index():
    assert binary_search([1, 2, 3, 4, 5], 5) == 4

# Valid equivalence class: array with single element, query present
def test_single_element_array_query_present():
    assert binary_search([7], 7) == 0

# Valid equivalence class: array with single element, query absent
def test_single_element_array_query_absent():
    assert binary_search([7], 8) == -1

# Valid equivalence class: empty array (query always absent)
def test_empty_array():
    assert binary_search([], 5) == -1

# Valid equivalence class: array with duplicate values, query present
def test_duplicate_values_query_present():
    # binary search may return any matching index; we accept any valid index
    result = binary_search([1, 2, 2, 2, 3], 2)
    assert result in [1, 2, 3]

# Valid equivalence class: array with duplicate values, query absent
def test_duplicate_values_query_absent():
    assert binary_search([1, 2, 2, 2, 3], 4) == -1

# Valid equivalence class: large array, query present
def test_large_array_query_present():
    arr = list(range(1000))
    assert binary_search(arr, 500) == 500

# Valid equivalence class: large array, query absent
def test_large_array_query_absent():
    arr = list(range(1000))
    assert binary_search(arr, 1500) == -1

# Invalid equivalence class: array not sorted (assumption violated)
def test_unsorted_array():
    # Behavior is undefined per spec; we test that it doesn't crash and returns something
    # This is a robustness test for invalid input class.
    result = binary_search([3, 1, 2], 2)
    # We don't assert a specific result, just that it runs without exception
    assert isinstance(result, int)

# Invalid equivalence class: array contains non-integers (type violation)
def test_array_with_non_integers():
    # The type hint is list[int]; passing other types may cause TypeError.
    # We test that it raises TypeError when comparing.
    with pytest.raises(TypeError):
        binary_search([1, 'a', 3], 2)

# Invalid equivalence class: query is not an integer
def test_query_non_integer():
    with pytest.raises(TypeError):
        binary_search([1, 2, 3], 'x')