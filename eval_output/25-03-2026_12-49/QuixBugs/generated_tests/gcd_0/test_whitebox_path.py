from correct_python_programs.gcd import gcd

# path: b == 0 → return a (no recursion)
def test_gcd_base_case():
    assert gcd(5, 0) == 5

# path: b != 0 → recurse once → b == 0 → return
def test_gcd_one_recursion():
    assert gcd(10, 5) == 5

# path: b != 0 → recurse multiple times → finally b == 0 → return
def test_gcd_multiple_recursions():
    assert gcd(14, 21) == 7

# path: b == 0 → return a when both a and b are zero
def test_gcd_zero_zero():
    assert gcd(0, 0) == 0