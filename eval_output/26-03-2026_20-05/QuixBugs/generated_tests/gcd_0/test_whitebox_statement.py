from correct_python_programs.gcd import gcd

# covers: if b == 0 (True), return a
def test_gcd_b_is_zero():
    assert gcd(5, 0) == 5

# covers: if b == 0 (False), return gcd(b, a % b) — recursive call eventually hits b==0
def test_gcd_basic():
    assert gcd(12, 8) == 4

# covers: same branches with different values
def test_gcd_coprime():
    assert gcd(7, 3) == 1

# covers: a equals b
def test_gcd_equal():
    assert gcd(6, 6) == 6