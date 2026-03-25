from python_programs.mergesort import mergesort

# covers: mergesort block 2 (len(arr)==0)
def test_empty():
    assert mergesort([]) == []

# covers: mergesort block 3 (else), merge blocks 4 (entry), 5 (while check false), 8 (extend right)
def test_single():
    assert mergesort([42]) == [42]

# covers: merge blocks 4 (entry), 5 (while check true), 6 (left[i] <= right[j] branch), 8 (extend right)
def test_two_sorted():
    assert mergesort([1, 2]) == [1, 2]

# covers: merge blocks 4 (entry), 5 (while check true), 7 (else branch), 8 (extend left)
def test_two_reverse():
    assert mergesort([2, 1]) == [1, 2]

# covers: mergesort block 3 (recursive else), merge blocks 4, 5 (multiple loop iterations), 6, 7, 8
def test_multiple():
    arr = [3, 5, 1, 4, 2]
    assert mergesort(arr) == [1, 2, 3, 4, 5]

# covers: merge block 6 (left[i] <= right[j] on equal elements)
def test_duplicates():
    assert mergesort([2, 3, 2, 1]) == [1, 2, 2, 3]