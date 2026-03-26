from python_programs.quicksort import quicksort

# covers: stmt 1 (True), stmt 2
def test_quicksort_empty():
    assert quicksort([]) == []

# covers: stmt 1 (False), stmt 3, stmt 4, stmt 5, stmt 6
def test_quicksort_single():
    assert quicksort([1]) == [1]