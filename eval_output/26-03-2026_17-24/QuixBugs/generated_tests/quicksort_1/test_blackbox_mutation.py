from python_programs.quicksort import quicksort

# catches: "not arr" mutated to "arr" (negation error) - base case inverted
def test_empty_list_returns_empty():
    assert quicksort([]) == []

# catches: "arr[0]" mutated to "arr[1]" (wrong index for pivot)
def test_single_element():
    assert quicksort([42]) == [42]

# catches: "x < pivot" mutated to "x <= pivot" (boundary mutation in lesser)
def test_duplicate_elements_not_duplicated():
    assert quicksort([3, 3, 3]) == [3, 3, 3]

# catches: "x < pivot" mutated to "x > pivot" (wrong operator in lesser filter)
def test_lesser_partition_correct():
    assert quicksort([3, 1, 2]) == [1, 2, 3]

# catches: "x > pivot" mutated to "x < pivot" (wrong operator in greater filter)
def test_greater_partition_correct():
    assert quicksort([1, 3, 2]) == [1, 2, 3]

# catches: "lesser + [pivot] + greater" mutated to "greater + [pivot] + lesser" (wrong order)
def test_order_is_ascending():
    assert quicksort([5, 3, 8, 1, 9, 2]) == [1, 2, 3, 5, 8, 9]

# catches: "[pivot]" omitted or mutated to "[]" (missing pivot in result)
def test_pivot_included_in_result():
    result = quicksort([2, 1, 3])
    assert result == [1, 2, 3]
    assert len(result) == 3

# catches: "arr[1:]" mutated to "arr[0:]" or "arr[:]" (including pivot in recursive calls)
def test_no_infinite_recursion_single_pivot():
    assert quicksort([5]) == [5]

# catches: "x < pivot" mutated to "x <= pivot" causing duplicates to be lost
def test_duplicates_preserved_correctly():
    assert quicksort([4, 2, 4, 1, 4]) == [1, 2, 4, 4, 4]

# catches: "x > pivot" mutated to "x >= pivot" causing duplicates to appear in greater
def test_duplicates_not_added_to_greater():
    result = quicksort([3, 3, 3, 3])
    assert result == [3, 3, 3, 3]
    assert len(result) == 4

# catches: lesser and greater swapped — full reverse order
def test_reverse_sorted_input():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# catches: "arr[1:]" mutated to "arr[2:]" (skipping an element)
def test_all_elements_present_after_sort():
    input_list = [7, 3, 5, 1, 9, 2, 8, 4, 6]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# catches: wrong base case condition allowing single element to recurse
def test_two_element_sorted():
    assert quicksort([2, 1]) == [1, 2]

# catches: "lesser + [pivot] + greater" mutated to "lesser + greater" (pivot dropped)
def test_result_length_equals_input_length():
    input_list = [10, 20, 30]
    result = quicksort(input_list)
    assert len(result) == 3
    assert result == [10, 20, 30]

# catches: negative numbers handled correctly (wrong comparison direction)
def test_negative_numbers():
    assert quicksort([-3, -1, -4, -1, -5, -9, -2]) == sorted([-3, -1, -4, -1, -5, -9, -2])

# catches: mixed positive and negative
def test_mixed_positive_negative():
    assert quicksort([-1, 3, -2, 0, 2, -3, 1]) == [-3, -2, -1, 0, 1, 2, 3]