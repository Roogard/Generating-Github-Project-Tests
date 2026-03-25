import pytest
from python_programs.mergesort import mergesort

def test_mergesort_empty_list():
    assert mergesort([]) == []

def test_mergesort_single_element():
    assert mergesort([1]) == [1]

def test_mergesort_sorted_list():
    assert mergesort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

def test_mergesort_reverse_sorted_list():
    assert mergesort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

def test_mergesort_with_duplicates():
    assert mergesort([3, 1, 2, 3, 1]) == [1, 1, 2, 3, 3]

def test_mergesort_negative_numbers():
    assert mergesort([-2, -5, 0, 3]) == [-5, -2, 0, 3]

def test_mergesort_floats_and_ints():
    assert mergesort([3.5, 2, 4.1, 2.0]) == [2, 2.0, 3.5, 4.1]

def test_mergesort_strings():
    assert mergesort(["banana", "apple", "cherry"]) == ["apple", "banana", "cherry"]

def test_mergesort_non_list_input_raises_type_error():
    with pytest.raises(TypeError):
        mergesort(None)

def test_mergesort_uncomparable_elements_raises_type_error():
    with pytest.raises(TypeError):
        mergesort([1, "a", 2])