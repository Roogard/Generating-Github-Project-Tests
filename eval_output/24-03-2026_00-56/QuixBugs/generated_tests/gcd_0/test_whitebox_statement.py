from correct_python_programs.gcd import gcd

# covers: if b == 0 (True), return a
def test_gcd_b_zero():
    assert gcd(12, 0) == 12

# covers: if b == 0 (False), else branch, recursive call, return gcd(...)
# This test will execute the recursive call until base case is reached.
def test_gcd_recursive():
    assert gcd(48, 18) == 6