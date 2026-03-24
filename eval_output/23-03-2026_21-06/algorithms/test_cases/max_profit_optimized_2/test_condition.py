from algorithms.dynamic_programming.buy_sell_stock import max_profit_optimized

# condition: cur_max + prices[i] - prices[i-1] > 0: True
# condition: cur_max + prices[i] - prices[i-1] > 0: False
def test_profit_increase_positive_difference():
    # cur_max + prices[i] - prices[i-1] > 0 becomes True, cur_max becomes positive
    # cur_max + prices[i] - prices[i-1] > 0 becomes False, cur_max becomes 0
    # This test includes both True and False across iterations
    # Iteration 1 (i=1): cur_max + (5-1)=4 > 0 → True, cur_max=4
    # Iteration 2 (i=2): cur_max + (3-5)=2 > 0 → True, cur_max=2
    # Iteration 3 (i=3): cur_max + (6-3)=5 > 0 → True, cur_max=5
    # Iteration 4 (i=4): cur_max + (4-6)=3 > 0 → True, cur_max=3
    assert max_profit_optimized([1, 5, 3, 6, 4]) == 5

# condition: cur_max + prices[i] - prices[i-1] > 0: False (all iterations)
def test_no_profit_decreasing_prices():
    # All differences negative, cur_max + prices[i] - prices[i-1] <= 0 → False
    # cur_max becomes 0 each iteration
    assert max_profit_optimized([7, 6, 4, 3, 1]) == 0

# condition: cur_max + prices[i] - prices[i-1] > 0: True then False
def test_profit_then_loss():
    # Iteration 1 (i=1): cur_max + (5-2)=3 > 0 → True, cur_max=3
    # Iteration 2 (i=2): cur_max + (1-5)=-1 > 0 → False, cur_max=0
    # Iteration 3 (i=3): cur_max + (4-1)=3 > 0 → True, cur_max=3
    assert max_profit_optimized([2, 5, 1, 4]) == 3

# condition: cur_max + prices[i] - prices[i-1] > 0: False then True
def test_loss_then_profit():
    # Iteration 1 (i=1): cur_max + (3-5)=-2 > 0 → False, cur_max=0
    # Iteration 2 (i=2): cur_max + (8-3)=5 > 0 → True, cur_max=5
    assert max_profit_optimized([5, 3, 8]) == 5

# condition: cur_max + prices[i] - prices[i-1] > 0: True (single iteration)
def test_single_profit_pair():
    # Only one iteration: cur_max + (6-1)=5 > 0 → True, cur_max=5
    assert max_profit_optimized([1, 6]) == 5

# condition: cur_max + prices[i] - prices[i-1] > 0: False (single iteration)
def test_single_loss_pair():
    # Only one iteration: cur_max + (1-6)=-5 > 0 → False, cur_max=0
    assert max_profit_optimized([6, 1]) == 0

# Edge case: empty or single price list (no iterations, no conditions evaluated)
def test_empty_list():
    # No loop iterations, no conditions
    assert max_profit_optimized([]) == 0

def test_single_price():
    # No loop iterations, no conditions
    assert max_profit_optimized([5]) == 0