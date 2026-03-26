from python_programs.quicksort import quicksort

# catches missing base-case return (e.g., if not arr: fall through yielding None)
def test_empty_list():
    assert quicksort([]) == []

# catches base-case logic error for single-element lists (e.g., not handling len==1)
def test_single_element():
    assert quicksort([42]) == [42]

# catches off-by-one slicing error (e.g., arr[1:] mistakenly written as arr[2:])
def test_two_elements_unsorted():
    assert quicksort([2, 1]) == [1, 2]

# catches comparator-flip mutation (e.g., using '>' instead of '<' or vice versa in partitions)
def test_three_elements_mixed():
    data = [1, 0, 2]
    assert quicksort(data) == [0, 1, 2]

# catches incorrect handling of equal-to-pivot (e.g., using '<' for both partitions or losing duplicates)
def test_with_duplicates():
    data = [3, 1, 2, 3, 1]
    assert quicksort(data) == [1, 1, 2, 3, 3]