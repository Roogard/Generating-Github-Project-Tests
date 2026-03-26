from correct_python_programs.gcd import gcd

# b==0: True
def test_gcd_b_zero_true():
    assert gcd(7, 0) == 7

# b==0: False
def test_gcd_b_zero_false():
    assert gcd(48, 18) == 6