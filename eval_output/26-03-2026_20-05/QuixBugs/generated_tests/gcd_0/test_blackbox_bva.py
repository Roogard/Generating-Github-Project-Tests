from correct_python_programs.gcd import gcd

def test_gcd_b_equals_zero():
    assert gcd(5, 0) == 5

def test_gcd_a_equals_zero():
    assert gcd(0, 5) == 5

def test_gcd_both_zero():
    assert gcd(0, 0) == 0

def test_gcd_a_equals_one():
    assert gcd(1, 5) == 1

def test_gcd_b_equals_one():
    assert gcd(5, 1) == 1

def test_gcd_a_equals_b():
    assert gcd(7, 7) == 7

def test_gcd_a_is_multiple_of_b():
    assert gcd(12, 4) == 4

def test_gcd_b_is_multiple_of_a():
    assert gcd(4, 12) == 4

def test_gcd_coprime_numbers():
    assert gcd(7, 13) == 1

def test_gcd_small_values_a_one_b_one():
    assert gcd(1, 1) == 1

def test_gcd_large_values():
    assert gcd(1000000, 999999) == 1

def test_gcd_large_common_divisor():
    assert gcd(1000000, 500000) == 500000

def test_gcd_a_just_above_one():
    assert gcd(2, 1) == 1

def test_gcd_b_just_above_one():
    assert gcd(1, 2) == 1

def test_gcd_a_equals_two():
    assert gcd(2, 4) == 2

def test_gcd_consecutive_integers():
    assert gcd(99, 100) == 1

def test_gcd_large_equal_values():
    assert gcd(1000000, 1000000) == 1000000

def test_gcd_prime_numbers():
    assert gcd(13, 17) == 1

def test_gcd_a_large_b_small():
    assert gcd(1000000, 1) == 1

def test_gcd_a_small_b_large():
    assert gcd(1, 1000000) == 1