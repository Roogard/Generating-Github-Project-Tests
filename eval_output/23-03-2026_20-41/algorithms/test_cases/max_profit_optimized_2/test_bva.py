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

def test_all_decreasing():
    assert max_profit_optimized([5, 4, 3, 2, 1]) == 0

def test_all_increasing():
    assert max_profit_optimized([1, 2, 3, 4, 5]) == 4

def test_profit_at_end():
    assert max_profit_optimized([3, 2, 1, 2, 3]) == 2

def test_profit_in_middle():
    assert max_profit_optimized([7, 1, 5, 3, 6, 4]) == 5

def test_min_price_zero():
    assert max_profit_optimized([0, 1, 2]) == 2

def test_large_price_range():
    assert max_profit_optimized([1, 1000]) == 999

def test_price_at_max_int_boundary():
    import sys
    max_int = sys.maxsize
    assert max_profit_optimized([0, max_int]) == max_int

def test_price_at_min_int_boundary():
    import sys
    min_int = -sys.maxsize - 1
    # Since prices are list[int], negative prices are allowed in Python typing.
    # Test with negative to zero transition.
    assert max_profit_optimized([min_int, 0]) == -min_int

def test_alternating_prices():
    assert max_profit_optimized([1, 3, 2, 4, 3, 5]) == 4

def test_flat_prices():
    assert max_profit_optimized([7, 7, 7, 7]) == 0

def test_single_dip_then_rise():
    assert max_profit_optimized([10, 1, 10]) == 9

def test_profit_after_minimum():
    assert max_profit_optimized([3, 1, 2, 4]) == 3