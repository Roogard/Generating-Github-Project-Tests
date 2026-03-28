from correct_python_programs.gcd import gcd

# condition: b == 0: True → return a
def test_gcd_b_is_zero():
    result = gcd(12, 0)
    # A correct gcd(a, 0) should return a
    assert result == 12
    # Property: result divides a
    assert 12 % result == 0

# condition: b == 0: False → recurse (b != 0, a % b eventually reaches 0)
def test_gcd_b_not_zero_simple():
    result = gcd(12, 4)
    # A correct gcd(12, 4) should return 4
    assert result == 4
    # Property: result divides both a and b
    assert 12 % result == 0
    assert 4 % result == 0

# condition: b == 0: False at first call, True eventually → gcd of coprime numbers
def test_gcd_b_not_zero_coprime():
    result = gcd(7, 3)
    # A correct gcd(7, 3) for coprime numbers should return 1
    assert result == 1
    # Property: result divides both a and b
    assert 7 % result == 0
    assert 3 % result == 0

# condition: b == 0: False → multiple recursive steps before b == 0
def test_gcd_b_not_zero_multiple_steps():
    result = gcd(48, 18)
    # A correct gcd(48, 18) should return 6
    assert result == 6
    # Property: result divides both a and b
    assert 48 % result == 0
    assert 18 % result == 0

# condition: b == 0: False → a == b case
def test_gcd_equal_values():
    result = gcd(9, 9)
    # A correct gcd(n, n) should return n
    assert result == 9
    # Property: result divides both a and b
    assert 9 % result == 0

# condition: b == 0: False → a < b case (b larger than a)
def test_gcd_a_less_than_b():
    result = gcd(4, 12)
    # A correct gcd(4, 12) should return 4
    assert result == 4
    # Property: result divides both a and b
    assert 4 % result == 0
    assert 12 % result == 0

# condition: b == 0: True → a == 0 edge case
def test_gcd_both_zero():
    result = gcd(0, 0)
    # A correct gcd(0, 0) — b is 0, so returns a which is 0
    assert result == 0

# condition: b == 0: False → large values, multiple recursive steps
def test_gcd_large_values():
    result = gcd(270, 192)
    # A correct gcd(270, 192) should return 6
    assert result == 6
    # Property: result divides both a and b
    assert 270 % result == 0
    assert 192 % result == 0