from python_programs.mergesort import mergesort
import types

# Extract inner merge function from mergesort's code object
merge_code = mergesort.__code__.co_consts[1]
merge = types.FunctionType(merge_code, {'__builtins__': __builtins__})

# covers: stmt 15 (len(arr)==0 True), stmt 16 (return arr)
def test_mergesort_empty():
    assert mergesort([]) == []

# covers: stmt 3 (result=[]), 4 (i=0), 5 (j=0), 6 (while False),
#         13 (extend with empty), 14 (return result)
def test_merge_both_empty():
    assert merge([], []) == []

# covers: stmt 6 (while True for two iterations),
#         stmt 7 (if True branch), 8 (append left[i]), 9 (i+=1),
#         stmt 13 (extend with right remainder), 14 (return result)
def test_merge_left_exhausted():
    assert merge([1, 2], [3, 4]) == [1, 2, 3, 4]

# covers: stmt 6 (while True for mixed comparisons),
#         stmt 7 (if branch), 8 (append left[i]), 9 (i+=1),
#         stmt 10 (else branch), 11 (append right[j]), 12 (j+=1),
#         stmt 13 (extend with whichever remains), 14 (return result)
def test_merge_mixed_order():
    assert merge([1, 4], [2, 3, 5]) == [1, 2, 3, 4, 5]