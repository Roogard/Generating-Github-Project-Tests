import pytest
from python_programs.quicksort import quicksort

# Valid equivalence classes

def test_quicksort_empty_list():
    assert quicksort([]) == []

def test_quicksort_single_element():
    assert quicksort([42]) == [42]

def test_quicksort_sorted_list():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

def test_quicksort_unsorted_list():
    assert quicksort([3, 1, 4, 2]) == [1, 2, 3, 4]

def test_quicksort_reverse_sorted_list():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

def test_quicksort_list_with_negatives_and_zero():
    assert quicksort([0, -1, 5, -3, 2]) == [-3, -1, 0, 2, 5]

def test_quicksort_list_of_strings():
    data = ["banana", "apple", "cherry"]
    assert quicksort(data) == ["apple", "banana", "cherry"]

def test_quicksort_list_with_duplicates():
    data = [2, 1, 2, 3, 1]
    assert quicksort(data) == [1, 1, 2, 2, 3]

# Invalid equivalence classes

def test_quicksort_none_input():
    with pytest.raises(TypeError):
        quicksort(None)

def test_quicksort_non_iterable_input():
    with pytest.raises(TypeError):
        quicksort(5)

def test_quicksort_uncomparable_elements():
    with pytest.raises(TypeError):
        quicksort([1, "a", 2])