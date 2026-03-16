from tests.test_backtracking import check_sum

# covers: lines 2-3 (if branch)
def test_check_sum_true():
    assert check_sum(None, [1, 2, 3], 6) == (True, [1, 2, 3])

# covers: lines 2, 4-5 (else branch)
def test_check_sum_false():
    assert check_sum(None, [1, 2, 3], 7) == (False, [1, 2, 3])