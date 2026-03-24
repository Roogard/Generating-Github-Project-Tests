import pytest
from python_programs.mergesort import mergesort

def test_mergesort_empty_list():
    assert mergesort([]) == []

def test_mergesort_single_element():
    assert mergesort([42]) == [42]

def test_mergesort_two_elements_sorted():
    assert mergesort([1, 2]) == [1, 2]

def test_mergesort_two_elements_reversed():
    assert mergesort([2, 1]) == [1, 2]

def test_mergesort_duplicate_elements():
    assert mergesort([3, 3, 3]) == [3, 3, 3]

def test_mergesort_already_sorted_list():
    assert mergesort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

def test_mergesort_reverse_sorted_list():
    assert mergesort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

def test_mergesort_mixed_negative_and_positive():
    assert mergesort([-2, 0, 3, -1, 2]) == [-2, -1, 0, 2, 3]

def test_mergesort_even_length_list():
    assert mergesort([4, 1, 3, 2]) == [1, 2, 3, 4]

def test_mergesort_odd_length_list():
    assert mergesort([7, 3, 5, 1, 9]) == [1, 3, 5, 7, 9]

def test_mergesort_none_input_raises_type_error():
    with pytest.raises(TypeError):
        mergesort(None)