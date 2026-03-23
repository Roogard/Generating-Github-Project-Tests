from algorithms.dynamic_programming.buy_sell_stock import max_profit_optimized

# condition: cur_max + prices[i] - prices[i-1] > 0: True
# condition: cur_max + prices[i] - prices[i-1] > 0: False
def test_profit_increasing_sequence():
    # Multiple iterations where cur_max + diff > 0 becomes True
    # First diff: 2-1=1, cur_max=max(0,0+1)=1 (>0 True)
    # Second diff: 3-2=1, cur_max=max(0,1+1)=2 (>0 True)
    assert max_profit_optimized([1, 2, 3]) == 2

# condition: cur_max + prices[i] - prices[i-1] > 0: False (first iteration)
# condition: cur_max + prices[i] - prices[i-1] > 0: True (later iteration)
def test_profit_decrease_then_increase():
    # First diff: 5-7=-2, cur_max=max(0,0-2)=0 (>0 False)
    # Second diff: 9-5=4, cur_max=max(0,0+4)=4 (>0 True)
    assert max_profit_optimized([7, 5, 9]) == 4

# condition: cur_max + prices[i] - prices[i-1] > 0: False (all iterations)
def test_no_profit():
    # All diffs negative or zero, cur_max stays 0 (>0 False always)
    assert max_profit_optimized([5, 4, 3, 2, 1]) == 0

# condition: max_so_far > cur_max: True
# condition: max_so_far > cur_max: False
def test_max_so_far_updates():
    # Sequence: 1, 3, 2, 5
    # i=1: diff=2, cur_max=2, max_so_far=max(0,2)=2 (max_so_far > cur_max? False, equal)
    # i=2: diff=-1, cur_max=max(0,2-1)=1, max_so_far=max(2,1)=2 (max_so_far > cur_max: True)
    # i=3: diff=3, cur_max=max(0,1+3)=4, max_so_far=max(2,4)=4 (max_so_far > cur_max: False, equal)
    assert max_profit_optimized([1, 3, 2, 5]) == 4

# Edge case: empty list (no loop, conditions not evaluated)
def test_empty_list():
    assert max_profit_optimized([]) == 0

# Edge case: single element (no loop, conditions not evaluated)
def test_single_price():
    assert max_profit_optimized([10]) == 0

# condition: cur_max + prices[i] - prices[i-1] > 0: True (exactly zero case)
# Actually zero is not >0, so this tests the boundary
def test_zero_price_change():
    # All diffs zero, cur_max stays 0 (>0 False)
    assert max_profit_optimized([5, 5, 5, 5]) == 0

# condition: cur_max + prices[i] - prices[i-1] > 0: True then False
def test_profit_reset_to_zero():
    # Prices: 2, 5, 1
    # i=1: diff=3, cur_max=3 (>0 True)
    # i=2: diff=-4, cur_max=max(0,3-4)=0 (>0 False)
    assert max_profit_optimized([2, 5, 1]) == 3