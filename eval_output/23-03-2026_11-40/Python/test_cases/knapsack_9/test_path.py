import pytest
from dynamic_programming.knapsack import _construct_solution

# Path enumeration:
# Branch 1: i > 0 and j > 0? (True/False)
# Branch 2 (if first branch True): dp[i-1][j] == dp[i][j]? (True/False)
# Recursive calls create additional paths, but each call is a new stack frame with same logic.
# We'll test base case (no recursion) and one recursive level for each branch.

# path: i <= 0 → function returns immediately (no recursion)
def test_construct_solution_i_zero():
    dp = [[0]]
    wt = []
    optimal_set = set()
    _construct_solution(dp, wt, 0, 1, optimal_set)
    assert optimal_set == set()

# path: j <= 0 → function returns immediately (no recursion)
def test_construct_solution_j_zero():
    dp = [[0], [0]]
    wt = [5]
    optimal_set = set()
    _construct_solution(dp, wt, 1, 0, optimal_set)
    assert optimal_set == set()

# path: i>0 and j>0 → dp[i-1][j] == dp[i][j] True → recursive call with i-1, j
def test_construct_solution_equal_dp():
    dp = [
        [0, 0, 0],
        [0, 2, 2],
        [0, 2, 4]
    ]
    wt = [1, 2]
    optimal_set = set()
    _construct_solution(dp, wt, 2, 2, optimal_set)
    # item 2 not added because dp[1][2] == dp[2][2]? No, 2 != 4, so this test is wrong.
    # Let's adjust: need dp[i-1][j] == dp[i][j]
    dp = [
        [0, 0, 0],
        [0, 2, 2],
        [0, 2, 2]
    ]
    optimal_set = set()
    _construct_solution(dp, wt, 2, 2, optimal_set)
    # Should recurse to (1,2) and then maybe further. At (1,2), dp[0][2] == dp[1][2]? 0 == 2? False.
    # So we need a deeper chain. Let's create a simple case where equality holds all the way.
    dp = [
        [0, 0, 0],
        [0, 2, 2],
        [0, 2, 2],
        [0, 2, 2]
    ]
    wt = [1, 2, 1]
    optimal_set = set()
    _construct_solution(dp, wt, 3, 2, optimal_set)
    # dp[2][2] == dp[3][2] (both 2) → recurse to (2,2)
    # dp[1][2] == dp[2][2] (both 2) → recurse to (1,2)
    # dp[0][2] == dp[1][2]? 0 == 2? False → else branch, add item 1? Wait, i=1, so add i=1? Actually in else branch optimal_set.add(i). i=1, wt[i-1]=wt[0]=1, recurse (0,1).
    # Then i=0 → base case.
    # So optimal_set should contain {1}.
    assert optimal_set == {1}

# path: i>0 and j>0 → dp[i-1][j] != dp[i][j] → add i, recurse with i-1, j-wt[i-1]
def test_construct_solution_unequal_dp():
    dp = [
        [0, 0, 0, 0],
        [0, 3, 3, 3],
        [0, 3, 7, 10]
    ]
    wt = [3, 4]
    optimal_set = set()
    _construct_solution(dp, wt, 2, 3, optimal_set)
    # dp[1][3] = 3, dp[2][3] = 10 → not equal → add i=2, recurse (1, 3-wt[1]) = (1, -1)
    # (1, -1): j=-1 <=0 → base case.
    assert optimal_set == {2}

# path: i>0 and j>0 → dp[i-1][j] != dp[i][j] → add i, recurse with i-1, j-wt[i-1] where j-wt[i-1] >0, leading to further recursion
def test_construct_solution_unequal_dp_deep_recursion():
    dp = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1],
        [0, 1, 6, 7, 7],
        [0, 1, 6, 7, 10]
    ]
    wt = [1, 5, 3]
    optimal_set = set()
    _construct_solution(dp, wt, 3, 4, optimal_set)
    # dp[2][4] = 7, dp[3][4] = 10 → not equal → add i=3, recurse (2, 4-wt[2]) = (2, 1)
    # At (2,1): dp[1][1] = 1, dp[2][1] = 1 → equal → recurse (1,1)
    # At (1,1): dp[0][1] = 0, dp[1][1] = 1 → not equal → add i=1, recurse (0, 1-wt[0]) = (0,0)
    # (0,0): base case.
    # optimal_set should contain {3, 1}
    assert optimal_set == {3, 1}

# path: i>0 and j>0 → dp[i-1][j] == dp[i][j] → recurse, then in recursion hit else branch
def test_construct_solution_mixed_paths():
    dp = [
        [0, 0, 0, 0],
        [0, 2, 2, 2],
        [0, 2, 4, 6],
        [0, 2, 4, 6]
    ]
    wt = [2, 2, 2]
    optimal_set = set()
    _construct_solution(dp, wt, 3, 3, optimal_set)
    # dp[2][3] = 6, dp[3][3] = 6 → equal → recurse (2,3)
    # dp[1][3] = 2, dp[2][3] = 6 → not equal → add i=2, recurse (1, 3-wt[1]) = (1,1)
    # dp[0][1] = 0, dp[1][1] = 2 → not equal → add i=1, recurse (0, -1)
    # base case.
    assert optimal_set == {2, 1}