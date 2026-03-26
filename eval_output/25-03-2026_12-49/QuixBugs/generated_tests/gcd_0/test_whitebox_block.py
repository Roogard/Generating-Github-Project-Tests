from correct_python_programs.gcd import gcd

# covers: block where b == 0 (if-true branch)
def test_gcd_b_zero():
    assert gcd(7, 0) == 7

# covers: block where b != 0 (else branch, recursive path)
def test_gcd_recursive():
    assert gcd(48, 18) == 6

# covers: else branch followed by immediate base case in recursion
def test_gcd_zero_and_nonzero():
    assert gcd(0, 5) == 5