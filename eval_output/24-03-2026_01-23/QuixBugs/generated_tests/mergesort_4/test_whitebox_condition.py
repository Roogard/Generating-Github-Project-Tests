from python_programs.mergesort import mergesort

# len(arr)==0: True
def test_mergesort_empty():
    assert mergesort([]) == []  # len(arr)==0: True

# len(arr)==0: False; left[i]<=right[j]: True; i<len(left): True then False; j<len(right): True
def test_mergesort_sorted_simple():
    assert mergesort([1, 2, 3]) == [1, 2, 3]  # len(arr)==0: False; left[i]<=right[j]: True; i<len(left): True/False; j<len(right): True

# len(arr)==0: False; left[i]<=right[j]: False; i<len(left): True; j<len(right): True
def test_mergesort_reverse_pair():
    assert mergesort([3, 2]) == [2, 3]  # len(arr)==0: False; left[i]<=right[j]: False; i<len(left): True; j<len(right): True

# len(arr)==0: False; left[i]<=right[j]: False; i<len(left): True; j<len(right): False
def test_mergesort_right_exhausted():
    # left=[5,6], right=[1,2] during merge => right elements always smaller so j reaches len(right)
    assert mergesort([5, 6, 1, 2]) == [1, 2, 5, 6]  # len(arr)==0: False; left[i]<=right[j]: False; i<len(left): True; j<len(right): False