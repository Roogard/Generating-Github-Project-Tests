from python_programs.mergesort import mergesort

# len(arr)==0: True
def test_empty_list():
    assert mergesort([]) == []

# len(arr)==0: False; i<len(left): True; j<len(right): True; left[i]<=right[j]: False; left[i:]: True
def test_merge_left_greater():
    assert mergesort([3, 1, 2]) == [1, 2, 3]

# len(arr)==0: False; i<len(left): True; j<len(right): True; left[i]<=right[j]: True; left[i:]: False; right[j:]: True
def test_merge_left_less():
    assert mergesort([2, 1, 3]) == [1, 2, 3]