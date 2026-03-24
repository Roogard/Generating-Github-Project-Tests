import pytest
from algorithms.dynamic_programming.buy_sell_stock import max_profit_optimized

# path: loop 0 iterations (len(prices) <= 1) → return max_so_far (0)
def test_max_profit_optimized_empty():
    assert max_profit_optimized([]) == 0

# path: loop 0 iterations (len(prices) <= 1) → return max_so_far (0)
def test_max_profit_optimized_single():
    assert max_profit_optimized([5]) == 0

# path: loop 1 iteration → cur_max = 0 (since price diff <= 0) → max_so_far = 0 → return 0
def test_max_profit_optimized_two_descending():
    assert max_profit_optimized([5, 3]) == 0

# path: loop 1 iteration → cur_max > 0 (price diff > 0) → max_so_far = cur_max → return cur_max
def test_max_profit_optimized_two_ascending():
    assert max_profit_optimized([3, 5]) == 2

# path: loop many iterations → cur_max always 0 (never positive cumulative diff) → max_so_far = 0 → return 0
def test_max_profit_optimized_all_descending():
    assert max_profit_optimized([7, 6, 4, 3, 1]) == 0

# path: loop many iterations → cur_max becomes positive, resets to 0, becomes positive again → max_so_far tracks highest
def test_max_profit_optimized_mixed():
    assert max_profit_optimized([7, 1, 5, 3, 6, 4]) == 5

# path: loop many iterations → cur_max stays positive and grows (monotonic increase) → max_so_far = final cur_max
def test_max_profit_optimized_continuously_ascending():
    assert max_profit_optimized([1, 2, 3, 4, 5]) == 4

# path: loop many iterations → cur_max positive, then resets to 0, then positive larger than before → max_so_far updates
def test_max_profit_optimized_dip_then_big_rise():
    assert max_profit_optimized([2, 1, 4]) == 3

# path: loop many iterations → cur_max positive, then stays positive without reset (cumulative diff stays >0) → max_so_far updates each step
def test_max_profit_optimized_volatile_upward():
    assert max_profit_optimized([3, 7, 2, 4, 9]) == 7

# kills: swapping prices[i] and prices[i-1] in the max function call instead of in the subtraction
def test_max_profit_optimized_swap_args_mutant():
    """Targets mutant that swaps prices[i] and prices[i-1] in the subtraction.
    Original: cur_max + prices[i] - prices[i-1]
    Mutant:   cur_max + prices[i-1] - prices[i]
    This changes the sign of the daily difference.
    Use a sequence where daily differences alternate signs and cumulative effect matters."""
    # Sequence where daily differences are: +1, -2, +3
    # Original cumulative: day1: max(0, 0+1)=1, day2: max(0, 1-2)=0, day3: max(0, 0+3)=3 → profit=3
    # Mutant cumulative:   day1: max(0, 0-1)=0, day2: max(0, 0+2)=2, day3: max(0, 2-3)=0 → profit=2
    prices = [1, 2, 0, 3]
    assert max_profit_optimized(prices) == 3

# Additional test to ensure detection of the swapped argument mutant with different pattern
def test_max_profit_optimized_swap_args_mutant2():
    """Another test targeting the swapped prices mutant.
    Uses a longer sequence where the mutant would produce a different max_so_far."""
    # Daily differences: +5, -1, +4, -2, +3
    # Original: cumulative: 5,4,8,6,9 → max=9
    # Mutant:   cumulative: -5,4,0,-2,1 → max=4 (or 1 depending on resets)
    prices = [10, 15, 14, 18, 16, 19]
    assert max_profit_optimized(prices) == 9