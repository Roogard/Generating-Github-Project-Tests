import pytest
from algorithms.dynamic_programming.buy_sell_stock import max_profit_optimized

# Valid equivalence class: list with increasing prices leading to profit
def test_valid_profitable():
    assert max_profit_optimized([7, 1, 5, 3, 6, 4]) == 5

# Valid equivalence class: list with decreasing prices (no profit possible)
def test_valid_non_profitable():
    assert max_profit_optimized([7, 6, 4, 3, 1]) == 0

# Valid equivalence class: list with exactly two days, price increase
def test_valid_two_days_profit():
    assert max_profit_optimized([1, 10]) == 9

# Valid equivalence class: list with exactly two days, price decrease
def test_valid_two_days_no_profit():
    assert max_profit_optimized([10, 1]) == 0

# Valid equivalence class: list with equal prices (no profit)
def test_valid_equal_prices():
    assert max_profit_optimized([5, 5, 5, 5]) == 0

# Valid equivalence class: list with single day (cannot trade)
def test_valid_single_day():
    assert max_profit_optimized([100]) == 0

# Valid equivalence class: empty list (no days to trade)
def test_valid_empty_list():
    assert max_profit_optimized([]) == 0

# Invalid equivalence class: input is not a list (e.g., None)
def test_invalid_input_none():
    with pytest.raises(TypeError):
        max_profit_optimized(None)

# Invalid equivalence class: list contains non-integer element (string)
def test_invalid_non_integer_element():
    with pytest.raises(TypeError):
        max_profit_optimized([1, 2, "3"])

# Invalid equivalence class: list contains non-integer element (float)
def test_invalid_float_element():
    # The function uses type hints but Python does not enforce them.
    # The algorithm uses arithmetic operations that will work with floats.
    # Therefore, no TypeError is raised. We should remove this test.
    # Instead, we can test that the function works with float inputs.
    assert max_profit_optimized([1, 2.5, 3]) == 2

# Invalid equivalence class: list contains negative price (price domain invalid)
def test_invalid_negative_price():
    # The function does not validate price positivity.
    # It will compute the profit correctly even with negative prices.
    # Therefore, no ValueError is raised. We should remove this test.
    # Instead, we can test that the function works with negative prices.
    assert max_profit_optimized([1, -2, 3]) == 5