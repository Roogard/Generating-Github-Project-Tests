from correct_python_programs.quicksort import quicksort

# condition: not arr: True → empty list
def test_empty_list():
    assert quicksort([]) == []

# condition: not arr: False → non-empty list
# sub-conditions in list comprehensions:
#   x < pivot: True (for some x)
#   x >= pivot: True (for some x)
def test_single_element():
    assert quicksort([5]) == [5]

# condition: not arr: False
# sub-conditions in recursion:
#   For first call: arr = [3, 1, 4, 2]
#     x < pivot (3): True (1, 2), False (4)
#     x >= pivot (3): True (4), False (1, 2)
#   Recursive calls will exercise further conditions
def test_multiple_elements():
    assert quicksort([3, 1, 4, 2]) == [1, 2, 3, 4]

# condition: not arr: False
# sub-conditions: all x < pivot are False (since pivot is min)
#   x < pivot: False for all x in arr[1:]
#   x >= pivot: True for all x in arr[1:]
def test_pivot_is_minimum():
    assert quicksort([1, 2, 3, 4]) == [1, 2, 3, 4]

# condition: not arr: False
# sub-conditions: all x >= pivot are False (since pivot is max)
#   x < pivot: True for all x in arr[1:]
#   x >= pivot: False for all x in arr[1:]
def test_pivot_is_maximum():
    assert quicksort([4, 3, 2, 1]) == [1, 2, 3, 4]

# condition: not arr: False
# sub-conditions: duplicate values
#   x < pivot: True for some, False for others
#   x >= pivot: True for some (including equals), False for others
def test_with_duplicates():
    assert quicksort([3, 1, 3, 2, 1]) == [1, 1, 2, 3, 3]