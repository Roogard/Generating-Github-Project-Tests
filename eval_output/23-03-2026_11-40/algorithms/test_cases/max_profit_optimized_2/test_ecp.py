import pytest
from algorithms.dynamic_programming.buy_sell_stock import max_profit_optimized

# Valid equivalence class: prices list with at least two elements, profitable trade exists
def test_valid_multiple_prices_profit():
    assert max_profit_optimized([7, 1, 5, 3, 6, 4]) == 5

# Valid equivalence class: prices list with at least two elements, no profitable trade (monotonic decreasing)
def test_valid_multiple_prices_no_profit():
    assert max_profit_optimized([7, 6, 4, 3, 1]) == 0

# Valid equivalence class: prices list with exactly two elements, profitable trade
def test_valid_two_prices_profit():
    assert max_profit_optimized([1, 10]) == 9

# Valid equivalence class: prices list with exactly two elements, no profitable trade
def test_valid_two_prices_no_profit():
    assert max_profit_optimized([10, 1]) == 0

# Valid equivalence class: prices list with all equal prices (profit zero)
def test_valid_all_equal_prices():
    assert max_profit_optimized([5, 5, 5, 5]) == 0

# Valid equivalence class: prices list with single element (profit zero by definition)
def test_valid_single_price():
    assert max_profit_optimized([42]) == 0

# Valid equivalence class: empty prices list (profit zero by definition)
def test_valid_empty_list():
    assert max_profit_optimized([]) == 0

# Invalid equivalence class: prices is not a list (e.g., None) - expecting TypeError
def test_invalid_input_not_list():
    with pytest.raises(TypeError):
        max_profit_optimized(None)

# Invalid equivalence class: prices list contains non-integer (e.g., float) - expecting TypeError
def test_invalid_list_contains_float():
    with pytest.raises(TypeError):
        max_profit_optimized([1, 2.5, 3])

# Invalid equivalence class: prices list contains non-numeric (e.g., string) - expecting TypeError
def test_invalid_list_contains_string():
    with pytest.raises(TypeError):
        max_profit_optimized([1, "2", 3])