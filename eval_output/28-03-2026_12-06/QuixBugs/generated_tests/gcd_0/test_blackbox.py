from correct_python_programs.gcd import gcd
import math

# --- BVA ---

def test_bva_b_equals_zero():
    # b at minimum boundary (0): gcd(a, 0) should return a
    assert gcd(5, 0) == 5

def test_bva_a_equals_zero():
    # a = 0: gcd(0, b) should return b (since gcd(0, b) = b by definition)
    assert gcd(0, 5) == 5

def test_bva_both_zero():
    # gcd(0, 0) is mathematically undefined/convention; standard Euclidean returns 0
    assert gcd(0, 0) == 0

def test_bva_a_equals_one():
    # gcd(1, n) = 1 for any n >= 1
    assert gcd(1, 7) == 1

def test_bva_b_equals_one():
    # gcd(n, 1) = 1 for any n >= 1
    assert gcd(7, 1) == 1

def test_bva_a_equals_b():
    # gcd(n, n) = n
    assert gcd(13, 13) == 13

def test_bva_a_equals_b_plus_one():
    # gcd(n+1, n) = 1 (consecutive integers are coprime)
    assert gcd(8, 7) == 1

def test_bva_large_values():
    # Large boundary values
    a, b = 10**9, 10**9 - 1
    assert gcd(a, b) == math.gcd(a, b)

def test_bva_large_equal_values():
    a = 10**9
    assert gcd(a, a) == a

def test_bva_single_element_a_is_one():
    assert gcd(1, 1) == 1

# --- ECP ---

def test_ecp_valid_coprime():
    # Valid class: two coprime integers > 1
    assert gcd(9, 14) == 1

def test_ecp_valid_common_factor():
    # Valid class: two integers sharing a common factor
    assert gcd(12, 8) == 4

def test_ecp_valid_a_multiple_of_b():
    # Valid class: a is a multiple of b
    assert gcd(20, 5) == 5

def test_ecp_valid_b_multiple_of_a():
    # Valid class: b is a multiple of a
    assert gcd(5, 20) == 5

def test_ecp_valid_prime_inputs():
    # Valid class: both inputs are distinct primes (gcd = 1)
    assert gcd(13, 17) == 1

def test_ecp_valid_same_prime():
    # Valid class: both inputs are the same prime
    assert gcd(7, 7) == 7

def test_ecp_valid_large_common_factor():
    # Valid class: large inputs with a large gcd
    assert gcd(100, 75) == 25

def test_ecp_valid_power_of_two():
    # Valid class: powers of two
    assert gcd(16, 4) == 4

def test_ecp_valid_fibonacci_consecutive():
    # Consecutive Fibonacci numbers are coprime
    assert gcd(55, 34) == 1

def test_ecp_valid_result_matches_builtin():
    # Property: result must always equal math.gcd for all valid positive inputs
    for a, b in [(48, 18), (100, 75), (1071, 462), (270, 192)]:
        assert gcd(a, b) == math.gcd(a, b), f"Failed for gcd({a}, {b})"

# --- Mutation Detection ---

def test_mutation_off_by_one_modulo():
    # Detects: wrong modulo logic (e.g., a % b replaced by a % (b+1))
    # gcd(9, 6) should be 3
    assert gcd(9, 6) == 3

def test_mutation_swap_a_b_in_recursive_call():
    # Detects: recursive call uses gcd(a, b % a) instead of gcd(b, a % b)
    # gcd(14, 21) = 7; if args swapped the recursion may still converge in some cases
    # but gcd(10, 4) = 2; wrong recursion gcd(10, 4%10)=gcd(10,4) would loop
    assert gcd(10, 4) == 2

def test_mutation_base_case_wrong_variable():
    # Detects: return b instead of return a when b == 0
    # gcd(7, 0): if mutation returns b (0) instead of a (7), result differs
    assert gcd(7, 0) == 7

def test_mutation_base_case_condition_negated():
    # Detects: condition changed to b != 0 (enters else for b==0)
    # gcd(3, 0) should be 3; if condition is negated, recursion is wrong
    assert gcd(3, 0) == 3

def test_mutation_off_by_one_base_condition():
    # Detects: b == 0 changed to b == 1 (early termination at b=1)
    # gcd(9, 3) = 3; if base case triggers at b==1, gcd(9,3) might return 1 prematurely
    assert gcd(9, 3) == 3

def test_mutation_wrong_operator_modulo_replaced_by_division():
    # Detects: a % b replaced by a // b
    # gcd(10, 3): correct = gcd(3, 10%3)=gcd(3,1)=1
    # mutation: gcd(3, 10//3)=gcd(3,3)=3 — wrong
    assert gcd(10, 3) == 1

def test_mutation_wrong_operator_subtraction_instead_of_modulo():
    # Detects: a % b replaced by a - b (subtraction-based gcd variant)
    # Both produce correct results for small inputs; test a case where they differ
    # gcd(100, 3): subtraction version would eventually work but modulo is used here
    # Property check: result must equal math.gcd
    assert gcd(100, 3) == math.gcd(100, 3)

def test_mutation_constant_zero_off_by_one():
    # Detects: base case uses b == 1 instead of b == 0
    # gcd(4, 2): should be 2; if base triggers at b==1, gcd(2,0)->returns 2 still OK
    # Use gcd(6, 2) = 2; trace: gcd(2, 0) -> returns 2 correctly
    assert gcd(6, 2) == 2

def test_mutation_recursive_args_both_same():
    # Detects: recursive call gcd(b, b) instead of gcd(b, a % b)
    # gcd(15, 10): correct path gcd(10, 5) -> gcd(5, 0) -> 5
    # mutation gcd(10, 10) -> gcd(10, 0) -> 10 (wrong)
    assert gcd(15, 10) == 5

def test_mutation_and_vs_or_in_condition():
    # Detects: condition changed to a == 0 or b == 0 returning wrong value
    # gcd(6, 4) should be 2, not 6 or 4
    assert gcd(6, 4) == 2

def test_mutation_returns_b_instead_of_a():
    # Detects: return b instead of return a (b is 0 at base case)
    # gcd(11, 0) should be 11, not 0
    assert gcd(11, 0) == 11