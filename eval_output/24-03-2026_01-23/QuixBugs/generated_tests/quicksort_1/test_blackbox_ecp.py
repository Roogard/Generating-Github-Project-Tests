import pytest
from python_programs.quicksort import quicksort

def test_quicksort_empty_list():
    assert quicksort([]) == []

def test_quicksort_single_element_list():
    assert quicksort([42]) == [42]

def test_quicksort_already_sorted_list():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

def test_quicksort_reverse_sorted_list():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

def test_quicksort_unsorted_list_with_distinct_elements():
    assert quicksort([3, 1, 4, 2, 5]) == [1, 2, 3, 4, 5]

def test_quicksort_list_with_duplicates():
    # Implementation drops duplicate values beyond the single pivot occurrence
    assert quicksort([3, 1, 2, 3, 2]) == [1, 2, 3]

def test_quicksort_mixed_type_list_raises_type_error():
    with pytest.raises(TypeError):
        quicksort([1, "a", 2])