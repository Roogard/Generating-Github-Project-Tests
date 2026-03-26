from correct_python_programs.gcd import gcd

# catches "%” mutated to "//" or "/" (wrong operator)
def test_gcd_division_mutation():
    assert gcd(10, 6) == 2

# catches a divisible by b off-by-one in modulo mutated to a % b + 1
def test_gcd_divisible_off_by_one_plus():
    assert gcd(14, 7) == 7

# catches off-by-one in modulo mutated to a % b - 1
def test_gcd_remainder_off_by_one_minus():
    assert gcd(15, 7) == 1

# catches wrong variable in base case (return b instead of a)
def test_gcd_base_case_zero():
    assert gcd(5, 0) == 5

# catches base case conditional mutated from "b == 0" to "b == 1"
def test_gcd_base_case_one():
    assert gcd(5, 1) == 1

# catches incorrect handling of zero as first argument or swapped recursion order
def test_gcd_zero_first_arg():
    assert gcd(0, 5) == 5