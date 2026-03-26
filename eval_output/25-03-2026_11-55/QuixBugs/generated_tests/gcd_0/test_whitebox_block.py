from correct_python_programs.gcd import gcd

# covers: block1 (b == 0), block2 (return a)
def test_gcd_b_zero():
    assert gcd(5, 0) == 5
    assert gcd(0, 0) == 0

# covers: block1 (b != 0), block3 (recursive call), block2 (eventual return)
def test_gcd_recursive_case():
    assert gcd(48, 18) == 6
    assert gcd(18, 48) == 6
    assert gcd(270, 192) == 6