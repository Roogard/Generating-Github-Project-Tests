from correct_python_programs.gcd import gcd

# catches wrong return variable, missing return, or comparison swapped (b == 0 mutated to b != 0)
def test_gcd_base_case_b_zero():
    assert gcd(7, 0) == 7

# catches missing recursive handling or wrong parameter order for a == 0 case
def test_gcd_zero_a():
    assert gcd(0, 5) == 5

# catches wrong operator mutation: 'a % b' mutated to 'a // b'
def test_gcd_nontrivial():
    assert gcd(12, 15) == 3

# catches wrong operator mutation in modulus or subtraction mutation in recursion
def test_gcd_rel_prime():
    assert gcd(10, 3) == 1

# catches missing base case mutation: gcd(0,0) should return 0, not recurse/divide by zero
def test_gcd_both_zero():
    assert gcd(0, 0) == 0

# catches wrong recursion argument order (e.g., swapping parameters in recursive call)
def test_gcd_commutativity():
    assert gcd(15, 12) == 3
    assert gcd(12, 15) == 3