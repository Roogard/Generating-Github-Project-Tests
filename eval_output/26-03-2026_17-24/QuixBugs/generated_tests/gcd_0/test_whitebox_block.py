from correct_python_programs.gcd import gcd

# covers: block 1 (entry, b == 0 is True), block 2 (return a)
def test_gcd_b_is_zero():
    assert gcd(5, 0) == 5

# covers: block 1 (entry, b != 0), block 3 (else branch, recursive call), eventually block 2
def test_gcd_basic():
    assert gcd(12, 8) == 4

# covers: else branch with coprime numbers
def test_gcd_coprime():
    assert gcd(7, 3) == 1

# covers: else branch where a < b
def test_gcd_a_less_than_b():
    assert gcd(3, 9) == 3

# covers: else branch with equal values
def test_gcd_equal():
    assert gcd(6, 6) == 6

# covers: else branch with larger values
def test_gcd_large():
    assert gcd(100, 75) == 25