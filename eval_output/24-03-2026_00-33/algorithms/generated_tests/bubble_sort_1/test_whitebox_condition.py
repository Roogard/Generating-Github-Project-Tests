from algorithms.sorting.bubble_sort import bubble_sort

# condition: swapped: True (initial) → enter while loop
# condition: array[i-1] > array[i]: True → swap occurs, swapped becomes True
def test_bubble_sort_with_unsorted():
    # swapped: True initially, enters loop
    # In first pass, at least one comparison is True (3>1)
    result = bubble_sort([3, 1, 2])
    assert result == [1, 2, 3]

# condition: swapped: False (after first pass) → exit while loop after one pass
# condition: array[i-1] > array[i]: False for all i → no swaps, swapped remains False
def test_bubble_sort_already_sorted():
    # swapped: True initially, enters loop
    # In first pass, all comparisons are False (1<2, 2<3)
    # swapped remains False, loop exits after one pass
    result = bubble_sort([1, 2, 3])
    assert result == [1, 2, 3]

# condition: swapped: True (initial) → enter while loop
# condition: array[i-1] > array[i]: True for some, False for others → mixed
def test_bubble_sort_reverse_sorted():
    # swapped: True initially, enters loop
    # In first pass, many comparisons are True (3>2, 2>1)
    result = bubble_sort([3, 2, 1])
    assert result == [1, 2, 3]

# condition: n - passes > 1 → inner for loop iterates at least once
# condition: n - passes == 1 → inner for loop range(1,1) is empty, no iterations
def test_bubble_sort_single_element():
    # n=1, passes=0 → n-passes=1 → range(1,1) empty, no comparisons
    # swapped remains False after first pass, loop exits
    result = bubble_sort([5])
    assert result == [5]

# condition: array[i-1] > array[i]: True only at specific positions
def test_bubble_sort_two_elements_unsorted():
    # swapped: True initially
    # In first pass, comparison True (2>1) → swap, swapped=True
    # Next pass, n-passes=1 → no comparisons, swapped=False, loop exits
    result = bubble_sort([2, 1])
    assert result == [1, 2]

# condition: array[i-1] > array[i]: False for all in two-element sorted case
def test_bubble_sort_two_elements_sorted():
    # swapped: True initially
    # In first pass, comparison False (1<2) → no swap, swapped=False
    # Loop exits after one pass
    result = bubble_sort([1, 2])
    assert result == [1, 2]

# condition: while swapped: False initially? Not possible because swapped=True initially.
# But we can test that after first pass with no swaps, loop exits.
# This is covered by test_bubble_sort_already_sorted.

# Additional test to ensure condition coverage for inner loop boundary
# condition: n - passes > 1 initially, but after passes increment, n - passes becomes 1
def test_bubble_sort_three_elements_one_swap_needed():
    # Initial: [2,1,3]
    # Pass 1: compare 2>1 → True, swap to [1,2,3]; compare 2>3 → False
    # swapped=True after pass 1
    # Pass 2: n-passes=1 → no comparisons, swapped=False, loop exits
    result = bubble_sort([2, 1, 3])
    assert result == [1, 2, 3]