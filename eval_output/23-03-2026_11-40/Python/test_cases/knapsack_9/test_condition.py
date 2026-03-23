from dynamic_programming.knapsack import _construct_solution

# condition: i>0: True, j>0: True, dp[i-1][j] == dp[i][j]: True
def test_construct_solution_i_gt_0_j_gt_0_dp_equal():
    dp = [[0, 0], [0, 0]]
    wt = [1]
    optimal_set = set()
    _construct_solution(dp, wt, 1, 1, optimal_set)
    assert optimal_set == set()

# condition: i>0: True, j>0: True, dp[i-1][j] == dp[i][j]: False
def test_construct_solution_i_gt_0_j_gt_0_dp_not_equal():
    dp = [[0, 0], [0, 1]]
    wt = [1]
    optimal_set = set()
    _construct_solution(dp, wt, 1, 1, optimal_set)
    assert optimal_set == {1}

# condition: i>0: True, j>0: False
def test_construct_solution_i_gt_0_j_le_0():
    dp = [[0], [0]]
    wt = [1]
    optimal_set = set()
    _construct_solution(dp, wt, 1, 0, optimal_set)
    assert optimal_set == set()

# condition: i>0: False, j>0: True
def test_construct_solution_i_le_0_j_gt_0():
    dp = [[0, 0]]
    wt = []
    optimal_set = set()
    _construct_solution(dp, wt, 0, 1, optimal_set)
    assert optimal_set == set()

# condition: i>0: False, j>0: False
def test_construct_solution_i_le_0_j_le_0():
    dp = [[0]]
    wt = []
    optimal_set = set()
    _construct_solution(dp, wt, 0, 0, optimal_set)
    assert optimal_set == set()