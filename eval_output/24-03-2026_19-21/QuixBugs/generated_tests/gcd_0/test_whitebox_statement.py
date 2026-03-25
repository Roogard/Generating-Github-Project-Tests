from correct_python_programs.gcd import gcd

# covers: b == 0 branch (return a)
def test_gcd_base_case():
    assert gcd(5, 0) == 5

# covers: b != 0 branch (recursive return gcd(b, a % b))
def test_gcd_recursive_case():
    assert gcd(48, 18) == 6