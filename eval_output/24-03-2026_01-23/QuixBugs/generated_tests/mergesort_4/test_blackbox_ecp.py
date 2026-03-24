import pytest
from python_programs.mergesort import mergesort

# Valid equivalence class: empty list
def test_empty_list():
    assert mergesort([]) == []

# Valid equivalence class: single-element list
def test_single_element_list():
    assert mergesort([42]) == [42]

# Valid equivalence class: unsorted list of integers
def test_unsorted_integer_list():
    assert mergesort([3, 1, 4, 5, 2]) == [1, 2, 3, 4, 5]

# Valid equivalence class: list with duplicate elements
def test_list_with_duplicates():
    assert mergesort([2, 3, 2, 1, 1]) == [1, 1, 2, 2, 3]

# Valid equivalence class: list mixing ints and floats
def test_list_with_ints_and_floats():
    assert mergesort([3.5, 2, 4.2, 2.0]) == [2, 2.0, 3.5, 4.2]

# Invalid equivalence class: input is None
def test_none_input_raises_type_error():
    with pytest.raises(TypeError):
        mergesort(None)

# Invalid equivalence class: input is non-iterable type
def test_non_iterable_input_raises_type_error():
    with pytest.raises(TypeError):
        mergesort(123)

# Invalid equivalence class: elements are not mutually comparable
def test_uncomparable_elements_raises_type_error():
    with pytest.raises(TypeError):
        mergesort([1, "two", 3])