from correct_python_programs.gcd import gcd

# covers: block 1 (b == 0)
def test_gcd_b_zero():
    assert gcd(5, 0) == 5
    assert gcd(0, 0) == 0

# covers: block 2 (recursive case) and block 1 via recursion
def test_gcd_recursive_multiple_levels():
    # 48 % 18 = 12 -> 18 % 12 = 6 -> 12 % 6 = 0 -> return 6
    assert gcd(48, 18) == 6

# covers: block 2 when b > a, and block 1 via recursion
def test_gcd_b_greater_than_a():
    # 10 % 15 = 10 -> gcd(15, 10) reduces to gcd(10, 5) -> gcd(5, 0) = 5
    assert gcd(10, 15) == 5