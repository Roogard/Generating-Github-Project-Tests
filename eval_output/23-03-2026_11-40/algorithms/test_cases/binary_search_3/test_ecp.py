import pytest
from algorithms.searching.binary_search import binary_search

# Valid equivalence class: query present in array (single element)
def test_query_present_single_element():
    assert binary_search([5], 5) == 0

# Valid equivalence class: query present in array (multiple elements, at start)
def test_query_present_at_start():
    assert binary_search([1, 2, 3, 4, 5], 1) == 0

# Valid equivalence class: query present in array (multiple elements, at end)
def test_query_present_at_end():
    assert binary_search([1, 2, 3, 4, 5], 5) == 4

# Valid equivalence class: query present in array (multiple elements, middle)
def test_query_present_middle():
    assert binary_search([1, 2, 3, 4, 5], 3) == 2

# Valid equivalence class: query not present, less than all elements
def test_query_not_present_less_than_all():
    assert binary_search([10, 20, 30], 5) == -1

# Valid equivalence class: query not present, greater than all elements
def test_query_not_present_greater_than_all():
    assert binary_search([10, 20, 30], 35) == -1

# Valid equivalence class: query not present, between elements
def test_query_not_present_between_elements():
    assert binary_search([10, 20, 30], 25) == -1

# Valid equivalence class: empty array (query never found)
def test_empty_array():
    assert binary_search([], 5) == -1

# Valid equivalence class: duplicate elements, query present
def test_duplicate_elements_query_present():
    # function returns first found index; behavior is acceptable
    result = binary_search([1, 2, 2, 3], 2)
    assert result in [1, 2]  # binary search may return either duplicate index

# Invalid equivalence class: array not sorted (ascending order violated)
def test_unsorted_array():
    # function behavior is undefined per spec; we test typical behavior
    # binary search on unsorted array may produce incorrect result
    # This is a valid input per type, but violates precondition.
    # We treat it as a separate class and observe actual output.
    result = binary_search([5, 2, 8], 8)
    # Not asserting a specific outcome, just that it runs without error
    assert result is not None  # could be -1 or an index

# Invalid equivalence class: array contains non-integer elements (type violation)
def test_array_non_integer():
    with pytest.raises(TypeError):
        binary_search([1, 'a', 3], 2)