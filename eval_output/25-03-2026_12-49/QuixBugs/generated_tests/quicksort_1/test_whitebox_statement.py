from python_programs.quicksort import quicksort

# covers: line 2 (if not arr True), line 3 (return [])
def test_quicksort_empty():
    assert quicksort([]) == []

# covers: line 2 (if not arr False), line 5 (pivot assignment),
#           line 6 (lesser recursion), line 7 (greater recursion),
#           line 8 (return concatenation)
def test_quicksort_mixed():
    arr = [3, 1, 4, 2]
    assert quicksort(arr) == [1, 2, 3, 4]