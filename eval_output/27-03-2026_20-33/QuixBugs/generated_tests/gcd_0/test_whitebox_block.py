from correct_python_programs.gcd import gcd

# covers: block 1 (if b == 0 is True), block 2 (return a)
def test_gcd_b_is_zero():
    result = gcd(12, 0)
    assert result == 12
    # property: result divides a
    assert 12 % result == 0

# covers: block 1 (if b == 0 is False), block 3 (else: return gcd(b, a % b))
# recursive call will eventually hit b == 0
def test_gcd_basic():
    result = gcd(12, 8)
    assert result == 4
    # property: result divides both a and b
    assert 12 % result == 0
    assert 8 % result == 0

# covers: else branch with different values
def test_gcd_coprime():
    result = gcd(7, 13)
    assert result == 1
    assert 7 % result == 0
    assert 13 % result == 0

# covers: else branch, multiple recursive steps
def test_gcd_larger_numbers():
    result = gcd(100, 75)
    assert result == 25
    assert 100 % result == 0
    assert 75 % result == 0

# covers: else branch where a < b (a % b == a initially)
def test_gcd_a_less_than_b():
    result = gcd(8, 12)
    assert result == 4
    assert 8 % result == 0
    assert 12 % result == 0

# covers: b == 0 via a = 0
def test_gcd_a_is_zero():
    result = gcd(0, 5)
    assert result == 5
    assert result == gcd(5, 0)

# covers: both values equal
def test_gcd_equal_values():
    result = gcd(6, 6)
    assert result == 6
    assert 6 % result == 0