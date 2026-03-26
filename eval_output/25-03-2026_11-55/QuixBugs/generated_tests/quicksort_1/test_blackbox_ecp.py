import pytest
from python_programs.quicksort import quicksort

def test_quicksort_empty_list():
    assert quicksort([]) == []

def test_quicksort_single_element_list():
    assert quicksort([42]) == [42]

def test_quicksort_already_sorted_list():
    data = [1, 2, 3, 4, 5]
    assert quicksort(data) == [1, 2, 3, 4, 5]

def test_quicksort_reverse_sorted_list():
    data = [5, 4, 3, 2, 1]
    assert quicksort(data) == [1, 2, 3, 4, 5]

def test_quicksort_unsorted_list():
    data = [3, 1, 4, 2]
    assert quicksort(data) == [1, 2, 3, 4]

def test_quicksort_list_with_duplicates():
    data = [3, 1, 2, 1, 3]
    # duplicates are lost except one occurrence of each value
    assert quicksort(data) == [1, 2, 3]

def test_quicksort_mixed_types_raises_typeerror():
    with pytest.raises(TypeError):
        quicksort([1, "a"])