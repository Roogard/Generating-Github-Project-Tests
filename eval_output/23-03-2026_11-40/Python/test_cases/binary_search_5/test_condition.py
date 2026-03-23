from matrix.binary_search_matrix import binary_search

# condition: array[r] == value: True
def test_binary_search_found_middle():
    # array[r] == value: True, lower_bound >= upper_bound: False, array[r] < value: False
    assert binary_search([1, 2, 3], 0, 2, 2) == 1

# condition: array[r] == value: False, lower_bound >= upper_bound: True
def test_binary_search_not_found_single_element():
    # array[r] == value: False, lower_bound >= upper_bound: True
    assert binary_search([5], 0, 0, 3) == -1

# condition: array[r] == value: False, lower_bound >= upper_bound: False, array[r] < value: True
def test_binary_search_recursive_right_side():
    # array[r] == value: False, lower_bound >= upper_bound: False, array[r] < value: True
    assert binary_search([1, 2, 3, 4, 5], 0, 4, 5) == 4

# condition: array[r] == value: False, lower_bound >= upper_bound: False, array[r] < value: False
def test_binary_search_recursive_left_side():
    # array[r] == value: False, lower_bound >= upper_bound: False, array[r] < value: False
    assert binary_search([1, 2, 3, 4, 5], 0, 4, 1) == 0

# condition: lower_bound >= upper_bound: True (with lower_bound > upper_bound)
def test_binary_search_invalid_bounds():
    # array[r] == value: False, lower_bound >= upper_bound: True (lower_bound > upper_bound)
    assert binary_search([1, 2, 3], 2, 1, 2) == -1

# condition: array[r] == value: True on first call, but also covers lower_bound >= upper_bound: False, array[r] < value: False
def test_binary_search_found_at_start():
    # array[r] == value: True
    assert binary_search([1, 2, 3], 0, 2, 1) == 0

# condition: array[r] == value: True on recursive call (right side)
def test_binary_search_found_at_end():
    # array[r] == value: True (after recursion)
    assert binary_search([1, 2, 3, 4, 5], 0, 4, 5) == 4

# condition: array[r] == value: False, lower_bound >= upper_bound: False, array[r] < value: True leading to not found
def test_binary_search_not_found_right_side():
    # array[r] == value: False, lower_bound >= upper_bound: False, array[r] < value: True (recurses until not found)
    assert binary_search([1, 2, 3, 4, 5], 0, 4, 6) == -1

# condition: array[r] == value: False, lower_bound >= upper_bound: False, array[r] < value: False leading to not found
def test_binary_search_not_found_left_side():
    # array[r] == value: False, lower_bound >= upper_bound: False, array[r] < value: False (recurses until not found)
    assert binary_search([1, 2, 3, 4, 5], 0, 4, 0) == -1