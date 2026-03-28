from correct_python_programs.gcd import gcd

# covers: block 1 (entry, b == 0 is True), block 2 (return a)
def test_gcd_b_is_zero():
    result = gcd(12, 0)
    assert result == 12
    assert result % 12 == 0

# covers: block 1 (entry, b != 0), block 3 (else branch, recursive call)
# eventually reaches b == 0 base case through recursion
def test_gcd_basic():
    result = gcd(12, 8)
    assert result == 4
    assert 12 % result == 0
    assert 8 % result == 0

# covers: else branch with coprime numbers (gcd == 1)
def test_gcd_coprime():
    result = gcd(7, 13)
    assert result == 1
    assert 7 % result == 0
    assert 13 % result == 0

# covers: else branch where a < b (swaps effectively)
def test_gcd_a_less_than_b():
    result = gcd(8, 12)
    assert result == 4
    assert 8 % result == 0
    assert 12 % result == 0

# covers: else branch with equal values
def test_gcd_equal_values():
    result = gcd(9, 9)
    assert result == 9
    assert 9 % result == 0

# covers: else branch with larger values
def test_gcd_larger_values():
    result = gcd(100, 75)
    assert result == 25
    assert 100 % result == 0
    assert 75 % result == 0

# covers: gcd(a, 1) should always be 1
def test_gcd_with_one():
    result = gcd(15, 1)
    assert result == 1
    assert 15 % result == 0
    assert 1 % result == 0