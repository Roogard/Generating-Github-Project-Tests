from correct_python_programs.gcd import gcd

# catches: "b == 0" mutated to "a == 0" (wrong variable in base case)
def test_base_case_b_zero():
    assert gcd(5, 0) == 5

# catches: "return a" mutated to "return b" (wrong variable returned in base case)
def test_base_case_returns_a_not_b():
    assert gcd(7, 0) == 7

# catches: "a % b" mutated to "b % a" (swapped operands in modulo)
def test_modulo_operand_order():
    assert gcd(10, 3) == 1

# catches: "gcd(b, a % b)" mutated to "gcd(a, a % b)" (wrong first arg in recursion)
def test_recursive_first_arg():
    assert gcd(12, 8) == 4

# catches: "a % b" mutated to "a / b" or "a - b" (wrong operator)
def test_modulo_vs_division():
    assert gcd(9, 6) == 3

# catches: "a % b" mutated to "a + b" (wrong arithmetic operator)
def test_gcd_coprime():
    assert gcd(7, 5) == 1

# catches: "b == 0" mutated to "b == 1" (wrong constant in base case)
def test_base_case_b_is_one():
    assert gcd(10, 1) == 1

# catches: missing else / fall-through without returning recursive result
def test_recursive_result_returned():
    assert gcd(48, 18) == 6

# catches: "a % b" mutated to "b % a" for edge case where a < b
def test_gcd_a_less_than_b():
    assert gcd(3, 9) == 3

# catches: "return a" mutated to "return 0" (wrong constant)
def test_base_case_returns_nonzero():
    assert gcd(13, 0) == 13

# catches: "b == 0" mutated to "b != 0" (negation of condition)
def test_negation_of_base_condition():
    assert gcd(6, 0) == 6

# catches: wrong recursion depth / off-by-one that stops too early
def test_multi_step_recursion():
    assert gcd(100, 75) == 25

# catches: "gcd(b, a % b)" mutated to "gcd(b, b % a)" (swapped in recursive call)
def test_large_values_gcd():
    assert gcd(252, 105) == 21

# catches: "a % b" mutated to "a - b" (subtraction instead of modulo)
def test_subtraction_vs_modulo():
    assert gcd(100, 3) == 1

# catches: both arguments equal
def test_equal_arguments():
    assert gcd(7, 7) == 7