from correct_python_programs.gcd import gcd

# path: b == 0 → return a (base case, single call)
def test_gcd_b_is_zero():
    assert gcd(5, 0) == 5

# path: b != 0 → recursive call → b == 0 on next call (1 recursive step)
def test_gcd_one_recursive_step():
    assert gcd(10, 5) == 5

# path: b != 0 → recursive calls → b == 0 after multiple steps (many recursive steps)
def test_gcd_multiple_recursive_steps():
    assert gcd(48, 18) == 6

# path: b != 0 → recursive calls → coprime numbers (gcd = 1)
def test_gcd_coprime_numbers():
    assert gcd(7, 13) == 1

# path: b != 0 → a < b initially → recursive calls until b == 0
def test_gcd_a_less_than_b():
    assert gcd(18, 48) == 6

# path: b != 0 → a == b → single recursive step → b == 0
def test_gcd_equal_numbers():
    assert gcd(7, 7) == 7

# path: b == 0 → return a where a == 0
def test_gcd_both_zero():
    assert gcd(0, 0) == 0

# path: b != 0 → a is 0 → recursive call → b == 0
def test_gcd_a_is_zero():
    assert gcd(0, 5) == 5

# path: b != 0 → large numbers → multiple recursive steps
def test_gcd_large_numbers():
    assert gcd(1071, 462) == 21