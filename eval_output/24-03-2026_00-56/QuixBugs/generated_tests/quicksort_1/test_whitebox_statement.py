from correct_python_programs.quicksort import quicksort

# covers: if not arr: (True), return []
def test_quicksort_empty():
    assert quicksort([]) == []

# covers: if not arr: (False), pivot = arr[0], lesser = ..., greater = ..., return lesser + [pivot] + greater
# also covers recursive calls for lesser and greater branches
def test_quicksort_sorted():
    assert quicksort([1, 2, 3]) == [1, 2, 3]

# covers: if not arr: (False), pivot = arr[0], lesser = ..., greater = ..., return lesser + [pivot] + greater
# also covers recursive calls where elements are partitioned
def test_quicksort_reverse():
    assert quicksort([3, 2, 1]) == [1, 2, 3]

# covers: if not arr: (False), pivot = arr[0], lesser = ..., greater = ..., return lesser + [pivot] + greater
# also covers recursive calls with duplicates (x >= pivot branch)
def test_quicksort_duplicates():
    assert quicksort([3, 1, 2, 1, 3]) == [1, 1, 2, 3, 3]