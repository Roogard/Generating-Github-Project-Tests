from python_programs.quicksort import quicksort

# path: root arr empty → if True → return []
def test_quicksort_empty():
    assert quicksort([]) == []

# path: root non-empty → lesser empty → greater empty (size 1)
def test_quicksort_single_element():
    assert quicksort([42]) == [42]

# path: root non-empty → lesser empty → greater non-empty
def test_quicksort_two_ascending():
    assert quicksort([1, 2]) == [1, 2]

# path: root non-empty → lesser non-empty → greater empty
def test_quicksort_two_descending():
    assert quicksort([2, 1]) == [1, 2]

# path: root non-empty → lesser non-empty → greater non-empty
def test_quicksort_three_elements_mixed():
    assert quicksort([2, 1, 3]) == [1, 2, 3]