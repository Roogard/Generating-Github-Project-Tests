from correct_python_programs.gcd import gcd

# condition: b == 0: True → return a directly
def test_gcd_b_is_zero():
    assert gcd(5, 0) == 5

# condition: b == 0: False → recurse; eventually b==0: True in base case
def test_gcd_b_nonzero_basic():
    assert gcd(10, 5) == 5

# condition: b == 0: False initially, then True after one recursion
def test_gcd_b_nonzero_two_steps():
    assert gcd(6, 4) == 2

# condition: b == 0: False for multiple recursive steps
def test_gcd_b_nonzero_multiple_steps():
    assert gcd(48, 18) == 6

# condition: b == 0: False, a and b are coprime (gcd == 1)
def test_gcd_coprime():
    assert gcd(7, 13) == 1

# condition: b == 0: True, a is zero
def test_gcd_both_zero():
    assert gcd(0, 0) == 0

# condition: b == 0: False, a < b (reversed order)
def test_gcd_a_less_than_b():
    assert gcd(4, 8) == 4

# condition: b == 0: True, a is 1
def test_gcd_a_is_one_b_zero():
    assert gcd(1, 0) == 1

# condition: b == 0: False, a == b
def test_gcd_equal_values():
    assert gcd(9, 9) == 9