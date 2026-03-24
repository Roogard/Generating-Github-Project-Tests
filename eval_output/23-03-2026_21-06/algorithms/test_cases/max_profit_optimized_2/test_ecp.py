import pytest
from algorithms.dynamic_programming.buy_sell_stock import max_profit_optimized

# Valid equivalence class: list with increasing prices (profit > 0)
def test_valid_increasing_prices():
    assert max_profit_optimized([1, 2, 3, 4, 5]) == 4

# Valid equivalence class: list with decreasing prices (profit = 0)
def test_valid_decreasing_prices():
    assert max_profit_optimized([5, 4, 3, 2, 1]) == 0

# Valid equivalence class: list with single price (profit = 0)
def test_valid_single_price():
    assert max_profit_optimized([10]) == 0

# Valid equivalence class: list with equal prices (profit = 0)
def test_valid_equal_prices():
    assert max_profit_optimized([3, 3, 3, 3]) == 0

# Valid equivalence class: list with mixed prices and profit in middle
def test_valid_mixed_prices():
    assert max_profit_optimized([7, 1, 5, 3, 6, 4]) == 5

# Valid equivalence class: list with profit at end
def test_valid_profit_at_end():
    assert max_profit_optimized([1, 2, 1, 3]) == 2

# Valid equivalence class: list with profit at start
def test_valid_profit_at_start():
    assert max_profit_optimized([1, 5, 2, 3]) == 4

# Invalid equivalence class: empty list
def test_invalid_empty_list():
    with pytest.raises(IndexError):
        max_profit_optimized([])

# Invalid equivalence class: list with non-integer element (string)
def test_invalid_non_integer_string():
    with pytest.raises(TypeError):
        max_profit_optimized([1, 2, "3"])

# Invalid equivalence class: list with non-integer element (float)
def test_invalid_non_integer_float():
    with pytest.raises(TypeError):
        max_profit_optimized([1, 2.5, 3])

# Invalid equivalence class: None input
def test_invalid_none_input():
    with pytest.raises(TypeError):
        max_profit_optimized(None)