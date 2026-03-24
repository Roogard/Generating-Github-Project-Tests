from correct_python_programs.gcd import gcd

# covers: if b == 0 (True), return a
def test_gcd_base_case():
    assert gcd(5, 0) == 5

# covers: if b == 0 (False), return gcd(b, a % b) through multiple recursive calls
def test_gcd_recursive_case():
    assert gcd(48, 18) == 6