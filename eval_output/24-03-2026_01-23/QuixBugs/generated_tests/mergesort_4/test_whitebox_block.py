from python_programs.mergesort import mergesort

# covers: block 7 (len(arr)==0)
def test_empty_list():
    assert mergesort([]) == []

# covers: block 8 (else branch), block 1 (merge entry), block 2 (while), block 4 (else branch of if), block 5 (residual left), block 6 (return)
def test_two_element_reverse():
    assert mergesort([2, 1]) == [1, 2]

# covers: block 8 (else branch), block 1 (merge entry), block 2 (while), block 3 (if branch of if), block 4 (else branch of if), block 5 (residual right), block 6 (return)
def test_even_length_mixed():
    assert mergesort([1, 3, 2, 4]) == [1, 2, 3, 4]