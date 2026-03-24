from algorithms.searching.binary_search import binary_search

# covers: low, high = 0, len(array) - 1, while low <= high (True), mid = low + (high - low) // 2, val = array[mid], if val == query (True), return mid
def test_binary_search_found_middle():
    assert binary_search([1, 2, 3, 4, 5], 3) == 2

# covers: low, high = 0, len(array) - 1, while low <= high (True), mid = low + (high - low) // 2, val = array[mid], if val == query (False), if val < query (True), low = mid + 1, while loop repeats, eventually returns mid
def test_binary_search_found_after_mid():
    assert binary_search([1, 2, 3, 4, 5], 4) == 3

# covers: low, high = 0, len(array) - 1, while low <= high (True), mid = low + (high - low) // 2, val = array[mid], if val == query (False), if val < query (False), else: high = mid - 1, while loop repeats, eventually returns mid
def test_binary_search_found_before_mid():
    assert binary_search([1, 2, 3, 4, 5], 2) == 1

# covers: low, high = 0, len(array) - 1, while low <= high (True), loop executes multiple times, eventually while low <= high (False), return -1
def test_binary_search_not_found():
    assert binary_search([1, 2, 3, 4, 5], 6) == -1

# covers: low, high = 0, len(array) - 1, while low <= high (False) immediately, return -1
def test_binary_search_empty_array():
    assert binary_search([], 1) == -1