from correct_python_programs.gcd import gcd

# b==0: True
def test_gcd_b_zero():
    assert gcd(5, 0) == 5

# b==0: False (first call), True (recursive call)
def test_gcd_standard():
    assert gcd(48, 18) == 6

# b==0: False (first call), True (recursive call with zero remainder)
def test_gcd_zero_numerator():
    assert gcd(0, 5) == 5