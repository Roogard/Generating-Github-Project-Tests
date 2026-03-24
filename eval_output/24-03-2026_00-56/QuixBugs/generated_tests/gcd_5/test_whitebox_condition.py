from correct_python_programs.gcd import gcd

# condition: b == 0: True
def test_gcd_b_zero():
    assert gcd(5, 0) == 5

# condition: b == 0: False (first call)
def test_gcd_b_nonzero_recursive():
    # b != 0 in first call, eventually reaches b == 0
    assert gcd(48, 18) == 6

# condition: b == 0: False (multiple recursive calls)
def test_gcd_b_nonzero_simple():
    # b != 0 in first call, returns directly from recursive call
    assert gcd(18, 48) == 6