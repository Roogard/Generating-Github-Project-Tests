import pytest
from algorithms.searching.binary_search import binary_search

# path: while loop 0 iterations (low > high initially) -> return -1
def test_binary_search_empty_array():
    assert binary_search([], 5) == -1

# path: while loop 1 iteration -> val == query -> return mid
def test_binary_search_single_element_found():
    assert binary_search([7], 7) == 0

# path: while loop 1 iteration -> val != query -> val < query -> low = mid+1 -> loop exits -> return -1
def test_binary_search_single_element_not_found_greater():
    assert binary_search([7], 10) == -1

# path: while loop 1 iteration -> val != query -> val > query -> high = mid-1 -> loop exits -> return -1
def test_binary_search_single_element_not_found_less():
    assert binary_search([7], 3) == -1

# path: while loop 2 iterations -> first: val != query, val < query -> low = mid+1 -> second: val == query -> return mid
def test_binary_search_two_elements_found_second():
    assert binary_search([1, 2], 2) == 1

# path: while loop 2 iterations -> first: val != query, val > query -> high = mid-1 -> second: val == query -> return mid
def test_binary_search_two_elements_found_first():
    assert binary_search([1, 2], 1) == 0

# path: while loop 2 iterations -> first: val != query, val < query -> low = mid+1 -> second: val != query, val > query -> high = mid-1 -> loop exits -> return -1
def test_binary_search_two_elements_not_found():
    assert binary_search([1, 3], 2) == -1

# path: while loop multiple iterations -> always val < query -> low updates -> eventually loop exits -> return -1 (query > all)
def test_binary_search_multiple_elements_not_found_greater():
    assert binary_search([1, 3, 5, 7, 9], 11) == -1

# path: while loop multiple iterations -> always val > query -> high updates -> eventually loop exits -> return -1 (query < all)
def test_binary_search_multiple_elements_not_found_less():
    assert binary_search([1, 3, 5, 7, 9], 0) == -1

# path: while loop multiple iterations -> mixed val < query / val > query -> eventually val == query -> return mid
def test_binary_search_multiple_elements_found_middle():
    assert binary_search([1, 3, 5, 7, 9, 11, 13], 7) == 3

# path: while loop multiple iterations -> mixed val < query / val > query -> eventually loop exits -> return -1 (query between elements)
def test_binary_search_multiple_elements_not_found_between():
    assert binary_search([1, 3, 5, 7, 9, 11, 13], 8) == -1

# path: while loop multiple iterations -> found on first mid (val == query immediately)
def test_binary_search_found_first_mid():
    assert binary_search([1, 2, 3, 4, 5], 3) == 2

# path: while loop multiple iterations -> found on last possible iteration (low == high)
def test_binary_search_found_last_iteration():
    assert binary_search([1, 2, 3, 4, 5], 1) == 0