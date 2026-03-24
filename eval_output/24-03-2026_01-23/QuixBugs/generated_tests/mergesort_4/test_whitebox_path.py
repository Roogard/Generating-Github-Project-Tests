import pytest
from python_programs.mergesort import mergesort

# path: len(arr) == 0 → returns immediately
def test_mergesort_empty():
    assert mergesort([]) == []

# path: len(arr) != 0 → enters recursion → ultimately RecursionError due to missing len(arr)==1 base-case
def test_mergesort_single_recursion_error():
    with pytest.raises(RecursionError):
        mergesort([1])

# path: len(arr) != 0 on a two-element list → enters recursion → ultimately RecursionError
def test_mergesort_two_recursion_error():
    with pytest.raises(RecursionError):
        mergesort([2, 1])