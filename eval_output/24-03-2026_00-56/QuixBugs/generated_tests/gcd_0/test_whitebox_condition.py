from correct_python_programs.gcd import gcd

# condition: b == 0: True
def test_gcd_b_zero():
    assert gcd(5, 0) == 5

# condition: b == 0: False (first call)
def test_gcd_b_nonzero():
    assert gcd(0, 5) == 5

# condition: b == 0: False (multiple recursive calls)
def test_gcd_both_nonzero():
    assert gcd(48, 18) == 6