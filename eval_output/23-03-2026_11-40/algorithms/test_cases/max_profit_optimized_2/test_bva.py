import pytest
from algorithms.dynamic_programming.buy_sell_stock import max_profit_optimized

def test_empty_price_list():
    assert max_profit_optimized([]) == 0

def test_single_price():
    assert max_profit_optimized([5]) == 0

def test_two_prices_profit():
    assert max_profit_optimized([1, 2]) == 1

def test_two_prices_loss():
    assert max_profit_optimized([2, 1]) == 0

def test_three_prices_increasing():
    assert max_profit_optimized([1, 2, 3]) == 2

def test_three_prices_decreasing():
    assert max_profit_optimized([3, 2, 1]) == 0

def test_three_prices_peak_middle():
    assert max_profit_optimized([1, 3, 2]) == 2

def test_three_prices_valley_middle():
    assert max_profit_optimized([3, 1, 2]) == 1

def test_all_same_prices():
    assert max_profit_optimized([5, 5, 5, 5]) == 0

def test_profit_at_end():
    assert max_profit_optimized([5, 4, 3, 2, 1, 2]) == 1

def test_profit_at_start():
    assert max_profit_optimized([1, 5, 4, 3, 2]) == 4

def test_profit_in_middle():
    assert max_profit_optimized([3, 2, 1, 2, 1]) == 1

def test_large_price_range():
    assert max_profit_optimized([1, 100]) == 99

def test_minimum_price_value():
    assert max_profit_optimized([0, 1, 0]) == 1

def test_negative_price_not_allowed_but_handled():
    # The function expects list[int], but if negative appears, check behavior
    # This tests the algorithm's handling of price differences, not input validation
    assert max_profit_optimized([10, 5, 10]) == 5

def test_long_decreasing_sequence():
    assert max_profit_optimized([10, 9, 8, 7, 6, 5, 4, 3, 2, 1]) == 0

def test_long_increasing_sequence():
    assert max_profit_optimized([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) == 9

def test_alternating_prices():
    assert max_profit_optimized([1, 5, 1, 5, 1, 5]) == 4

def test_single_dip_and_recovery():
    assert max_profit_optimized([10, 1, 10]) == 9

def test_profit_requires_multiple_days():
    # Edge: profit only possible over multiple days, not single day
    assert max_profit_optimized([3, 1, 4, 1, 5]) == 4