import pytest
from algorithms.sorting.insertion_sort import insertion_sort

# path: for loop 0 iterations (empty array) -> return
def test_insertion_sort_empty():
    assert insertion_sort([]) == []

# path: for loop 1 iteration -> while condition False (pos == 0) -> return
def test_insertion_sort_single():
    assert insertion_sort([5]) == [5]

# path: for loop 2 iterations:
#   i=0: while False (pos == 0)
#   i=1: while condition True (pos>0 and array[pos-1] > cursor) -> execute body once -> while condition becomes False -> assign cursor
def test_insertion_sort_two_descending():
    assert insertion_sort([2, 1]) == [1, 2]

# path: for loop 2 iterations:
#   i=0: while False
#   i=1: while condition False (array[pos-1] <= cursor) -> skip while body
def test_insertion_sort_two_ascending():
    assert insertion_sort([1, 2]) == [1, 2]

# path: for loop many iterations -> while condition False for all i (already sorted)
def test_insertion_sort_already_sorted():
    assert insertion_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# path: for loop many iterations -> while condition True for multiple positions in at least one iteration (multiple shifts)
def test_insertion_sort_multiple_shifts():
    assert insertion_sort([5, 2, 4, 6, 1, 3]) == [1, 2, 3, 4, 5, 6]

# path: for loop many iterations -> while condition True exactly once in at least one iteration (single shift)
def test_insertion_sort_single_shift():
    assert insertion_sort([1, 3, 2, 4, 5]) == [1, 2, 3, 4, 5]

# path: for loop many iterations -> while condition True for all possible positions in at least one iteration (cursor smallest so far)
def test_insertion_sort_cursor_smallest():
    assert insertion_sort([4, 3, 2, 1]) == [1, 2, 3, 4]