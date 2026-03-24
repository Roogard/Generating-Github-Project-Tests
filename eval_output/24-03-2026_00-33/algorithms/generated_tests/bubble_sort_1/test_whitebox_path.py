import pytest
from algorithms.sorting.bubble_sort import bubble_sort

# path: while loop 0 iterations (swapped initially True, but n <= 1 so inner for loop does 0 iterations, swapped remains False, while loop exits after 1 pass)
def test_bubble_sort_empty():
    assert bubble_sort([]) == []

# path: while loop 0 iterations (swapped initially True, but n <= 1 so inner for loop does 0 iterations, swapped remains False, while loop exits after 1 pass)
def test_bubble_sort_single():
    assert bubble_sort([5]) == [5]

# path: while loop 1 iteration, inner for loop 1 iteration, if condition True, swapped becomes True, while loop second iteration, inner for loop 0 iterations (n - passes = 0), swapped remains False, while loop exits
def test_bubble_sort_two_descending():
    assert bubble_sort([2, 1]) == [1, 2]

# path: while loop 1 iteration, inner for loop 1 iteration, if condition False, swapped remains False, while loop exits
def test_bubble_sort_two_ascending():
    assert bubble_sort([1, 2]) == [1, 2]

# path: while loop 1 iteration, inner for loop many iterations (2+), at least one if condition True, swapped becomes True, while loop second iteration, inner for loop fewer iterations, all if conditions False, swapped remains False, while loop exits
def test_bubble_sort_multiple_one_pass():
    assert bubble_sort([3, 1, 2]) == [1, 2, 3]

# path: while loop many iterations (2+), inner for loop many iterations each pass, at least one swap in first pass, at least one swap in second pass, eventually no swaps and loop exits
def test_bubble_sort_multiple_passes():
    assert bubble_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# path: while loop many iterations (2+), inner for loop many iterations each pass, swaps occur in decreasing number of iterations per pass, eventually no swaps and loop exits
def test_bubble_sort_already_sorted():
    assert bubble_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# path: while loop many iterations (2+), inner for loop many iterations each pass, swaps occur only in first pass, second pass has no swaps and loop exits
def test_bubble_sort_one_swap_needed():
    assert bubble_sort([1, 3, 2, 4, 5]) == [1, 2, 3, 4, 5]