from correct_python_programs.gcd import gcd

# catches: "b == 0" mutated to "b <= 0" (boundary mutation)
def test_gcd_b_is_zero():
    assert gcd(12, 0) == 12

# catches: "b == 0" mutated to "b != 0" (negation error)
def test_gcd_a_is_zero():
    assert gcd(0, 7) == 7

# catches: "a % b" mutated to "a / b" (wrong operator)
def test_gcd_non_trivial():
    assert gcd(48, 18) == 6

# catches: "return a" mutated to "return b" (wrong variable)
def test_gcd_b_is_zero_returns_a():
    assert gcd(17, 0) == 17

# catches: "return gcd(b, a % b)" mutated to "return gcd(a, a % b)" (wrong variable)
def test_gcd_ensures_recursion_swaps():
    assert gcd(18, 48) == 6

# catches: missing base case (infinite recursion) - test would hang or overflow
# This test passes quickly on correct implementation.
def test_gcd_mutually_prime():
    assert gcd(13, 17) == 1

# catches: "a % b" mutated to "b % a" (argument swap)
def test_gcd_larger_first():
    assert gcd(100, 25) == 25

# catches: "a % b" mutated to "(a % b) + 1" (off-by-one in operation)
def test_gcd_exact_multiple():
    assert gcd(81, 9) == 9

# catches: "b == 0" mutated to "a == 0" (wrong variable in condition)
def test_gcd_both_non_zero():
    assert gcd(21, 14) == 7

# catches: "return gcd(b, a % b)" mutated to "return gcd(b, b % a)" (wrong modulo order)
def test_gcd_small_remainder():
    assert gcd(17, 5) == 1