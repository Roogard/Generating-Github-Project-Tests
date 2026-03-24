from algorithms.dynamic_programming.buy_sell_stock import max_profit_optimized

# condition: cur_max + prices[i] - prices[i-1] > 0: True
def test_cur_max_positive():
    # Prices where price increase leads to positive cur_max
    # At i=1: cur_max = max(0, 0 + 5-1) = 4 > 0 → True
    # At i=2: cur_max = max(0, 4 + 3-5) = max(0,2) = 2 > 0 → True
    assert max_profit_optimized([1, 5, 3]) == 4

# condition: cur_max + prices[i] - prices[i-1] > 0: False
def test_cur_max_non_positive():
    # Prices where price change leads to cur_max + diff <= 0
    # At i=1: cur_max = max(0, 0 + 3-5) = 0 → False (equal to 0)
    # At i=2: cur_max = max(0, 0 + 1-3) = 0 → False
    assert max_profit_optimized([5, 3, 1]) == 0

# condition: cur_max + prices[i] - prices[i-1] > 0: True then False
def test_cur_max_positive_then_non_positive():
    # At i=1: cur_max = max(0, 0 + 5-1) = 4 > 0 → True
    # At i=2: cur_max = max(0, 4 + 1-5) = 0 → False
    assert max_profit_optimized([1, 5, 1]) == 4

# condition: max_so_far > cur_max: True
def test_max_so_far_greater_than_cur_max():
    # Sequence where max_so_far from earlier is greater than later cur_max
    # At i=1: cur_max=4, max_so_far=4
    # At i=2: cur_max=2, max_so_far=max(4,2)=4 → max_so_far > cur_max: True
    assert max_profit_optimized([1, 5, 3]) == 4

# condition: max_so_far > cur_max: False (equal case)
def test_max_so_far_equal_to_cur_max():
    # Sequence where cur_max equals max_so_far throughout
    # At i=1: cur_max=4, max_so_far=4 → max_so_far > cur_max: False
    # At i=2: cur_max=6, max_so_far=6 → False
    assert max_profit_optimized([1, 5, 7]) == 6

# condition: max_so_far > cur_max: False (cur_max greater)
def test_cur_max_greater_than_max_so_far():
    # Sequence where cur_max becomes greater than previous max_so_far
    # At i=1: cur_max=4, max_so_far=4
    # At i=2: cur_max=5, max_so_far=max(4,5)=5 → max_so_far > cur_max: False (equal)
    # Need a case where cur_max increases beyond previous max_so_far
    # At i=1: cur_max=2, max_so_far=2
    # At i=2: cur_max=5, max_so_far=max(2,5)=5 → max_so_far > cur_max: False (equal)
    # Actually, max_so_far is updated after cur_max, so they become equal.
    # To have cur_max > max_so_far before update, we need multiple increases.
    # At i=1: cur_max=2, max_so_far=2
    # At i=2: cur_max=4 (2 + 3-1), max_so_far=max(2,4)=4 → False (equal)
    # The condition max_so_far > cur_max is evaluated in max(max_so_far, cur_max).
    # The comparison is >=, not >. So False when cur_max >= max_so_far.
    # We'll test when cur_max > old max_so_far.
    assert max_profit_optimized([1, 3, 6]) == 5

# condition: len(prices) > 1: True (loop executes)
def test_multiple_prices():
    assert max_profit_optimized([7, 1, 5, 3, 6, 4]) == 5

# condition: len(prices) > 1: False (loop doesn't execute)
def test_single_price():
    assert max_profit_optimized([7]) == 0

# condition: prices[i] - prices[i-1] > -cur_max: True (leads to positive cur_max)
def test_price_increase_exceeds_negative_cur_max():
    # cur_max is negative, but price increase large enough to make sum positive
    # Start with prices that give negative cur_max, then large increase
    # [5,3,10]: 
    # i=1: cur_max = max(0, 0+3-5)=0
    # i=2: cur_max = max(0, 0+10-3)=7 > 0 → True
    assert max_profit_optimized([5, 3, 10]) == 7

# condition: prices[i] - prices[i-1] > -cur_max: False (leads to zero/negative cur_max)
def test_price_increase_does_not_exceed_negative_cur_max():
    # cur_max is negative, price increase not enough
    # [5,3,4]:
    # i=1: cur_max=0
    # i=2: cur_max = max(0, 0+4-3)=1 > 0 → Actually True
    # Need cur_max positive from previous, then drop
    # [1,5,3]:
    # i=1: cur_max=4
    # i=2: cur_max = max(0, 4+3-5)=2 > 0 → Still positive
    # To get False, need cur_max + diff <= 0
    # [1,5,1]:
    # i=1: cur_max=4
    # i=2: cur_max = max(0, 4+1-5)=0 → False
    assert max_profit_optimized([1, 5, 1]) == 4