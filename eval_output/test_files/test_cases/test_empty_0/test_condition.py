from algorithms.backtracking import check_sum

# condition: sum(nums) == target: True
def test_check_sum_true():
    assert check_sum([1, 2, 3], 6) == (True, [1, 2, 3])

# condition: sum(nums) == target: False
def test_check_sum_false():
    assert check_sum([1, 2, 3], 7) == (False, [1, 2, 3])