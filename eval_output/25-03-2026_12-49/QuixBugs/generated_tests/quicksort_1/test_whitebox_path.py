import pytest
from python_programs.quicksort import quicksort

# path: arr empty → return []
def test_quicksort_empty():
    assert quicksort([]) == []

# path: non-empty → lesser=[], greater=[] → return [pivot]
def test_quicksort_single():
    assert quicksort([42]) == [42]

# path: non-empty → lesser non-empty, greater empty (sorted descending)
def test_quicksort_sorted_desc():
    assert quicksort([3, 2, 1]) == [1, 2, 3]

# path: non-empty → lesser empty, greater non-empty (sorted ascending)
def test_quicksort_sorted_asc():
    assert quicksort([1, 2, 3]) == [1, 2, 3]

# path: non-empty → lesser & greater both non-empty
def test_quicksort_mixed():
    assert quicksort([2, 1, 3]) == [1, 2, 3]

# path: duplicates equal pivot are dropped (elements == pivot excluded)
def test_quicksort_duplicates():
    assert quicksort([2, 1, 2, 3]) == [1, 2, 3]

# path: handles negative numbers and zeros
def test_quicksort_negatives():
    assert quicksort([0, -1, 1, -2]) == [-2, -1, 0, 1]

# Note: exhaustive recursion paths are numerous; these cover primary base and branch scenarios.