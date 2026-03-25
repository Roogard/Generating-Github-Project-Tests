from python_programs.quicksort import quicksort

# covers: block1 (empty array branch)
def test_quicksort_empty():
    assert quicksort([]) == []

# covers: block2 (pivot assignment), block3 (lesser recursion), block4 (greater recursion), block5 (return concatenation), and recursive block1
def test_quicksort_single():
    assert quicksort([42]) == [42]

# covers: block2, block3, block4, block5 in a typical multi-element case
def test_quicksort_multiple():
    data = [3, 1, 2]
    assert quicksort(data) == [1, 2, 3]