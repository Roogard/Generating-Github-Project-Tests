from algorithms.sorting.insertion_sort import insertion_sort

# covers: for loop init, cursor = array[i], pos = i, while condition (False), array[pos] = cursor, return array
def test_insertion_sort_single_element():
    assert insertion_sort([5]) == [5]

# covers: for loop iterating, cursor = array[i], pos = i, while condition (True), array[pos] = array[pos - 1], pos -= 1, array[pos] = cursor, return array
def test_insertion_sort_multiple_elements():
    assert insertion_sort([3, 1, 2]) == [1, 2, 3]

# covers: for loop iterating, cursor = array[i], pos = i, while condition (False) because array[pos - 1] <= cursor, array[pos] = cursor, return array
def test_insertion_sort_already_sorted():
    assert insertion_sort([1, 2, 3]) == [1, 2, 3]

# covers: for loop iterating, cursor = array[i], pos = i, while condition (True) for multiple iterations, array[pos] = array[pos - 1], pos -= 1, array[pos] = cursor, return array
def test_insertion_sort_reverse_sorted():
    assert insertion_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]