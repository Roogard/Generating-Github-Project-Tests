from correct_python_programs.gcd import gcd

# condition: b == 0: True → return a
def test_gcd_b_is_zero():
    result = gcd(12, 0)
    # gcd(12, 0) should return 12
    assert result == 12
    # property: result divides a
    assert 12 % result == 0

# condition: b == 0: False → recurse (b != 0, eventually reaches b==0)
def test_gcd_b_not_zero_simple():
    result = gcd(12, 4)
    # gcd(12, 4) should be 4
    assert result == 4
    # property: result divides both a and b
    assert 12 % result == 0
    assert 4 % result == 0

# condition: b == 0: False → recurse; covers case where a % b != 0 initially
def test_gcd_b_not_zero_non_divisible():
    result = gcd(10, 3)
    # gcd(10, 3) should be 1
    assert result == 1
    # property: result divides both a and b
    assert 10 % result == 0
    assert 3 % result == 0

# condition: b == 0: False → recurse; larger gcd
def test_gcd_b_not_zero_larger_gcd():
    result = gcd(48, 18)
    # gcd(48, 18) should be 6
    assert result == 6
    # property: result divides both a and b
    assert 48 % result == 0
    assert 18 % result == 0

# condition: b == 0: False → recurse; coprime numbers
def test_gcd_coprime():
    result = gcd(7, 13)
    # gcd(7, 13) should be 1
    assert result == 1
    # property: result divides both a and b
    assert 7 % result == 0
    assert 13 % result == 0

# condition: b == 0: True → return a (a == 0 edge case)
def test_gcd_both_zero():
    result = gcd(0, 0)
    # gcd(0, 0) conventionally returns 0
    assert result == 0

# condition: b == 0: False → recurse; a is 0, b is not
def test_gcd_a_zero_b_not_zero():
    result = gcd(0, 5)
    # gcd(0, 5) should be 5
    assert result == 5
    # property: result divides b
    assert 5 % result == 0

# condition: b == 0: False → recurse multiple times; equal values
def test_gcd_equal_values():
    result = gcd(9, 9)
    # gcd(9, 9) should be 9
    assert result == 9
    # property: result divides both a and b
    assert 9 % result == 0
    assert 9 % result == 0

# condition: b == 0: False → recurse; b > a initially
def test_gcd_b_greater_than_a():
    result = gcd(4, 12)
    # gcd(4, 12) should be 4
    assert result == 4
    # property: result divides both a and b
    assert 4 % result == 0
    assert 12 % result == 0