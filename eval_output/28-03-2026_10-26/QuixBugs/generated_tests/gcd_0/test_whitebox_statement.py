from correct_python_programs.gcd import gcd

# covers: b == 0 branch (True), return a
def test_gcd_b_is_zero():
    result = gcd(12, 0)
    assert result == 12
    assert result > 0
    assert 12 % result == 0

# covers: b != 0 branch (else), recursive call gcd(b, a % b), eventually hits b == 0
def test_gcd_basic():
    result = gcd(12, 8)
    assert result == 4
    assert 12 % result == 0
    assert 8 % result == 0

def test_gcd_coprime():
    result = gcd(7, 3)
    assert result == 1
    assert 7 % result == 0
    assert 3 % result == 0

def test_gcd_same_values():
    result = gcd(6, 6)
    assert result == 6
    assert 6 % result == 0

def test_gcd_larger_b():
    result = gcd(3, 9)
    assert result == 3
    assert 3 % result == 0
    assert 9 % result == 0

def test_gcd_divides_both():
    a, b = 48, 18
    result = gcd(a, b)
    assert a % result == 0
    assert b % result == 0
    # no larger common divisor exists
    import math
    assert result == math.gcd(a, b)