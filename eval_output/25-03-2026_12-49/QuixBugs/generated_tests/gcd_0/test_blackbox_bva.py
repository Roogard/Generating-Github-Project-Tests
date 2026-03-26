from correct_python_programs.gcd import gcd

def test_gcd_both_zero():
    assert gcd(0, 0) == 0

def test_gcd_zero_and_nonzero():
    assert gcd(0, 5) == 5

def test_gcd_nonzero_and_zero():
    assert gcd(7, 0) == 7

def test_gcd_same_numbers():
    assert gcd(5, 5) == 5

def test_gcd_coprime_numbers():
    assert gcd(8, 15) == 1

def test_gcd_multiple_of_each_other():
    assert gcd(14, 7) == 7

def test_gcd_negative_first_argument():
    assert gcd(-3, 6) == 3

def test_gcd_negative_second_argument():
    assert gcd(3, -6) == -3