import pytest
from python_programs.quicksort import quicksort

def test_quicksort_empty_list():
    assert quicksort([]) == []

def test_quicksort_unsorted_list_of_integers():
    assert quicksort([3, 1, 4, 2]) == [1, 2, 3, 4]

def test_quicksort_list_with_duplicate_integers():
    assert quicksort([3, 1, 2, 3, 2, 1]) == [1, 2, 3]

def test_quicksort_input_tuple_of_integers():
    assert quicksort((4, 2, 3, 1)) == [1, 2, 3, 4]

def test_quicksort_non_iterable_input_type_error():
    with pytest.raises(TypeError):
        quicksort(None)

def test_quicksort_incomparable_types_type_error():
    with pytest.raises(TypeError):
        quicksort([1, "2", 3])