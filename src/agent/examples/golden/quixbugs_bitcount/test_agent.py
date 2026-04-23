import pytest

from bitcount import bitcount


def test_zero_has_zero_bits():
    # Tier 1: defined by semantics ("count of set bits")
    assert bitcount(0) == 0


def test_powers_of_two_have_one_bit():
    # Tier 2 metamorphic: every power of two has exactly one set bit
    for shift in range(10):
        assert bitcount(1 << shift) == 1


def test_all_ones_match_bit_length():
    # Tier 2 metamorphic: 2**k - 1 has exactly k set bits
    for k in range(1, 12):
        assert bitcount((1 << k) - 1) == k


def test_matches_bin_count_across_range():
    # Tier 2 metamorphic: oracle derived from the stdlib
    for n in range(0, 256):
        assert bitcount(n) == bin(n).count("1")


def test_non_negative_result():
    # Tier 3 property: bit count is non-negative for any non-negative input
    for n in [1, 2, 5, 17, 255, 1024, 99999]:
        assert bitcount(n) >= 0
