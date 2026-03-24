from correct_python_programs.gcd import gcd

# b==0: True
def test_gcd_b_zero():
    assert gcd(5, 0) == 5

# b==0: False (triggers recursion)
def test_gcd_recursion():
    assert gcd(48, 18) == 6