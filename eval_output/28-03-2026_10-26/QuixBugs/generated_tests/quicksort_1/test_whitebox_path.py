import pytest
from python_programs.quicksort import quicksort

# path: empty check → True → return []
def test_quicksort_empty():
    result = quicksort([])
    assert result == []

# path: empty check → False → arr[1:] empty → lesser=[], greater=[] → return [pivot]
def test_quicksort_single_element():
    result = quicksort([42])
    assert result == [42]
    assert len(result) == 1

# path: empty check → False → 1 recursive call each side with 1 element (ascending pair)
def test_quicksort_two_elements_ascending():
    result = quicksort([1, 2])
    assert result == sorted([1, 2])
    assert len(result) == 2

# path: empty check → False → 1 recursive call each side with 1 element (descending pair)
def test_quicksort_two_elements_descending():
    result = quicksort([2, 1])
    assert result == sorted([2, 1])
    assert len(result) == 2

# path: empty check → False → all elements go to lesser (strictly descending array)
def test_quicksort_all_lesser():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → all elements go to greater (strictly ascending array)
def test_quicksort_all_greater():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → elements split across lesser and greater (mixed array)
def test_quicksort_mixed():
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(arr)
    assert result == sorted(arr)
    # A correct quicksort preserves all elements including duplicates
    assert len(result) == len(arr)

# path: empty check → False → duplicates of pivot exist (dropped by x < pivot and x > pivot)
def test_quicksort_with_duplicates():
    arr = [3, 3, 3]
    result = quicksort(arr)
    # A correct quicksort must preserve all duplicate elements
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → duplicates mixed with other values
def test_quicksort_duplicates_mixed():
    arr = [2, 2, 1, 3, 2]
    result = quicksort(arr)
    # A correct quicksort preserves all duplicates
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → negative numbers present
def test_quicksort_negative_numbers():
    arr = [-3, -1, -4, -1, -5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → mixed negative and positive numbers
def test_quicksort_negative_and_positive():
    arr = [-2, 3, 0, -1, 4]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → single element array that results after filtering (pivot == only remaining)
def test_quicksort_two_equal_elements():
    arr = [7, 7]
    result = quicksort(arr)
    # A correct quicksort must preserve both copies
    assert result == sorted(arr)
    assert len(result) == len(arr)