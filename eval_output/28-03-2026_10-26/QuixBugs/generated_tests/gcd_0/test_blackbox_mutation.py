from correct_python_programs.gcd import gcd

# catches: "b == 0" mutated to "a == 0" (wrong variable in base case)
def test_base_case_b_is_zero():
    assert gcd(5, 0) == 5

# catches: "return a" mutated to "return b" (wrong variable in base case return)
def test_base_case_returns_a_not_b():
    assert gcd(7, 0) == 7

# catches: "a % b" mutated to "b % a" (swapped operands in modulo)
def test_modulo_operand_order():
    # gcd(10, 3): correct is gcd(3, 10%3)=gcd(3,1)=gcd(1,0)=1
    # if mutated to b%a: gcd(3, 3%10)=gcd(3,3)->...=3, which is wrong
    assert gcd(10, 3) == 1

# catches: "gcd(b, a % b)" mutated to "gcd(a, a % b)" (wrong first argument in recursion)
def test_recursive_first_arg():
    # gcd(12, 8): correct=4; if first arg stays a=12 instead of b=8, recursion diverges or gives wrong answer
    assert gcd(12, 8) == 4

# catches: "a % b" mutated to "a // b" (wrong operator in recursion)
def test_modulo_not_division():
    # gcd(9, 6): correct=3; a//b=1, gcd(6,1)=1 which is wrong
    assert gcd(9, 6) == 3

# catches: missing else / wrong branching (b != 0 case returns a immediately)
def test_non_trivial_gcd():
    assert gcd(48, 18) == 6

# catches: "b == 0" mutated to "b != 0" (negated base case condition)
def test_negated_base_case():
    # if condition flipped, b==0 triggers recursion (infinite) and b!=0 returns a
    # for b!=0, correct should recurse; a direct call with b!=0 should not equal a
    assert gcd(15, 5) == 5
    assert gcd(15, 5) != 15

# catches: off-by-one or constant error in base value (e.g., returning 0 instead of a)
def test_base_case_nonzero_return():
    assert gcd(13, 0) != 0
    assert gcd(13, 0) == 13

# catches: "a % b" mutated to "a - b" (subtraction instead of modulo)
def test_modulo_not_subtraction():
    # gcd(100, 3): modulo gives fast convergence to 1; subtraction would be very slow and wrong for large gaps
    assert gcd(100, 3) == 1

# catches: swapping arguments entirely: gcd(a, b) -> gcd(b, a) in recursive call (both swapped)
def test_asymmetric_inputs():
    # gcd is commutative so test with known value
    assert gcd(14, 21) == 7
    assert gcd(21, 14) == 7

# catches: returning 1 always (constant mutation)
def test_gcd_greater_than_one():
    assert gcd(24, 36) == 12

# catches: returning 0 always (constant mutation)
def test_gcd_never_zero_for_positive_inputs():
    assert gcd(5, 10) > 0
    assert gcd(7, 7) == 7

# catches: "return a" mutated to "return a + b" or "return a - b"
def test_base_case_exact_value():
    assert gcd(42, 0) == 42