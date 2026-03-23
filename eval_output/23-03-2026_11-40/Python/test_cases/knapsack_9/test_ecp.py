import pytest
from dynamic_programming.knapsack import _construct_solution

# Valid equivalence class: dp table with multiple items, i and j within bounds, item i is included
def test_construct_solution_item_included():
    dp = [
        [0, 0, 0, 0],
        [0, 1, 1, 1],
        [0, 1, 2, 2]
    ]
    wt = [1, 2]
    optimal_set = set()
    _construct_solution(dp, wt, i=2, j=3, optimal_set=optimal_set)
    # The function adds index 2, then recursively adds index 1 because dp[0][1] != dp[1][1] (0 != 1)
    # So the optimal set should be {1, 2}
    assert optimal_set == {1, 2}

# Valid equivalence class: dp table with multiple items, i and j within bounds, item i is not included
def test_construct_solution_item_not_included():
    dp = [
        [0, 0, 0, 0],
        [0, 1, 1, 1],
        [0, 1, 1, 1]
    ]
    wt = [1, 2]
    optimal_set = set()
    _construct_solution(dp, wt, i=2, j=3, optimal_set=optimal_set)
    # dp[1][3] == dp[2][3] (1 == 1) so item 2 not included, then check i=1, j=3.
    # dp[0][3] == dp[1][3] (0 == 1) is false, so item 1 is included.
    # Then recursively check i=0, j=2 (3 - wt[0]=3-1=2). i=0 stops recursion.
    # So optimal set should be {1}
    assert optimal_set == {1}

# Valid equivalence class: i = 0 (base case, recursion stops)
def test_construct_solution_i_zero():
    dp = [[0, 0, 0]]
    wt = []
    optimal_set = set()
    _construct_solution(dp, wt, i=0, j=2, optimal_set=optimal_set)
    assert optimal_set == set()

# Valid equivalence class: j = 0 (base case, recursion stops)
def test_construct_solution_j_zero():
    dp = [
        [0],
        [0],
        [0]
    ]
    wt = [1, 2]
    optimal_set = set()
    _construct_solution(dp, wt, i=2, j=0, optimal_set=optimal_set)
    assert optimal_set == set()

# Valid equivalence class: i > 0, j > 0, dp[i-1][j] == dp[i][j] (item not included)
def test_construct_solution_equal_dp_values():
    dp = [
        [0, 0, 0],
        [0, 1, 1],
        [0, 1, 1]
    ]
    wt = [1, 1]
    optimal_set = set()
    _construct_solution(dp, wt, i=2, j=2, optimal_set=optimal_set)
    # dp[1][2] == dp[2][2] (1 == 1) so item 2 not included, then check i=1, j=2.
    # dp[0][2] == dp[1][2] (0 == 1) is false, so item 1 is included.
    # Then recursively check i=0, j=1 (2 - wt[0]=2-1=1). i=0 stops.
    # So optimal set should be {1}
    assert optimal_set == {1}

# Valid equivalence class: i > 0, j > 0, dp[i-1][j] != dp[i][j] (item included)
def test_construct_solution_unequal_dp_values():
    dp = [
        [0, 0, 0],
        [0, 1, 1],
        [0, 1, 2]
    ]
    wt = [1, 1]
    optimal_set = set()
    _construct_solution(dp, wt, i=2, j=2, optimal_set=optimal_set)
    # dp[1][2] != dp[2][2] (1 != 2) so item 2 is included.
    # Then recursively check i=1, j=1 (2 - wt[1]=2-1=1).
    # dp[0][1] == dp[1][1] (0 == 1) is false, so item 1 is included.
    # Then recursively check i=0, j=0 (1 - wt[0]=1-1=0). i=0 stops.
    # So optimal set should be {1, 2}
    assert optimal_set == {1, 2}

# Valid equivalence class: optimal_set is pre-populated, function adds to it
def test_construct_solution_prepopulated_set():
    dp = [
        [0, 0, 0],
        [0, 1, 1],
        [0, 1, 2]
    ]
    wt = [1, 1]
    optimal_set = {3}
    _construct_solution(dp, wt, i=2, j=2, optimal_set=optimal_set)
    # Same reasoning as previous test: items 1 and 2 are added.
    assert optimal_set == {1, 2, 3}

# Valid equivalence class: wt list with zero weight item
def test_construct_solution_zero_weight_item():
    dp = [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ]
    wt = [0, 0]
    optimal_set = set()
    _construct_solution(dp, wt, i=2, j=2, optimal_set=optimal_set)
    # dp[1][2] == dp[2][2] (0 == 0) so item 2 not included, then check i=1, j=2.
    # dp[0][2] == dp[1][2] (0 == 0) so item 1 not included, then check i=0, j=2 stops.
    assert optimal_set == set()

# Valid equivalence class: single item, i=1, j>=wt[0], item included
def test_construct_solution_single_item_included():
    dp = [
        [0, 0, 0],
        [0, 1, 1]
    ]
    wt = [1]
    optimal_set = set()
    _construct_solution(dp, wt, i=1, j=2, optimal_set=optimal_set)
    # dp[0][2] != dp[1][2] (0 != 1) so item 1 is included.
    # Then recursively check i=0, j=1 (2 - wt[0]=2-1=1). i=0 stops.
    assert optimal_set == {1}

# Valid equivalence class: single item, i=1, j>=wt[0], item not included (dp equal)
def test_construct_solution_single_item_not_included():
    dp = [
        [0, 0, 0],
        [0, 0, 0]
    ]
    wt = [1]
    optimal_set = set()
    _construct_solution(dp, wt, i=1, j=2, optimal_set=optimal_set)
    # dp[0][2] == dp[1][2] (0 == 0) so item 1 not included, then i=0 stops.
    assert optimal_set == set()