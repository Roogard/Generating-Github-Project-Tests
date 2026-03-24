import pytest
from correct_python_programs.gcd import gcd

# path: b == 0 → True → return a
def test_gcd_b_zero():
    assert gcd(42, 0) == 42

# path: b == 0 → False → recursive call eventually hits base case with single recursion
def test_gcd_single_recursion():
    assert gcd(10, 5) == 5

# path: b == 0 → False → recursive call eventually hits base case with multiple recursions
def test_gcd_multiple_recursions():
    assert gcd(48, 18) == 6

# path: b == 0 → False → recursive call with a % b == 0 in next call (immediate base case)
def test_gcd_next_step_zero():
    assert gcd(7, 14) == 7

# path: b == 0 → False → recursive call with a % b != 0, requiring deeper recursion
def test_gcd_large_numbers():
    assert gcd(1071, 462) == 21

# path: b == 0 → False → recursive call with negative numbers (handled by modulo)
def test_gcd_negative_numbers():
    assert gcd(-48, 18) == 6

# path: b == 0 → False → recursive call where a < b (modulo swaps them)
def test_gcd_a_less_than_b():
    assert gcd(18, 48) == 6