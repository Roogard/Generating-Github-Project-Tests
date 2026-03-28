import pytest
from correct_python_programs.gcd import gcd

# path: b == 0 → return a (base case, no recursion)
def test_gcd_b_is_zero():
    result = gcd(5, 0)
    assert result == 5
    assert 5 % result == 0

# path: b != 0 → recurse once → base case (b becomes 0 after one recursive call)
def test_gcd_one_recursion():
    # gcd(4, 2): gcd(2, 4%2=0) → returns 2
    result = gcd(4, 2)
    assert result == 2
    assert 4 % result == 0
    assert 2 % result == 0

# path: b != 0 → recurse multiple times → base case
def test_gcd_multiple_recursions():
    # gcd(48, 18): gcd(18,12) → gcd(12,6) → gcd(6,0) → 6
    result = gcd(48, 18)
    assert result == 6
    assert 48 % result == 0
    assert 18 % result == 0

# path: b != 0 → recurse multiple times → coprime inputs (gcd = 1)
def test_gcd_coprime():
    # gcd(7, 13): many steps, result = 1
    result = gcd(7, 13)
    assert result == 1
    assert 7 % result == 0
    assert 13 % result == 0

# path: b != 0 → recurse → both equal inputs (gcd = a = b)
def test_gcd_equal_inputs():
    result = gcd(12, 12)
    assert result == 12
    assert 12 % result == 0

# path: b != 0 → recurse → a < b (swapped order)
def test_gcd_a_less_than_b():
    # gcd(3, 9): gcd(9, 3) → gcd(3, 0) → 3
    result = gcd(3, 9)
    assert result == 3
    assert 3 % result == 0
    assert 9 % result == 0

# path: b != 0 → recurse multiple times → larger Fibonacci-like inputs (worst case for Euclidean)
def test_gcd_fibonacci_like():
    # gcd(89, 55): consecutive Fibonacci numbers, gcd = 1, many steps
    result = gcd(89, 55)
    assert result == 1
    assert 89 % result == 0
    assert 55 % result == 0

# path: b == 0, a == 0 → return 0 (edge case: both zero)
def test_gcd_both_zero():
    result = gcd(0, 0)
    assert result == 0

# path: b != 0 → recurse → a == 0, b != 0 (a is zero, b is not)
def test_gcd_a_is_zero():
    # gcd(0, 5): gcd(5, 0) → returns 5
    result = gcd(0, 5)
    assert result == 5
    assert 5 % result == 0