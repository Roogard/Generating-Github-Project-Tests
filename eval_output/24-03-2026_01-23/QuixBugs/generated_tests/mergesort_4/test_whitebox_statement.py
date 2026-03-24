from python_programs.mergesort import mergesort

# covers: stmt1 (len(arr)==0 True), stmt2 (return arr)
def test_mergesort_empty():
    assert mergesort([]) == []

# covers: stmt1 False, stmt3 (else), stmt4 (middle calculation), stmt5 & stmt6 (recursive calls),
# merge: stmt merge1–merge3, merge4 True, merge5 True, merge6–merge7 (left branch), merge10 (extend right tail), merge11
def test_mergesort_sorted_two():
    assert mergesort([1, 2]) == [1, 2]

# covers: stmt1 False, stmt3, stmt4, stmt5 & stmt6,
# merge: stmt merge1–merge3, merge4 True, merge5 False, merge8–merge9 (right branch), merge10 (extend left tail), merge11
def test_mergesort_reverse_two():
    assert mergesort([2, 1]) == [1, 2]