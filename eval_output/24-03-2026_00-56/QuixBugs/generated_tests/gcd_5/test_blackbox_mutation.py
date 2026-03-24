from correct_python_programs.gcd import gcd

# catches: "b == 0" mutated to "b <= 0" (boundary mutation)
def test_gcd_b_is_zero():
    assert gcd(12, 0) == 12

# catches: "b == 0" mutated to "b != 0" (negation error)
def test_gcd_a_is_zero():
    assert gcd(0, 7) == 7

# catches: "a % b" mutated to "a / b" (wrong operator)
def test_gcd_nonzero_remainder():
    assert gcd(14, 8) == 2

# catches: "return a" mutated to "return b" (wrong variable)
def test_gcd_b_is_zero_returns_a():
    assert gcd(5, 0) == 5

# catches: "return gcd(b, a % b)" mutated to "return gcd(a, a % b)" (wrong argument)
def test_gcd_swapped_arguments():
    assert gcd(48, 18) == 6

# catches: "return gcd(b, a % b)" mutated to "return gcd(b, b % a)" (modulo swap)
def test_gcd_large_first_argument():
    assert gcd(56, 98) == 14

# catches: missing base case (infinite recursion) - test should still pass on correct code
def test_gcd_coprime():
    assert gcd(9, 28) == 1

# catches: "b == 0" mutated to "a == 0" (wrong variable in condition)
def test_gcd_both_nonzero():
    assert gcd(21, 6) == 3

# catches: off-by-one in recursion, e.g., "return gcd(b, (a % b) - 1)"
def test_gcd_exact_divisor():
    assert gcd(100, 25) == 25

# catches: "a % b" mutated to "a - b" (arithmetic operator error)
def test_gcd_with_remainder_not_divisible():
    assert gcd(17, 5) == 1