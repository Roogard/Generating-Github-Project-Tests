from correct_python_programs.gcd import gcd

# covers: stmt1 (True), stmt2
def test_gcd_b_zero():
    assert gcd(10, 0) == 10

# covers: stmt1 (False), stmt4 (recursive path)
def test_gcd_recursive():
    assert gcd(48, 18) == 6