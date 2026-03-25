from correct_python_programs.gcd import gcd

# covers: block 1, block 2 (b == 0)
def test_gcd_base_case():
    assert gcd(10, 0) == 10

# covers: block 1, block 3 (b != 0), and subsequent recursion until base case
def test_gcd_recursive_case():
    assert gcd(14, 21) == 7