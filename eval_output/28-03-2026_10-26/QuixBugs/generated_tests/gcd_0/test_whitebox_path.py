from correct_python_programs.gcd import gcd
import math

# path: b == 0 → return a (base case, no recursion)
def test_gcd_base_case_b_zero():
    result = gcd(7, 0)
    assert result == 7
    assert result % 7 == 0
    assert 7 % result == 0

# path: b != 0 → recurse once → b == 0 (one recursive call)
def test_gcd_one_recursion():
    # gcd(6, 3): gcd(3, 0) → 3
    result = gcd(6, 3)
    assert result == math.gcd(6, 3)
    assert 6 % result == 0
    assert 3 % result == 0

# path: b != 0 → recurse multiple times → b == 0 (multiple recursive calls)
def test_gcd_multiple_recursions():
    # gcd(48, 18): several steps before b == 0
    result = gcd(48, 18)
    assert result == math.gcd(48, 18)
    assert 48 % result == 0
    assert 18 % result == 0

# path: b != 0 → recurse multiple times → coprime inputs (gcd == 1)
def test_gcd_coprime_numbers():
    result = gcd(13, 7)
    assert result == math.gcd(13, 7)
    assert result == 1
    assert 13 % result == 0
    assert 7 % result == 0

# path: b != 0 → recurse → same number (a == b)
def test_gcd_equal_numbers():
    result = gcd(9, 9)
    assert result == math.gcd(9, 9)
    assert result == 9
    assert 9 % result == 0

# path: b != 0 → recurse multiple times → large Fibonacci-like inputs (worst case for Euclid)
def test_gcd_fibonacci_like():
    # Consecutive Fibonacci numbers are coprime
    result = gcd(89, 55)
    assert result == math.gcd(89, 55)
    assert 89 % result == 0
    assert 55 % result == 0

# path: b != 0 → recurse → a < b (a and b swapped in effect)
def test_gcd_a_less_than_b():
    # gcd(3, 9): first call has a < b, so recursion swaps effectively
    result = gcd(3, 9)
    assert result == math.gcd(3, 9)
    assert 3 % result == 0
    assert 9 % result == 0

# path: base case with a == 0 and b == 0
def test_gcd_both_zero():
    result = gcd(0, 0)
    # By convention gcd(0,0) == 0
    assert result == 0

# path: b != 0 → recurse → a is 0, b is nonzero (result should be b)
def test_gcd_a_zero_b_nonzero():
    result = gcd(0, 5)
    assert result == math.gcd(0, 5)
    assert result == 5