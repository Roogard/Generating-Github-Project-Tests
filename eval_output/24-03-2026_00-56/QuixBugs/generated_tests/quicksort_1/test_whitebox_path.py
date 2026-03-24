import pytest
from correct_python_programs.quicksort import quicksort

# path: empty list -> return []
def test_quicksort_empty():
    assert quicksort([]) == []

# path: non-empty list -> recursion base case (single element)
# For single element: arr[0] exists, arr[1:] is empty, both recursive calls hit empty case
def test_quicksort_single():
    assert quicksort([5]) == [5]

# path: non-empty list -> recursion with two elements where pivot is smaller
# arr = [1,2]: pivot=1, lesser=quicksort([])=[], greater=quicksort([2])=[2]
def test_quicksort_two_ascending():
    assert quicksort([1, 2]) == [1, 2]

# path: non-empty list -> recursion with two elements where pivot is larger
# arr = [2,1]: pivot=2, lesser=quicksort([1])=[1], greater=quicksort([])=[]
def test_quicksort_two_descending():
    assert quicksort([2, 1]) == [1, 2]

# path: non-empty list -> recursion with three elements, pivot splits into non-empty lesser and greater
def test_quicksort_three_mixed():
    assert quicksort([3, 1, 2]) == [1, 2, 3]

# path: non-empty list -> recursion where all elements go to greater (duplicates)
def test_quicksort_all_duplicates():
    assert quicksort([4, 4, 4]) == [4, 4, 4]

# path: non-empty list -> recursion where all elements go to lesser
def test_quicksort_all_less():
    assert quicksort([5, 1, 2, 3, 4]) == [1, 2, 3, 4, 5]

# path: non-empty list -> recursion where all elements go to greater
def test_quicksort_all_greater():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# path: non-empty list -> recursion with multiple levels of recursion (larger case)
def test_quicksort_larger_mixed():
    assert quicksort([10, 80, 30, 90, 40, 50, 70]) == [10, 30, 40, 50, 70, 80, 90]