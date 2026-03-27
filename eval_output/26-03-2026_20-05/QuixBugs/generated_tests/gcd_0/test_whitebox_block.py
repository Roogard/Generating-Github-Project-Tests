from correct_python_programs.gcd import gcd

# covers: block 1 (entry), block 2 (b == 0, return a)
def test_gcd_b_is_zero():
    assert gcd(5, 0) == 5

# covers: block 1 (entry), block 3 (else branch, recursive call)
# eventually hits block 2 on recursion base case
def test_gcd_basic():
    assert gcd(12, 8) == 4

# covers: block 3 (else branch) with a < b initially
def test_gcd_a_less_than_b():
    assert gcd(8, 12) == 4

# covers: recursive path with coprime numbers
def test_gcd_coprime():
    assert gcd(7, 13) == 1

# covers: same values
def test_gcd_same_values():
    assert gcd(6, 6) == 6

# covers: one divides the other
def test_gcd_divisible():
    assert gcd(10, 5) == 5

# covers: gcd(a, 0) where a is 0
def test_gcd_both_zero():
    assert gcd(0, 0) == 0