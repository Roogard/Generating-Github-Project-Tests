from correct_python_programs.gcd import gcd

# condition: b == 0: True → return a directly
def test_gcd_b_is_zero():
    assert gcd(12, 0) == 12

# condition: b == 0: False → recurse; eventually b==0: True in base case
def test_gcd_b_nonzero_simple():
    assert gcd(6, 3) == 3

# condition: b == 0: False multiple times before True
def test_gcd_b_nonzero_multiple_steps():
    assert gcd(48, 18) == 6

# condition: b == 0: False → recurse with equal values
def test_gcd_equal_values():
    assert gcd(7, 7) == 7

# condition: b == 0: False → a < b case (a % b != 0 immediately)
def test_gcd_a_less_than_b():
    assert gcd(3, 9) == 3

# condition: b == 0: False → coprime numbers, base case reached with gcd=1
def test_gcd_coprime():
    assert gcd(13, 7) == 1

# condition: b == 0: True when a == 0 (edge case)
def test_gcd_a_is_zero():
    assert gcd(0, 5) == 5

# condition: b == 0: False → large numbers
def test_gcd_large_numbers():
    assert gcd(100, 75) == 25