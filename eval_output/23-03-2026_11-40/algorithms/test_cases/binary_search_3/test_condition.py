from algorithms.searching.binary_search import binary_search

# condition: low <= high: True, val == query: True → return mid
def test_binary_search_found_middle():
    # low <= high: True, val == query: True
    assert binary_search([1, 2, 3, 4, 5], 3) == 2

# condition: low <= high: True, val == query: False, val < query: True → low = mid + 1
def test_binary_search_query_greater():
    # low <= high: True, val == query: False, val < query: True
    assert binary_search([1, 2, 3, 4, 5], 4) == 3

# condition: low <= high: True, val == query: False, val < query: False → high = mid - 1
def test_binary_search_query_less():
    # low <= high: True, val == query: False, val < query: False
    assert binary_search([1, 2, 3, 4, 5], 2) == 1

# condition: low <= high: False → return -1
def test_binary_search_not_found():
    # low <= high: False
    assert binary_search([1, 2, 3, 4, 5], 6) == -1

# condition: low <= high: True, val == query: True (first element)
def test_binary_search_found_first():
    # low <= high: True, val == query: True
    assert binary_search([1, 2, 3, 4, 5], 1) == 0

# condition: low <= high: True, val == query: True (last element)
def test_binary_search_found_last():
    # low <= high: True, val == query: True
    assert binary_search([1, 2, 3, 4, 5], 5) == 4

# condition: low <= high: True, val == query: False, val < query: True (multiple steps)
def test_binary_search_query_greater_multiple_steps():
    # low <= high: True, val == query: False, val < query: True (first step)
    # then low <= high: True, val == query: True (second step)
    assert binary_search([1, 3, 5, 7, 9], 7) == 3

# condition: low <= high: True, val == query: False, val < query: False (multiple steps)
def test_binary_search_query_less_multiple_steps():
    # low <= high: True, val == query: False, val < query: False (first step)
    # then low <= high: True, val == query: True (second step)
    assert binary_search([1, 3, 5, 7, 9], 3) == 1

# condition: empty array, low <= high: False immediately
def test_binary_search_empty_array():
    # low <= high: False
    assert binary_search([], 1) == -1

# condition: single element, low <= high: True, val == query: True
def test_binary_search_single_element_found():
    # low <= high: True, val == query: True
    assert binary_search([5], 5) == 0

# condition: single element, low <= high: True, val == query: False, val < query: True
def test_binary_search_single_element_query_greater():
    # low <= high: True, val == query: False, val < query: True
    # then low <= high: False, return -1
    assert binary_search([5], 10) == -1

# condition: single element, low <= high: True, val == query: False, val < query: False
def test_binary_search_single_element_query_less():
    # low <= high: True, val == query: False, val < query: False
    # then low <= high: False, return -1
    assert binary_search([5], 1) == -1