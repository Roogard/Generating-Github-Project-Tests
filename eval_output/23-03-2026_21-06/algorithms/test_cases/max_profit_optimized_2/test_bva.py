import pytest
from algorithms.dynamic_programming.buy_sell_stock import max_profit_optimized

def test_empty_list():
    assert max_profit_optimized([]) == 0

def test_single_price():
    assert max_profit_optimized([5]) == 0

def test_two_prices_increasing():
    assert max_profit_optimized([1, 2]) == 1

def test_two_prices_decreasing():
    assert max_profit_optimized([2, 1]) == 0

def test_two_prices_equal():
    assert max_profit_optimized([3, 3]) == 0

def test_minimum_possible_price():
    assert max_profit_optimized([0, 1]) == 1

def test_maximum_possible_price():
    assert max_profit_optimized([10**4, 10**4 + 1]) == 1

def test_all_decreasing():
    assert max_profit_optimized([5, 4, 3, 2, 1]) == 0

def test_all_increasing():
    assert max_profit_optimized([1, 2, 3, 4, 5]) == 4

def test_profit_at_end():
    assert max_profit_optimized([3, 2, 1, 2, 3]) == 2

def test_profit_at_start():
    assert max_profit_optimized([1, 5, 4, 3, 2]) == 4

def test_large_price_fluctuation():
    assert max_profit_optimized([2, 10, 1, 5]) == 8

def test_multiple_peaks():
    assert max_profit_optimized([1, 5, 3, 8, 2, 10]) == 9

def test_zero_profit_constant_prices():
    assert max_profit_optimized([7, 7, 7, 7]) == 0

def test_single_day_drop_then_rise():
    assert max_profit_optimized([10, 1, 10]) == 9

def test_minimum_length_list_with_profit():
    assert max_profit_optimized([0, 100]) == 100

def test_minimum_length_list_without_profit():
    assert max_profit_optimized([100, 0]) == 0

def test_alternating_prices():
    assert max_profit_optimized([1, 3, 2, 4, 3, 5]) == 4