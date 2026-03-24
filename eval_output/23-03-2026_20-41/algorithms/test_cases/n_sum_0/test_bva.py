import pytest
from algorithms.array.n_sum import _two_sum

def test_two_sum_empty_list():
    # Boundary: empty nums list
    nums = []
    target = 5
    sum_closure = lambda x, y: x + y
    compare_closure = lambda x, y: -1 if x < y else (1 if x > y else 0)
    same_closure = lambda x, y: x == y
    result = _two_sum(nums, target, sum_closure, compare_closure, same_closure)
    assert result == []

def test_two_sum_single_element():
    # Boundary: single element list (cannot form a pair)
    nums = [3]
    target = 3
    sum_closure = lambda x, y: x + y
    compare_closure = lambda x, y: -1 if x < y else (1 if x > y else 0)
    same_closure = lambda x, y: x == y
    result = _two_sum(nums, target, sum_closure, compare_closure, same_closure)
    assert result == []

def test_two_sum_two_elements_matching():
    # Boundary: minimum list length to form a pair (success)
    nums = [1, 2]
    target = 3
    sum_closure = lambda x, y: x + y
    compare_closure = lambda x, y: -1 if x < y else (1 if x > y else 0)
    same_closure = lambda x, y: x == y
    result = _two_sum(nums, target, sum_closure, compare_closure, same_closure)
    assert result == [[1, 2]]

def test_two_sum_two_elements_not_matching():
    # Boundary: minimum list length to form a pair (failure)
    nums = [1, 2]
    target = 4
    sum_closure = lambda x, y: x + y
    compare_closure = lambda x, y: -1 if x < y else (1 if x > y else 0)
    same_closure = lambda x, y: x == y
    result = _two_sum(nums, target, sum_closure, compare_closure, same_closure)
    assert result == []

def test_two_sum_all_identical_matching():
    # Boundary: all elements identical and match target
    nums = [5, 5, 5, 5]
    target = 10
    sum_closure = lambda x, y: x + y
    compare_closure = lambda x, y: -1 if x < y else (1 if x > y else 0)
    same_closure = lambda x, y: x == y
    result = _two_sum(nums, target, sum_closure, compare_closure, same_closure)
    assert result == [[5, 5]]

def test_two_sum_all_identical_not_matching():
    # Boundary: all elements identical and do not match target
    nums = [5, 5, 5, 5]
    target = 11
    sum_closure = lambda x, y: x + y
    compare_closure = lambda x, y: -1 if x < y else (1 if x > y else 0)
    same_closure = lambda x, y: x == y
    result = _two_sum(nums, target, sum_closure, compare_closure, same_closure)
    assert result == []

def test_two_sum_negative_numbers():
    # Boundary: negative target and numbers
    nums = [-5, -3, -1, 0, 2, 4]
    target = -4
    sum_closure = lambda x, y: x + y
    compare_closure = lambda x, y: -1 if x < y else (1 if x > y else 0)
    same_closure = lambda x, y: x == y
    result = _two_sum(nums, target, sum_closure, compare_closure, same_closure)
    assert result == [[-5, 1]]

def test_two_sum_zero_target():
    # Boundary: target is zero
    nums = [-2, -1, 0, 1, 2]
    target = 0
    sum_closure = lambda x, y: x + y
    compare_closure = lambda x, y: -1 if x < y else (1 if x > y else 0)
    same_closure = lambda x, y: x == y
    result = _two_sum(nums, target, sum_closure, compare_closure, same_closure)
    assert sorted(result) == [[-2, 2], [-1, 1]]

def test_two_sum_large_numbers():
    # Boundary: large integers
    nums = [10**6, 10**6 + 1, 10**6 + 2]
    target = 2 * 10**6 + 1
    sum_closure = lambda x, y: x + y
    compare_closure = lambda x, y: -1 if x < y else (1 if x > y else 0)
    same_closure = lambda x, y: x == y
    result = _two_sum(nums, target, sum_closure, compare_closure, same_closure)
    assert result == [[10**6, 10**6 + 1]]

def test_two_sum_duplicate_pairs():
    # Boundary: duplicate pairs due to duplicate values
    nums = [1, 1, 2, 2, 3, 3]
    target = 4
    sum_closure = lambda x, y: x + y
    compare_closure = lambda x, y: -1 if x < y else (1 if x > y else 0)
    same_closure = lambda x, y: x == y
    result = _two_sum(nums, target, sum_closure, compare_closure, same_closure)
    assert result == [[1, 3], [2, 2]]

def test_two_sum_custom_closure_operations():
    # Boundary: custom closures (non-numeric operations)
    nums = ['a', 'b', 'c', 'd']
    target = 'ab'
    sum_closure = lambda x, y: x + y
    compare_closure = lambda x, y: -1 if x < y else (1 if x > y else 0)
    same_closure = lambda x, y: x == y
    result = _two_sum(nums, target, sum_closure, compare_closure, same_closure)
    assert result == [['a', 'b']]