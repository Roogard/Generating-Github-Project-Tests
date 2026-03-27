from correct_python_programs.gcd import gcd

# catches: "b == 0" mutated to "a == 0" (wrong variable in base case)
def test_base_case_b_zero():
    assert gcd(5, 0) == 5

# catches: "return a" mutated to "return b" (wrong variable returned in base case)
def test_base_case_returns_a_not_b():
    assert gcd(7, 0) == 7

# catches: "a % b" mutated to "b % a" (wrong variable order in modulo)
def test_modulo_order():
    assert gcd(10, 3) == 1

# catches: "gcd(b, a % b)" mutated to "gcd(a, a % b)" (wrong first recursive arg)
def test_recursive_first_arg():
    assert gcd(12, 8) == 4

# catches: "a % b" mutated to "a - b" (wrong operator: modulo vs subtraction)
def test_modulo_vs_subtraction():
    assert gcd(100, 75) == 25

# catches: "a % b" mutated to "a / b" or "a * b" (wrong arithmetic operator)
def test_modulo_vs_division():
    assert gcd(9, 6) == 3

# catches: "b == 0" mutated to "b != 0" (negation of condition)
def test_negated_base_condition():
    assert gcd(0, 5) == 5

# catches: missing recursion / wrong base case when both are equal
def test_equal_values():
    assert gcd(6, 6) == 6

# catches: "b == 0" mutated to "b == 1" (constant error in base case)
def test_base_case_b_is_one():
    assert gcd(5, 1) == 1

# catches: off-by-one or constant error where gcd of coprimes should be 1
def test_coprime_numbers():
    assert gcd(13, 7) == 1

# catches: wrong variable usage causing incorrect result for larger GCD
def test_larger_gcd():
    assert gcd(48, 18) == 6

# catches: recursive call args swapped entirely "gcd(a % b, b)" instead of "gcd(b, a % b)"
def test_args_not_swapped():
    assert gcd(17, 5) == 1

# catches: "return a" mutated to "return 0" (constant error in base case)
def test_base_case_not_zero():
    assert gcd(15, 0) == 15

# catches: mutual recursion correctness for a < b case
def test_a_less_than_b():
    assert gcd(3, 12) == 3