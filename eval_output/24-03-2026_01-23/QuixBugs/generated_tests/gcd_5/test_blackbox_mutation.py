from python_programs.gcd import gcd

# catches: wrong return variable in base case (return b instead of return a)
def test_gcd_b_zero_returns_a():
    assert gcd(7, 0) == 7

# catches: mutated "==" to "!=" in base check (would return a for any b)
def test_gcd_nonzero_b_recurses():
    # if base condition b != 0, gcd(5,1) would incorrectly return 5 instead of computing gcd
    assert gcd(5, 1) == 1

# catches: missing swap or wrong recursion parameters (should handle a<b by swapping)
def test_gcd_handles_a_less_than_b_via_recursion():
    # 18 and 48 are swapped internally until base case
    assert gcd(18, 48) == 6

# catches: incorrect remainder operation (e.g., using floor division instead of modulo)
def test_gcd_remainder_computation():
    assert gcd(48, 18) == 6

# catches: wrong logic when inputs are equal (should return the number itself)
def test_gcd_equal_numbers():
    assert gcd(9, 9) == 9

# catches: wrong result for coprime numbers
def test_gcd_primes():
    assert gcd(17, 13) == 1