from correct_python_programs.gcd import gcd

# b==0: True
def test_gcd_b_zero():
    assert gcd(5, 0) == 5

# b==0: False
def test_gcd_b_nonzero():
    assert gcd(10, 15) == 5