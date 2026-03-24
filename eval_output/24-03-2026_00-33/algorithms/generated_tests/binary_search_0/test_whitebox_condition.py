from algorithms.searching.binary_search import binary_search

# condition: low <= high: True, val == query: True
def test_binary_search_found_middle():
    assert binary_search([1, 2, 3, 4, 5], 3) == 2

# condition: low <= high: True, val == query: False, val < query: True
def test_binary_search_val_less_than_query():
    assert binary_search([1, 2, 3, 4, 5], 4) == 3

# condition: low <= high: True, val == query: False, val < query: False
def test_binary_search_val_greater_than_query():
    assert binary_search([1, 2, 3, 4, 5], 2) == 1

# condition: low <= high: False (loop not entered)
def test_binary_search_empty_array():
    assert binary_search([], 1) == -1

# condition: low <= high: True initially, becomes False after narrowing
def test_binary_search_not_found():
    assert binary_search([1, 2, 3, 4, 5], 6) == -1

# condition: low <= high: True, val == query: True on first iteration
def test_binary_search_found_first_element():
    assert binary_search([1, 2, 3, 4, 5], 1) == 0

# condition: low <= high: True, val == query: True on last iteration
def test_binary_search_found_last_element():
    assert binary_search([1, 2, 3, 4, 5], 5) == 4

# condition: low <= high: True, val == query: False, val < query: True (multiple times)
def test_binary_search_val_less_than_query_multiple_steps():
    assert binary_search([1, 3, 5, 7, 9], 7) == 3

# condition: low <= high: True, val == query: False, val < query: False (multiple times)
def test_binary_search_val_greater_than_query_multiple_steps():
    assert binary_search([1, 3, 5, 7, 9], 3) == 1