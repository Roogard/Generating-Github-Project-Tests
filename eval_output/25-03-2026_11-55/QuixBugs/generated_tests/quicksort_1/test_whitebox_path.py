from python_programs.quicksort import quicksort

# path: if not arr True
def test_quicksort_empty():
    assert quicksort([]) == []

# path: if not arr False → lesser(empty) → greater(empty)
def test_quicksort_single():
    assert quicksort([42]) == [42]

# path: if not arr False → lesser(empty) → greater(non-empty → both recursive branches empty)
def test_quicksort_two_ascending():
    assert quicksort([1, 2]) == [1, 2]

# path: if not arr False → lesser(non-empty → both recursive branches empty) → greater(empty)
def test_quicksort_two_descending():
    assert quicksort([2, 1]) == [1, 2]

# path: if not arr False → lesser(non-empty) → greater(non-empty)
def test_quicksort_multiple():
    assert quicksort([3, 1, 4, 2, 5]) == [1, 2, 3, 4, 5]