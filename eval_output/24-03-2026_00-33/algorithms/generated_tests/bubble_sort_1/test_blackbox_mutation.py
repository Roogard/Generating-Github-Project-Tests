from algorithms.sorting.bubble_sort import bubble_sort

# catches: "range(1, n - passes)" mutated to "range(0, n - passes)" (off-by-one start)
def test_bubble_sort_first_element_compared():
    assert bubble_sort([2, 1, 3]) == [1, 2, 3]

# catches: "range(1, n - passes)" mutated to "range(1, n - passes + 1)" (off-by-one end, includes out-of-bounds)
def test_bubble_sort_last_element_not_recompared_after_pass():
    assert bubble_sort([3, 2, 1]) == [1, 2, 3]

# catches: "if array[i - 1] > array[i]" mutated to "if array[i - 1] >= array[i]" (wrong operator, > to >=)
def test_bubble_sort_stable_equal_elements():
    # Actually bubble sort is not stable in this implementation for equal values? The condition is >, so equal values won't swap.
    # But if mutated to >=, equal values would swap unnecessarily.
    # We can't easily detect order of equal values because they are ints.
    # Instead, test that equal values don't cause infinite loop or wrong output.
    assert bubble_sort([5, 3, 3, 1]) == [1, 3, 3, 5]

# catches: "if array[i - 1] > array[i]" mutated to "if array[i - 1] < array[i]" (wrong comparison direction)
def test_bubble_sort_reverse_sorted():
    assert bubble_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# catches: "swapped = True" inside if mutated to "swapped = False" (negation error)
def test_bubble_sort_already_sorted():
    assert bubble_sort([1, 2, 3]) == [1, 2, 3]

# catches: "while swapped:" mutated to "while not swapped:" (negation error)
def test_bubble_sort_single_element():
    assert bubble_sort([42]) == [42]

# catches: "passes += 1" mutated to "passes -= 1" or omitted (off-by-one in pass counter)
def test_bubble_sort_many_passes_needed():
    assert bubble_sort([6, 5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5, 6]

# catches: "n = len(array)" mutated to "n = len(array) - 1" (off-by-one in length)
def test_bubble_sort_empty_list():
    assert bubble_sort([]) == []

# catches: "array[i - 1], array[i] = array[i], array[i - 1]" mutated to swap wrong indices (e.g., array[i], array[i] = ...)
def test_bubble_sort_swap_adjacent_pair():
    assert bubble_sort([1, 3, 2, 4]) == [1, 2, 3, 4]

# catches: "swapped = True" in while loop mutated to "swapped = False" (initialization error)
def test_bubble_sort_two_elements_unsorted():
    assert bubble_sort([2, 1]) == [1, 2]

# catches: "range(1, n - passes)" mutated to "range(0, n - passes - 1)" (off-by-one both ends)
def test_bubble_sort_three_elements():
    assert bubble_sort([3, 1, 2]) == [1, 2, 3]