from python_programs.quicksort import quicksort

def test_quicksort_empty():
    # not arr: True
    assert quicksort([]) == []

def test_quicksort_non_empty():
    # not arr: False
    assert quicksort([3, 1, 2]) == [1, 2, 3]

def test_quicksort_single_element():
    # not arr: False
    assert quicksort([42]) == [42]

def test_quicksort_already_sorted():
    # not arr: False
    assert quicksort([1, 2, 3, 4]) == [1, 2, 3, 4]

def test_quicksort_with_negatives_and_duplicates():
    # not arr: False
    assert quicksort([0, -1, 5, -1, 3]) == [-1, -1, 0, 3, 5]  # note: duplicates of pivot are preserved in lesser/greater logic here