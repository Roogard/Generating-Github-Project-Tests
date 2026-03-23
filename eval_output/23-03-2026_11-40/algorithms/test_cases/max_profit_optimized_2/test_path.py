import pytest
from algorithms.dynamic_programming.buy_sell_stock import max_profit_optimized

# path: loop 0 iterations (len(prices) <= 1) → return max_so_far (0)
def test_max_profit_optimized_empty():
    assert max_profit_optimized([]) == 0

# path: loop 0 iterations (len(prices) <= 1) → return max_so_far (0)
def test_max_profit_optimized_single():
    assert max_profit_optimized([5]) == 0

# path: loop 1 iteration → cur_max = 0 (since price diff <= 0) → max_so_far remains 0 → return 0
def test_max_profit_optimized_two_descending():
    assert max_profit_optimized([5, 3]) == 0

# path: loop 1 iteration → cur_max > 0 (price diff > 0) → max_so_far updated → return profit
def test_max_profit_optimized_two_ascending():
    assert max_profit_optimized([3, 5]) == 2

# path: loop many iterations → cur_max always 0 (never positive cumulative diff) → max_so_far remains 0 → return 0
def test_max_profit_optimized_all_descending():
    assert max_profit_optimized([7, 6, 4, 3, 1]) == 0

# path: loop many iterations → cur_max becomes positive, stays positive, updates max_so_far once → return that profit
def test_max_profit_optimized_single_peak():
    assert max_profit_optimized([7, 1, 5, 3, 6, 4]) == 5

# path: loop many iterations → cur_max becomes positive, resets to 0, becomes positive again → max_so_far captures first peak
def test_max_profit_optimized_two_peaks_first_higher():
    assert max_profit_optimized([2, 10, 1, 5]) == 8

# path: loop many iterations → cur_max becomes positive, resets to 0, becomes positive again → max_so_far captures second peak
def test_max_profit_optimized_two_peaks_second_higher():
    assert max_profit_optimized([2, 5, 1, 10]) == 9

# path: loop many iterations → cur_max positive and accumulates across multiple days → max_so_far updated at end
def test_max_profit_optimized_continuous_rise():
    assert max_profit_optimized([1, 2, 3, 4, 5]) == 4

# path: loop many iterations → cur_max positive, drops but stays positive, then increases → max_so_far updated multiple times
def test_max_profit_optimized_volatile():
    assert max_profit_optimized([3, 2, 6, 5, 0, 3]) == 4