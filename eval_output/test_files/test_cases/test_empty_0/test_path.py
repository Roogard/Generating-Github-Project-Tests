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

# Note: The function `check_sum` is a method of a test class. We'll create a test class to instantiate.
# Path coverage analysis:
# Branch points: 1 (if sum(nums) == target)
# Paths:
# 1. sum(nums) == target → True → return (True, nums)
# 2. sum(nums) != target → False → return (False, nums)

class TestCheckSum(unittest.TestCase):
    # path: sum(nums) == target → True → return (True, nums)
    def test_check_sum_true(self):
        obj = self.__class__('dummy')  # Create instance of test class
        result = obj.check_sum([1, 2, 3], 6)
        self.assertEqual(result, (True, [1, 2, 3]))

    # path: sum(nums) != target → False → return (False, nums)
    def test_check_sum_false(self):
        obj = self.__class__('dummy')
        result = obj.check_sum([1, 2, 3], 5)
        self.assertEqual(result, (False, [1, 2, 3]))