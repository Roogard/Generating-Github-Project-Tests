import pytest
from algorithms.searching.binary_search import binary_search

# Valid equivalence class: query present in array (single element)
def test_query_present_single_element():
    assert binary_search([5], 5) == 0

# Valid equivalence class: query present in array (multiple elements, first half)
def test_query_present_first_half():
    assert binary_search([1, 2, 3, 4, 5], 2) == 1

# Valid equivalence class: query present in array (multiple elements, second half)
def test_query_present_second_half():
    assert binary_search([1, 2, 3, 4, 5], 4) == 3

# Valid equivalence class: query present at first index
def test_query_present_at_first_index():
    assert binary_search([1, 2, 3, 4, 5], 1) == 0

# Valid equivalence class: query present at last index
def test_query_present_at_last_index():
    assert binary_search([1, 2, 3, 4, 5], 5) == 4

# Valid equivalence class: query not present, smaller than all elements
def test_query_not_present_smaller():
    assert binary_search([1, 2, 3, 4, 5], 0) == -1

# Valid equivalence class: query not present, larger than all elements
def test_query_not_present_larger():
    assert binary_search([1, 2, 3, 4, 5], 6) == -1

# Valid equivalence class: query not present, within range but missing
def test_query_not_present_middle():
    assert binary_search([1, 3, 5, 7, 9], 4) == -1

# Valid equivalence class: empty array
def test_empty_array():
    assert binary_search([], 5) == -1

# Valid equivalence class: array with duplicate values, query present
def test_query_present_with_duplicates():
    assert binary_search([1, 2, 2, 3, 4], 2) in [1, 2]

# Valid equivalence class: array with duplicate values, query not present
def test_query_not_present_with_duplicates():
    assert binary_search([1, 1, 3, 3, 5], 2) == -1