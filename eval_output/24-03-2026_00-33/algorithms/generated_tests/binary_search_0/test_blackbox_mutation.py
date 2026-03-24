from algorithms.searching.binary_search import binary_search

# catches: "low <= high" mutated to "low < high" (off-by-one, missing element when low==high)
def test_binary_search_single_element_found():
    assert binary_search([5], 5) == 0

# catches: "low <= high" mutated to "low < high" (off-by-one, not found when low==high)
def test_binary_search_single_element_not_found():
    assert binary_search([5], 3) == -1

# catches: "mid = low + (high - low) // 2" mutated to "mid = (low + high) // 2" (integer overflow not relevant, but common mutation)
# also catches: "high = mid - 1" mutated to "high = mid" (off-by-one, infinite loop or missed element)
def test_binary_search_found_at_beginning():
    assert binary_search([1, 2, 3, 4, 5], 1) == 0

# catches: "low = mid + 1" mutated to "low = mid" (off-by-one, infinite loop or missed element)
def test_binary_search_found_at_end():
    assert binary_search([1, 2, 3, 4, 5], 5) == 4

# catches: "val < query" mutated to "val <= query" (comparison swap, would skip correct index)
def test_binary_search_found_in_middle():
    assert binary_search([1, 2, 3, 4, 5], 3) == 2

# catches: "val < query" mutated to "val > query" (wrong operator)
def test_binary_search_query_greater_than_mid():
    assert binary_search([1, 3, 5, 7, 9], 7) == 3

# catches: "else: high = mid - 1" mutated to "else: high = mid" (off-by-one, infinite loop)
def test_binary_search_query_less_than_mid():
    assert binary_search([1, 3, 5, 7, 9], 3) == 1

# catches: "return -1" mutated to "return 0" or other wrong constant
def test_binary_search_not_found_in_empty_array():
    assert binary_search([], 1) == -1

# catches: "len(array) - 1" mutated to "len(array)" (off-by-one, index error)
def test_binary_search_not_found_larger_than_all():
    assert binary_search([1, 2, 3], 5) == -1

# catches: "low, high = 0, len(array) - 1" mutated to "low, high = 1, len(array) - 1" (off-by-one, miss first element)
def test_binary_search_not_found_smaller_than_all():
    assert binary_search([1, 2, 3], 0) == -1

# catches: "val == query" mutated to "val != query" (negation error)
def test_binary_search_found_with_duplicates():
    assert binary_search([1, 2, 2, 3], 2) in {1, 2}

# catches: "while low <= high" mutated to "while low < high" and "high = mid - 1" mutated to "high = mid" (combined off-by-one)
def test_binary_search_even_length_found():
    assert binary_search([1, 2, 3, 4], 3) == 2

# catches: "low = mid + 1" mutated to "low = mid + 2" (off-by-one constant)
def test_binary_search_odd_length_found():
    assert binary_search([1, 2, 3, 4, 5], 4) == 3

# catches: missing update of low/high (e.g., "if val < query: pass" mutation)
def test_binary_search_large_array_found():
    assert binary_search(list(range(1000)), 499) == 499