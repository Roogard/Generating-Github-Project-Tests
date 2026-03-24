import pytest
from algorithms.dynamic_programming.buy_sell_stock import max_profit_optimized

def test_empty_price_list():
    assert max_profit_optimized([]) == 0

def test_single_price():
    assert max_profit_optimized([5]) == 0

def test_two_prices_profitable():
    assert max_profit_optimized([1, 5]) == 4

def test_two_prices_non_profitable():
    assert max_profit_optimized([5, 1]) == 0

def test_three_prices_ascending():
    assert max_profit_optimized([1, 2, 3]) == 2

def test_three_prices_descending():
    assert max_profit_optimized([3, 2, 1]) == 0

def test_three_prices_valley():
    assert max_profit_optimized([5, 1, 6]) == 5

def test_profit_at_end():
    assert max_profit_optimized([5, 4, 3, 2, 1, 3]) == 2

def test_profit_at_beginning():
    assert max_profit_optimized([1, 5, 4, 3, 2]) == 4

def test_all_equal_prices():
    assert max_profit_optimized([7, 7, 7, 7]) == 0

def test_large_profit_span():
    assert max_profit_optimized([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) == 9

def test_large_loss_span():
    assert max_profit_optimized([10, 9, 8, 7, 6, 5, 4, 3, 2, 1]) == 0

def test_alternating_prices():
    assert max_profit_optimized([1, 5, 1, 5, 1, 5]) == 4

def test_min_price_value():
    assert max_profit_optimized([0, 1, 0]) == 1

def test_max_price_value():
    assert max_profit_optimized([10**6, 10**6 + 5, 10**6]) == 5

def test_long_list_no_profit():
    prices = list(range(1000, 0, -1))
    assert max_profit_optimized(prices) == 0

def test_long_list_small_profit():
    prices = list(range(1000)) + [999]
    assert max_profit_optimized(prices) == 999

def test_profit_with_price_drop():
    assert max_profit_optimized([3, 2, 6, 5, 0, 3]) == 4

def test_profit_with_multiple_rises():
    assert max_profit_optimized([1, 2, 1, 2, 1, 2]) == 1

def test_profit_zero_after_calculation():
    assert max_profit_optimized([5, 4, 3, 2, 1]) == 0

# kills: Swapped arguments: swapping prices[i] and prices[i-1] in the max function call instead of in the subtraction
def test_mutation_swap_prices_in_subtraction():
    """Targets mutant where prices[i] and prices[i-1] are swapped in the subtraction.
    Original: cur_max + prices[i] - prices[i-1]
    Mutant:   cur_max + prices[i-1] - prices[i]
    This test uses a sequence where the order matters for the subtraction result."""
    # Sequence where prices[i] - prices[i-1] is positive but prices[i-1] - prices[i] is negative
    # For i=1: prices[1]-prices[0] = 3-1 = 2, mutant gives 1-3 = -2
    # cur_max becomes max(0, 0 + 2) = 2 vs max(0, 0 + (-2)) = 0
    # max_so_far becomes 2 vs 0
    assert max_profit_optimized([1, 3, 2]) == 2

# Additional test to ensure detection of the same mutant in different scenario
def test_mutation_swap_prices_in_subtraction_with_negative_cur_max():
    """Targets the same mutant when cur_max is negative from previous iteration.
    Original: cur_max = max(0, cur_max + prices[i] - prices[i-1])
    Mutant:   cur_max = max(0, cur_max + prices[i-1] - prices[i])
    With cur_max negative, the difference in subtraction outcome affects whether max(0, ...) stays 0 or not."""
    # Sequence: [5, 3, 4]
    # i=1: prices[1]-prices[0] = 3-5 = -2, cur_max = max(0, 0 + (-2)) = 0
    # i=2: prices[2]-prices[1] = 4-3 = 1, cur_max = max(0, 0 + 1) = 1, max_so_far=1
    # Mutant at i=2: prices[1]-prices[2] = 3-4 = -1, cur_max = max(0, 0 + (-1)) = 0, max_so_far stays 0
    assert max_profit_optimized([5, 3, 4]) == 1