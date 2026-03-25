from correct_python_programs.gcd import gcd

# catches: "b == 0" mutated to "b != 0" or removed base case
def test_base_case_b_zero():
    assert gcd(7, 0) == 7

# catches: "b == 0" mutated to "a == 0" (wrong variable in condition)
def test_base_case_a_zero():
    assert gcd(0, 5) == 5

# catches: wrong modulo operator (a % b -> a // b) or off-by-one in modulo
def test_common_factor():
    assert gcd(12, 8) == 4

# catches: incorrect early return for b == 1 or missing recursion deeper
def test_coprime_numbers():
    assert gcd(17, 13) == 1

# catches: wrong argument order in recursive call (gcd(a % b, b) vs gcd(b, a % b))
def test_other_common_factor():
    assert gcd(14, 21) == 7

# catches: base case incorrectly only for b == 1 (should be b == 0)
def test_base_case_b_one():
    assert gcd(7, 1) == 1