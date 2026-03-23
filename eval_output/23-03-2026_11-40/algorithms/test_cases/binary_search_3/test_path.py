import pytest
from algorithms.searching.binary_search import binary_search

# path: while loop condition false initially (low > high) → return -1
def test_binary_search_empty():
    assert binary_search([], 5) == -1

# path: while true → val == query → return mid (first iteration)
def test_binary_search_single_element_found():
    assert binary_search([5], 5) == 0

# path: while true → val != query → val < query → low = mid+1 → while false → return -1
def test_binary_search_single_element_not_found_greater():
    assert binary_search([3], 5) == -1

# path: while true → val != query → val > query → high = mid-1 → while false → return -1
def test_binary_search_single_element_not_found_less():
    assert binary_search([7], 5) == -1

# path: while true → val != query → val < query → low = mid+1 → while true (second iteration) → val == query → return mid
def test_binary_search_two_elements_found_second():
    assert binary_search([1, 2], 2) == 1

# path: while true → val != query → val > query → high = mid-1 → while true (second iteration) → val == query → return mid
def test_binary_search_two_elements_found_first():
    assert binary_search([1, 2], 1) == 0

# path: while true → val != query → val < query → low = mid+1 → while false → return -1
def test_binary_search_two_elements_not_found_greater():
    assert binary_search([1, 2], 3) == -1

# path: while true → val != query → val > query → high = mid-1 → while false → return -1
def test_binary_search_two_elements_not_found_less():
    assert binary_search([1, 2], 0) == -1

# path: while true → val != query → val < query → low = mid+1 → while true (second iteration) → val != query → val < query → low = mid+1 → while false → return -1
def test_binary_search_three_elements_not_found_rightmost():
    assert binary_search([1, 2, 3], 4) == -1

# path: while true → val != query → val > query → high = mid-1 → while true (second iteration) → val != query → val > query → high = mid-1 → while false → return -1
def test_binary_search_three_elements_not_found_leftmost():
    assert binary_search([1, 2, 3], 0) == -1

# path: while true → val != query → val < query → low = mid+1 → while true (second iteration) → val == query → return mid
def test_binary_search_three_elements_found_right():
    assert binary_search([1, 2, 3], 3) == 2

# path: while true → val != query → val > query → high = mid-1 → while true (second iteration) → val == query → return mid
def test_binary_search_three_elements_found_left():
    assert binary_search([1, 2, 3], 1) == 0

# path: while true → val != query → val < query → low = mid+1 → while true (second iteration) → val != query → val > query → high = mid-1 → while true (third iteration) → val == query → return mid
def test_binary_search_four_elements_found_middle():
    assert binary_search([1, 2, 3, 4], 3) == 2

# path: while true → val != query → val > query → high = mid-1 → while true (second iteration) → val != query → val < query → low = mid+1 → while true (third iteration) → val == query → return mid
def test_binary_search_four_elements_found_other_middle():
    assert binary_search([1, 2, 3, 4], 2) == 1

# path: many iterations, query found after multiple low updates
def test_binary_search_large_found():
    arr = list(range(1, 100))
    assert binary_search(arr, 78) == 77

# path: many iterations, query not found after multiple updates
def test_binary_search_large_not_found():
    arr = list(range(1, 100, 2))  # odd numbers only
    assert binary_search(arr, 50) == -1