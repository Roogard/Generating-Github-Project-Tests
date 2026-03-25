import pytest
from python_programs.mergesort import mergesort

# path: len(arr) == 0 → return arr
def test_mergesort_empty():
    assert mergesort([]) == []

# path: len(arr) != 0 → enters else → infinite recursion → raises RecursionError
def test_mergesort_non_empty_recursion():
    with pytest.raises(RecursionError):
        mergesort([3, 1, 2])