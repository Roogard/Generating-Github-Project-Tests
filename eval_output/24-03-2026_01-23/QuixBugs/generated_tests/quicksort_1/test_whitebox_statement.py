from python_programs.quicksort import quicksort

# covers: stmt 1 (if not arr True), stmt 2 (return [])
def test_quicksort_empty():
    assert quicksort([]) == []

# covers: stmt 3 (pivot assignment), stmt 4 & 5 (list comprehensions for lesser/greater),
# recursive calls including base case, and stmt 6 (final return concatenation)
def test_quicksort_unordered():
    arr = [3, 1, 2, 5, 4]
    assert quicksort(arr) == [1, 2, 3, 4, 5]