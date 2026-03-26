from correct_python_programs.gcd import gcd

# catches: incorrect base-case check or wrong return in base (e.g., b==0 mutated or return variable wrong)
def test_gcd_base_case():
    assert gcd(5, 0) == 5

# catches: failure to handle a < b properly (wrong recursive arguments or missing swap)
def test_gcd_argument_swap():
    assert gcd(18, 48) == 6

# catches: wrong modulus operator mutation (a % b → b % a or a // b)
def test_gcd_mod_operator():
    assert gcd(48, 18) == 6

# catches: missing return in recursive call (falls through to None)
def test_gcd_missing_return():
    assert gcd(20, 6) == 2