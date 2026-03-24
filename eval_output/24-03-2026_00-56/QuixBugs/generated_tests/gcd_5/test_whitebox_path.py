import pytest
from correct_python_programs.gcd import gcd

# path: b == 0 → True → return a
def test_gcd_b_zero():
    assert gcd(42, 0) == 42

# path: b == 0 → False → recursive call eventually reaches base case
# This path covers the recursive reduction until b becomes 0.
# Test with two numbers where recursion depth is 1 (one recursive call).
def test_gcd_recursive_one_step():
    assert gcd(8, 12) == 4

# path: b == 0 → False → recursive call with multiple reductions
# Test with numbers that require multiple recursive steps.
def test_gcd_recursive_multiple_steps():
    assert gcd(54, 24) == 6

# path: b == 0 → False → recursive call where a % b becomes 0 immediately
# This tests the case where after first modulo, b becomes 0 in the next call.
def test_gcd_mod_zero_next():
    assert gcd(12, 4) == 4

# path: b == 0 → False → recursive call with swapped values due to modulo
# Test with a < b, ensuring the first recursive call swaps them.
def test_gcd_a_less_than_b():
    assert gcd(12, 18) == 6