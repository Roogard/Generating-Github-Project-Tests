import unittest
from algorithms.backtracking import (
    add_operators,
    anagram,
    array_sum_combinations,
    combination_sum,
    find_words,
    generate_abbreviations,
    generate_parenthesis_v1,
    generate_parenthesis_v2,
    get_factors,
    letter_combinations,
    palindromic_substrings,
    pattern_match,
    permute,
    permute_iter,
    permute_recursive,
    permute_unique,
    recursive_get_factors,
    subsets,
    subsets_unique,
    subsets_v2,
    unique_array_sum_combinations,
)

class TestCheckSum(unittest.TestCase):
    def test_check_sum_empty_list_target_zero(self):
        result = self.check_sum([], 0)
        self.assertEqual(result, (True, []))

    def test_check_sum_empty_list_target_nonzero(self):
        result = self.check_sum([], 1)
        self.assertEqual(result, (False, []))

    def test_check_sum_single_element_equals_target(self):
        result = self.check_sum([5], 5)
        self.assertEqual(result, (True, [5]))

    def test_check_sum_single_element_not_equal_target(self):
        result = self.check_sum([5], 3)
        self.assertEqual(result, (False, [5]))

    def test_check_sum_negative_sum_equals_target(self):
        result = self.check_sum([-1, -2, -3], -6)
        self.assertEqual(result, (True, [-1, -2, -3]))

    def test_check_sum_negative_sum_not_equal_target(self):
        result = self.check_sum([-1, -2, -3], -5)
        self.assertEqual(result, (False, [-1, -2, -3]))

    def test_check_sum_mixed_sign_sum_equals_target(self):
        result = self.check_sum([10, -5, 2], 7)
        self.assertEqual(result, (True, [10, -5, 2]))

    def test_check_sum_mixed_sign_sum_not_equal_target(self):
        result = self.check_sum([10, -5, 2], 8)
        self.assertEqual(result, (False, [10, -5, 2]))

    def test_check_sum_large_numbers_equals_target(self):
        result = self.check_sum([1000000, 2000000], 3000000)
        self.assertEqual(result, (True, [1000000, 2000000]))

    def test_check_sum_large_numbers_not_equal_target(self):
        result = self.check_sum([1000000, 2000000], 3000001)
        self.assertEqual(result, (False, [1000000, 2000000]))

    def test_check_sum_zero_list_equals_target_zero(self):
        result = self.check_sum([0, 0, 0], 0)
        self.assertEqual(result, (True, [0, 0, 0]))

    def test_check_sum_zero_list_not_equal_target_nonzero(self):
        result = self.check_sum([0, 0, 0], 1)
        self.assertEqual(result, (False, [0, 0, 0]))

    def test_check_sum_single_zero_equals_target_zero(self):
        result = self.check_sum([0], 0)
        self.assertEqual(result, (True, [0]))

    def test_check_sum_single_zero_not_equal_target_nonzero(self):
        result = self.check_sum([0], 1)
        self.assertEqual(result, (False, [0]))