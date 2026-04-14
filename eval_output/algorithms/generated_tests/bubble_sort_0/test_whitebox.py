import pytest
from algorithms.sorting.bubble_sort import bubble_sort

# --- Statement Coverage ---

def test_empty_list():
    # Covers: n = 0, while swapped condition false, return array
    result = bubble_sort([])
    # A correct bubble sort of an empty list returns an empty list
    assert result == []

def test_single_element():
    # Covers: n = 1, while swapped condition true, for loop range(1, 1) -> zero iterations, swapped remains False, passes increments, while loop exits
    result = bubble_sort([5])
    assert result == [5]

def test_two_elements_unsorted():
    # Covers: n = 2, while swapped true, for loop iterates once (i=1), if condition true, swap, swapped set True, passes increments, another while iteration, for loop range(1, 1) -> zero iterations, swapped remains False, exit
    result = bubble_sort([2, 1])
    # Correct bubble sort should produce [1, 2]
    assert result == [1, 2]

def test_already_sorted():
    # Covers: while swapped true, for loop iterates, if condition false for all i, swapped remains False, passes increments, while loop exits
    result = bubble_sort([1, 2, 3])
    assert result == [1, 2, 3]

def test_multiple_elements_unsorted():
    # Covers: while swapped true, for loop multiple iterations, at least one swap, swapped True, passes increments, another while iteration, etc.
    result = bubble_sort([3, 1, 4, 2])
    # Correct bubble sort ascending order
    assert result == [1, 2, 3, 4]

# --- Block Coverage ---
# Block coverage is already achieved by statement coverage tests above.
# No new blocks need to be covered.

# --- Condition Coverage ---

def test_condition_if_true():
    # array[i-1] > array[i]: True
    # This occurs during a swap.
    result = bubble_sort([5, 3])
    # Correct output after swap
    assert result == [3, 5]

def test_condition_if_false():
    # array[i-1] > array[i]: False
    # This occurs when elements are in order.
    result = bubble_sort([3, 5])
    assert result == [3, 5]

def test_while_swapped_true_then_false():
    # while swapped: True initially, then becomes False after a pass with no swaps.
    # Already covered by test_already_sorted.
    pass

def test_while_swapped_false_immediately():
    # while swapped: False initially (when n=0).
    # Already covered by test_empty_list.
    pass

# --- Path Coverage ---

def test_path_empty():
    # path: n=0 -> swapped=True -> while condition false -> return array
    result = bubble_sort([])
    assert result == []

def test_path_single_element():
    # path: n=1 -> swapped=True -> while true -> for loop zero iterations -> swapped remains False -> passes+=1 -> while condition false -> return
    result = bubble_sort([7])
    assert result == [7]

def path_two_elements_sorted():
    # path: n=2 -> swapped=True -> while true -> for loop one iteration, if false -> swapped remains False -> passes+=1 -> while false -> return
    result = bubble_sort([1, 2])
    assert result == [1, 2]

def test_path_two_elements_unsorted():
    # path: n=2 -> swapped=True -> while true -> for loop one iteration, if true -> swap, swapped=True -> passes+=1 -> while true again -> for loop zero iterations (n-passes=0) -> swapped remains False -> passes+=1 -> while false -> return
    result = bubble_sort([2, 1])
    assert result == [1, 2]

def test_path_three_elements_one_pass_sufficient():
    # path: n=3, initial order [1,3,2] -> first pass: compare (1,3) no swap, compare (3,2) swap -> swapped=True -> passes=1 -> second pass: range(1, 2) -> compare (1,2) no swap -> swapped remains False -> passes=2 -> exit
    result = bubble_sort([1, 3, 2])
    assert result == [1, 2, 3]

def test_path_three_elements_worst_case():
    # path: n=3, initial order [3,2,1] -> first pass: (3,2) swap, (3,1) swap -> swapped=True -> passes=1 -> second pass: range(1, 2) -> compare (2,1) swap -> swapped=True -> passes=2 -> third pass: range(1, 1) zero iterations -> swapped remains False -> passes=3 -> exit
    result = bubble_sort([3, 2, 1])
    assert result == [1, 2, 3]

def test_path_multiple_passes_with_early_exit():
    # path: n=4, initial order [2,1,3,4] -> first pass: (2,1) swap, (2,3) no swap, (3,4) no swap -> swapped=True -> passes=1 -> second pass: range(1, 3) -> (1,2) no swap, (2,3) no swap -> swapped remains False -> passes=2 -> exit
    result = bubble_sort([2, 1, 3, 4])
    assert result == [1, 2, 3, 4]

# Additional loop coverage: zero iterations of for loop already covered (single element, second pass of two-element unsorted).
# One iteration of for loop covered (two-element cases).
# Multiple iterations of for loop covered (three or more elements).