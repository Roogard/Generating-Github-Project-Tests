import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from correct_python_programs.quicksort import quicksort

# Block mapping for quicksort:
# block 1: if not arr: return [] (entry, condition check, and return)
# block 2: pivot = arr[0]; lesser = ...; greater = ...; return lesser + [pivot] + greater (main body)

# covers: block 1 (empty array)
def test_quicksort_empty():
    assert quicksort([]) == []

# covers: block 2 (single element, recursion stops at block 1 in deeper calls)
def test_quicksort_single():
    assert quicksort([5]) == [5]

# covers: block 2 (multiple elements, recursion covers both lesser and greater branches)
def test_quicksort_multiple_sorted():
    assert quicksort([1, 2, 3]) == [1, 2, 3]

# covers: block 2 (multiple elements unsorted, recursion covers both lesser and greater branches)
def test_quicksort_multiple_unsorted():
    assert quicksort([3, 1, 2]) == [1, 2, 3]

# covers: block 2 (with duplicates, ensures x >= pivot branch is taken)
def test_quicksort_with_duplicates():
    assert quicksort([3, 1, 2, 1, 3]) == [1, 1, 2, 3, 3]