from python_programs.quicksort import quicksort

def test_quicksort_empty():
    # path: if-arr-empty → True → return []
    assert quicksort([]) == []

def test_quicksort_single_element():
    # path: if-arr-empty → False → pivot → lesser([])→True→return → greater([])→True→return
    assert quicksort([42]) == [42]

def test_quicksort_two_ascending():
    # path: if-arr-empty → False → pivot=1 → lesser([])→True→return → greater([2])→False→pivot→[...] 
    assert quicksort([1, 2]) == [1, 2]

def test_quicksort_two_descending():
    # path: if-arr-empty → False → pivot=2 → lesser([1])→False→pivot→[...] → greater([])→True→return
    assert quicksort([2, 1]) == [1, 2]

def test_quicksort_duplicates():
    # path: if-arr-empty → False → pivot=1 → lesser & greater both [] → True → return pivot only
    assert quicksort([1, 1]) == [1]

def test_quicksort_multiple_elements():
    # path: if-arr-empty → False → pivot=3 → lesser([1,1]) & greater([4,5]) recursive mix of paths
    assert quicksort([3, 1, 4, 1, 5]) == [1, 1, 3, 4, 5]