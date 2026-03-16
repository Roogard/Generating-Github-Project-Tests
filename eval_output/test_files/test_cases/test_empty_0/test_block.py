from algorithms.backtracking import check_sum

# covers: entry block, if-true block (sum equals target)
def test_check_sum_true():
    result = check_sum([1, 2, 3], 6)
    assert result[0] is True
    assert result[1] == [1, 2, 3]

# covers: entry block, else block (sum not equal to target)
def test_check_sum_false():
    result = check_sum([1, 2, 3], 5)
    assert result[0] is False
    assert result[1] == [1, 2, 3]