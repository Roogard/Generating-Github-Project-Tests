from python_programs.quicksort import quicksort

# covers: if not arr True, return [] (empty input)
def test_quicksort_empty():
    assert quicksort([]) == []

# covers: if not arr False, pivot assignment, recursive calls on empty lists, return [pivot]
def test_quicksort_single():
    assert quicksort([5]) == [5]

# covers: pivot assignment, list comprehensions filtering into lesser and greater, recursive sorting
def test_quicksort_mixed():
    arr = [3, 1, 4, 2]
    assert quicksort(arr) == [1, 2, 3, 4]