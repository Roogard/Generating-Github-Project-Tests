import unittest
from algorithms.backtracking import check_sum

class TestCheckSum(unittest.TestCase):
    # kills: line 2, == → != (would return (False, nums) when sum matches target)
    def test_sum_equals_target_returns_true(self):
        result = check_sum([1, 2, 3], 6)
        self.assertEqual(result, (True, [1, 2, 3]))

    # kills: line 2, == → != (would return (False, nums) when sum matches target, edge case zero)
    def test_sum_zero_equals_target_zero_returns_true(self):
        result = check_sum([0, 0, 0], 0)
        self.assertEqual(result, (True, [0, 0, 0]))

    # kills: line 2, == → != (would return (False, nums) when sum matches target, single element)
    def test_sum_single_element_equals_target_returns_true(self):
        result = check_sum([5], 5)
        self.assertEqual(result, (True, [5]))

    # kills: line 4, else branch deletion (would return None when sum != target)
    def test_sum_not_equal_target_returns_false(self):
        result = check_sum([1, 2, 3], 7)
        self.assertEqual(result, (False, [1, 2, 3]))

    # kills: line 4, else branch deletion (would return None when sum != target, negative sum)
    def test_sum_negative_not_equal_target_returns_false(self):
        result = check_sum([-1, -2], -4)
        self.assertEqual(result, (False, [-1, -2]))

    # kills: line 3, return (True, nums) → return (False, nums) (mutated return value)
    def test_sum_equals_target_returns_correct_tuple_structure_true(self):
        result = check_sum([10, 20], 30)
        self.assertTrue(result[0])
        self.assertEqual(result[1], [10, 20])

    # kills: line 5, return (False, nums) → return (True, nums) (mutated return value)
    def test_sum_not_equal_target_returns_correct_tuple_structure_false(self):
        result = check_sum([10, 20], 31)
        self.assertFalse(result[0])
        self.assertEqual(result[1], [10, 20])

    # kills: line 2, sum(nums) mutation (e.g., sum → len)
    def test_sum_calculation_correct_for_positive_numbers(self):
        result = check_sum([2, 3, 4], 9)
        self.assertEqual(result, (True, [2, 3, 4]))

    # kills: line 2, sum(nums) mutation (e.g., sum → max)
    def test_sum_calculation_correct_for_mixed_numbers(self):
        result = check_sum([-5, 10, 2], 7)
        self.assertEqual(result, (True, [-5, 10, 2]))

    # kills: line 2, target constant replacement (e.g., target → target+1)
    def test_sum_equals_specific_target_boundary(self):
        result = check_sum([1, 1, 1, 1], 4)
        self.assertEqual(result, (True, [1, 1, 1, 1]))